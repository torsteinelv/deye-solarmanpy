import requests
import os
import sys
import logging
from pysolarmanv5 import PySolarmanV5
import time
import json

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Define the path to the JSON file
config_path = "/data/options.json"

# Read the JSON file
with open(config_path, "r") as file:
    config_data = json.load(file)

# Access and print specific values
token = os.environ.get("SUPERVISOR_TOKEN")
ip_address = config_data.get("ip")
serial_number = config_data.get("serialnumber")

# Check if ip_address and serial_number are not None
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

while True:
    try:
        # Send a GET request to the Home Assistant API to retrieve the states
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

            # Convert state to a float
            state_float = float(state)

            # Calculate voltage from state
            def input_to_voltage(input_val):
                voltage = (input_val / 100) * 1680 + 4200
                voltage = round(voltage)
                return voltage

            input_val = round(state_float)
            voltage = input_to_voltage(input_val)

            if input_val < 20 or input_val > 90:
                logger.warning("Input value is outside of the valid range (0-100)")
                continue

            # Call the main function to send an update to the inverter for state1
            modbus = PySolarmanV5(ip_address, serial_number, port=8899, mb_slave_id=1, verbose=False)

            # Read the current value from the inverter
            read = modbus.read_holding_registers(register_addr=262, quantity=1)
            read_battery_amps = modbus.read_holding_registers(register_addr=210, quantity=1)
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

        state2 = int(state2)
        if state2 != prev_state2:
            logger.info(f"State2 changed! New state: {state2} / {prev_state2}")
            state2 = int(state2)

            if state2 > 40:
                logger.warning("Input value2 is outside of the valid range (0-40)")
                continue

            # Call the main function to send an update to the inverter for state2
            modbus = PySolarmanV5(ip_address, serial_number, port=8899, mb_slave_id=1, verbose=False)

            # Read the current value from the inverter
            read = modbus.read_holding_registers(register_addr=210, quantity=1)

            if read[0] == state2:
                logger.info(f"Skipping write, same value ({read[0]} amps {state2})")
                prev_state2 = state2
            # Otherwise, write the new value
            else:
                write = modbus.write_multiple_holding_registers(register_addr=210, values=[state2])
                if write == 1:
                    logger.info(f"Write to the inverter successful, new amp now: {state2}")
                    prev_state2 = state2
                else:
                    logger.warning("Write to the inverter failed!")

    except Exception as e:
        logger.error(f"An error occurred: {e}")

    # Pause for 1 minute
    time.sleep(60)
