Temperature Logger
==================

This is a simple temperature logger using an ESP32,
a DS18B20 probe and micropython.

Deepsleep is needed to save battery life. Since the official
micropython port did not support it at this point, I compiled
a firmware from [MrSurly
that has the deepsleep enabled](https://github.com/MrSurly/micropython-esp32/tree/dev-deepsleep). A compiled version of the firmware
is available in `firmware`.

Quickstart
----------

1. Connect a DS18B20 probe to pin 13 of the ESP32.

2. Update the firmware of the ESP32 to the one with deepsleep enabled.

        esptool.py --chip esp32 --port /dev/ttyUSB1 write_flash -z 0x1000 firmware.bin

3. Edit `config.json` and edit the `url` and `token` with the values for your
   own API configuration.

4. Edit `main.py`, set your WIFI credentials in the `WIFI_SSID` and
   `WIFI_PASSWORD` variables.

5. Upload `config.json` and `main.py` to the ESP32

        ampy put config.json
        ampy put main.py

    Then, reset it. The serial output has some debug info.
    First, the sensor will try to create a new series. If this is successful,
    it will add the new series_id in the `config.json` file and always
    add new points to that series.
