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
    try:
        config_data = load_config(config_path)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON configuration file: {config_path}")
        sys.exit(1)

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
import asyncio
from pysolarmanv5 import PySolarmanV5Async, V5FrameError, NoSocketAvailableError


async def handle_client(reader, writer):
    solarmanv5 = PySolarmanV5Async(
        ip_address, serial_number, verbose=True, auto_reconnect=True
    )
    await solarmanv5.connect()

    addr = writer.get_extra_info("peername")

    print(f"{addr}: New connection")

    while True:
        modbus_request = await reader.read(1024)
        if not modbus_request:
            break
        try:
            reply = await solarmanv5.send_raw_modbus_frame(modbus_request)
            writer.write(reply)
        except:
            pass

    await writer.drain()
    print(f"{addr}: Connection closed")
    await solarmanv5.disconnect()


async def run_server():
    server = await asyncio.start_server(handle_client, "0.0.0.0", 1502)
    async with server:
        await server.serve_forever()


asyncio.run(run_server())