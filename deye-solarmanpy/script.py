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

def load_config(config_path):
    """Load configuration from the JSON file."""
    with open(config_path, "r") as file:
        return json.load(file)

def get_environment_variable(key, default=None):
    """Get environment variable with a default value."""
    return os.environ.get(key, default)

def get_inverter_values(ip_address, serial_number):
    """Get current values from the inverter."""
    return PySolarmanV5(ip_address, serial_number, port=8899, mb_slave_id=1, verbose=False)

def update_inverter_register(modbus, register_addr, new_value):
    """Update register value in the inverter."""
    write = modbus.write_multiple_holding_registers(register_addr, values=[new_value])
    return write

def main():
    # Define the path to the JSON file
    config_path = get_environment_variable("CONFIG_PATH", "/data/options.json")

    # Load configuration
    config_data = load_config(config_path)

    # Access specific values from the configuration
    token = get_environment_variable("SUPERVISOR_TOKEN")
    ip_address = config_data.get("ip")
    serial_number = int(config_data.get("serialnumber", 0))

    # Check if required configuration values are present
    if not all((ip_address, serial_number, token)):
        logger.error("Configuration values 'ip_address', 'serial_number', or 'token' are missing.")
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

    # Main loop
    while True:
        # Send HTTP GET requests to Home Assistant API to retrieve the states
        response = requests.get(f"{url}/states/{entity_id}", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        response2 = requests.get(f"{url}/states/{hass_deye_charge_amps}", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})

        # Extract the states from the response JSON
        state = response.json().get("state")
        state2 = response2.json().get("state")

        # Log the new states
        if state != prev_state:
            logger.info(f"State changed! New state: {state}")

            try:
                state_float = float(state)
                input_val = round(state_float)
                voltage = (input_val / 100) * 1680 + 4200
                voltage = round(voltage)

                if 20 <= input_val <= 90:
                    modbus = get_inverter_values(ip_address, serial_number)
                    read = modbus.read_holding_registers(register_addr=262, quantity=1)
                    if read[0] == voltage:
                        logger.info(f"Skipping write, same value ({read[0]} voltage)")
                        prev_state = state
                    else:
                        write = update_inverter_register(modbus, register_addr=262, new_value=voltage)
                        if write == 1:
                            logger.info(f"Write to the inverter successful, new voltage: {voltage}")
                            prev_state = state
                        else:
                            logger.warning("Write to the inverter failed!")
            except Exception as e:
                logger.error(f"Error interacting with inverter: {e}")

        try:
            state2_float = float(state2)
            if state2_float != prev_state2:
                logger.info(f"State2 changed! New state: {state2_float} / {prev_state2}")
                if 0 <= state2_float <= 40:
                    modbus = get_inverter_values(ip_address, serial_number)
                    read = modbus.read_holding_registers(register_addr=210, quantity=1)
                    if read[0] == state2_float:
                        logger.info(f"Skipping write, same value ({read[0]} amps {state2_float})")
                        prev_state2 = state2_float
                    else:
                        write = update_inverter_register(modbus, register_addr=210, new_value=state2_float)
                        if write == 1:
                            logger.info(f"Write to the inverter successful, new amp now: {state2_float}")
                           
