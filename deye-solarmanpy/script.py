import requests
import os
import sys
import logging
from pysolarmanv5 import PySolarmanV5
from datetime import datetime
import time

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Access token for authentication
token = os.environ.get("SUPERVISOR_TOKEN")
ip_address = os.environ.get("MY_ADDON_IP_ADDRESS")
serial_number = os.environ.get("MY_ADDON_SERIAL_NUMBER")

# Check if ip_address and serial_number are not None
if ip_address is None or serial_number is None:
    logger.error("Configuration values 'ip_address' or 'serial_number' are missing.")
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
            logger.debug("States have not changed, skipping iteration")
            time.sleep(60)
            continue

        # Rest of your script...

    except Exception as e:
        logger.error(f"An error occurred: {e}")

    # Pause for 1 minute
    time.sleep(60)
