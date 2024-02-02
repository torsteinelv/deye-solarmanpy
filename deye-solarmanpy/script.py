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
    print("Configuration values 'ip_address' or 'serial_number' are missing.")
    sys.exit(1)

print(f"{token}: {ip_address}, {serial_number}")

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
            print("States have not changed, skipping iteration")
            time.sleep(60)
            continue

        # Rest of your script...

    except Exception as e:
        print(f"An error occurred: {e}")

    # Pause for 1 minute
    time.sleep(60)
