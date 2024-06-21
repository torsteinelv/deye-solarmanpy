# Home Assistant Modbus Integration for Deye Inverters

This repository contains the configuration and script setup for integrating Deye inverters with Home Assistant using the Modbus protocol over TCP.

## Prerequisites

- Home Assistant
- Uses pysolarmanv5
- Solarman data logger

## Installation



1. **Update the configuration:**

    Ensure your `configuration.yaml` includes the Modbus setup:

    ```yaml
    modbus:
      name: solarman-modbus-proxy
      type: rtuovertcp
      host: 10.10.10.101
      port: 1502
      delay: 3
      sensors:
        - name: tte_test_01
          unit_of_measurement: "%"
          address: 262
          input_type: holding
          slave: 1
          scan_interval: 60
    ```

2. **Add the automation script:**

    In your `scripts.yaml` file, add the following script to write to the Modbus register:

    ```yaml
    write_modbus_262:
      alias: write_modbus_262
      sequence:
        - service: modbus.write_register
          data:
            hub: solarman-modbus-proxy
            unit: 1  # Ensure this is the correct unit/slave ID
            address: 262
            value: [4705]
    ```

## Usage

1. **Configure Modbus:**

    In your Home Assistant configuration, ensure you have the Modbus integration set up as described above.

2. **Write to the Modbus register:**

    Trigger the `write_modbus_262` script from Home Assistant UI or through an automation to send the specified value to the inverter's register.

## Example

Here is an example configuration for the Deye inverter:

### Modbus Configuration

```yaml
modbus:
  name: solarman-modbus-proxy
  type: rtuovertcp
  host: 10.10.10.101
  port: 1502
  delay: 3
  sensors:
    - name: tte_test_01
      unit_of_measurement: "%"
      address: 262
      input_type: holding
      slave: 1
      scan_interval: 60
