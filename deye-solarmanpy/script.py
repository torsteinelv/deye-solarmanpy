import requests
import os
import sys
import logging
from pysolarmanv5 import PySolarmanV5
from datetime import datetime
import time

print(os.environ.get('YOUR_LONG_LIVED_ACCESS_TOKEN'))

# Home Assistant REST API URL
url = "http://supervisor/core/api"

# Entity IDs to retrieve the states for
entity_id = "input_text.emhass_deye_set_soc"
hass_deye_charge_amps = "input_text.emhass_deye_charge_amps"

# Access token for authentication
token = os.environ.get("SUPERVISOR_TOKEN")

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

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
                logger.warning("Input value is outside of valid range (0-100)")
                continue

            # Call main function to send update to inverter for state1
            modbus = PySolarmanV5("10.10.12.24", , port=8899, mb_slave_id=1, verbose=False)

            # Read current value from inverter
            read = modbus.read_holding_registers(register_addr=262, quantity=1)
            read_battery_amps = modbus.read_holding_registers(register_addr=210, quantity=1)
            logger.debug(f"Current voltage on inverter: {read[0]}")

            # If current value matches the desired value, skip write
            if read[0] == voltage:
              logger.info(f"Skipping write, same value({read[0]} voltage)")
              prev_state = state
            # Otherwise, write the new value
            else:
              write = modbus.write_multiple_holding_registers(register_addr=262, values=[voltage])
              if write == 1:
                logger.info(f"Write to inverter successful, new voltage: {voltage}")
                prev_state = state
              else:
                logger.warning("Write to inverter failed!")
        state2 = int(state2)
        if state2 != prev_state2:
            logger.info(f"State2 changed! New state: {state2} / {prev_state2}")
            state2 = int(state2)


            if state2 > 40:
                logger.warning("Input value2 is outside of valid range (0-40)")
                continue

            # Call main function to send update to inverter for state2
#            main(register_addr=210, value=state2)
            modbus = PySolarmanV5("10.10.12.24", 2338439962, port=8899, mb_slave_id=1, verbose=False)

    # Read current value from inverter
            read = modbus.read_holding_registers(register_addr=210, quantity=1)


            if read[0] == state2:
              logger.info(f"Skipping write, same value({read[0]} amps {state2})")
              prev_state2 = state2
    # Otherwise, write the new value
            else:

              write = modbus.write_multiple_holding_registers(register_addr=210, values=[state2])
              if write == 1:
                logger.info(f"Write to inverter successful, new amp now: {state2}")
                prev_state2 = state2
              else:
                logger.warning("Write to inverter failed!")


    except Exception as e:
        logger.error(f"An error occurred: {e}")

    # Pause for 1 minute
    time.sleep(60)
