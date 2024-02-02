import requests
import os
import sys
import logging
from pysolarmanv5 import PySolarmanV5
from datetime import datetime
import time
import json

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Log to stdout with a simple format
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Define the path to the JSON file
config_path = "/data/options.json"

# Load configuration from the JSON file
with open(config_path, "r") as file:
    config_data = json.load(file)

# Access specific values from the configuration
token = os.environ.get("SUPERVISOR_TOKEN")
ip_address = config_data.get("ip")
serial_number = int(config_data.get("serialnumber", 0))

# Check if required configuration values are present
if ip_address is None or serial_number is None:
    logger.error("Configuration values 'ip_address' or 'serial_number' are missing.")
    sys.exit(1)

logger.info(f"Configuration values: Token={token}, IP={ip_address}, Serial Number={serial_number}")

# Home Assistant REST API URL
url = "http://supervisor/core/api"

# Entity IDs to retrieve the states for
entity_id = "input_text.emhass_deye_set_soc"
hass_deye_charge_amps = "input_text.emhass_deye_charge_amps"

# Initialize previous states
prev_state = None
prev_state2 = None

# Define the headers for the HTTP request
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}

# Main loop
while True:
    try:
        # Send HTTP GET requests to Home Assistant API to retrieve the states
        response = requests.get(f"{url}/states/{entity_id}", headers=headers)
        response2 = requests.get(f"{url}/states/{hass_deye_charge_amps}", headers=headers)

        # Extract the states from the response JSON
        state = response.json()["state"]
        state2 = response2.json()["state"]

        # If the states have not changed, skip this iteration
        if state == prev_state and state2 == prev_state2:
            logger.debug("States have not changed, skipping iteration")
            time.sleep(60)
            continue

        # Log the new states
        if state != prev_state:
            logger.info(f"State changed! New state: {state}")

            try:
                state_float = float(state)
            except ValueError:
                logger.warning("Failed to convert state to float. Skipping iteration.")
                time.sleep(60)
                continue

            # Calculate voltage from state
            input_val = round(state_float)
            voltage = (input_val / 100) * 1680 + 4200
            voltage = round(voltage)

            if 20 <= input_val <= 90:
                # Call the main function to send an update to the inverter for state1
                modbus = PySolarmanV5(ip_address, serial_number, port=8899, mb_slave_id=1, verbose=False)

                # Read the current value from the inverter
                read = modbus.read_holding_registers(register_addr=262, quantity=1)
                logger.debug(f"Current voltage on the inverter: {read[0]}")

                # If the current value matches the desired value, skip the write
                if read[0] == voltage:
                    logger.info(f"Skipping write, same value ({read[0]} voltage)")
                    prev_state = state
                # Otherwise, write the new value
                else:
                    write = modbus.write_multiple_holding_registers(register_addr=262, values=[voltage])
                    if write == 1:
                        logger.info(f"Write to the inverter successful, new voltage: {voltage}")
                        prev_state = state
                    else:
                        logger.warning("Write to the inverter failed!")

        try:
            state2_float = float(state2)
        except ValueError:
            logger.warning("Failed to convert state2 to float. Skipping iteration.")
            time.sleep(60)
            continue

        if state2_float != prev_state2:
            logger.info(f"State2 changed! New state: {state2_float} / {prev_state2}")

            if 0 <= state2_float <= 40:
                # Call the main function to send an update to the inverter for state2
                modbus = PySolarmanV5(ip_address, serial_number, port=8899, mb_slave_id=1, verbose=False)

                # Read the current value from the inverter
                read = modbus.read_holding_registers(register_addr=210, quantity=1)

                # If the current value matches the desired value, skip the write
                if read[0] == state2_float:
                    logger.info(f"Skipping write, same value ({read[0]} amps {state2_float})")
                    prev_state2 = state2_float
                # Otherwise, write the new value
                else:
                    write = modbus.write_multiple_holding_registers(register_addr=210, values=[state2_float])
                    if write == 1:
                        logger.info(f"Write to the inverter successful, new amp now: {state2_float}")
                        prev_state2 = state2_float
                    else:
                        logger.warning("Write to the inverter failed!")

    except Exception as e:
        logger.error(f"An error occurred: {e}")

    # Pause for 1 minute
    time.sleep(60)
