#!/usr/bin/with-contenv bashio

exec python3  /script.py "${SUPERVISOR_TOKEN}  ${MY_ADDON_IP_ADDRESS} ${MY_ADDON_SERIAL_NUMBER}"
