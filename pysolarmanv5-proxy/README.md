example for deye:

modbus:
  - name: solarman-modbus-proxy
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
        
script:
  write_modbus_262:
    alias: write_modbus_262
    sequence:
      - service: modbus.write_register
        data:
          hub: solarman-modbus-proxy
          unit: 1  # Ensure this is the correct unit/slave ID
          address: 262
          value: [4705]
