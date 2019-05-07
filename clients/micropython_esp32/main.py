import socket
import json 
import ubinascii
import urequests
import network
import time
import machine
import onewire, ds18x20

# Use the on board led for feedback
led = machine.Pin(5)
led.init(led.OUT)

def blink(n, t_on=200, t_off=200):
    for i in range(n):
        led.value(1)
        time.sleep_ms(t_on)
        led.value(0)
        time.sleep_ms(t_off)

def do_connect(ssid="", password=""):
    import network
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(ssid, password)
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())

# signal start
blink(2, t_on=200, t_off=200)

# Read the config file
with open('/config.json', 'r') as f:
    config = json.load(f)


#######################
# Series registration #
#######################

# Try to create a new session if it doesn't exist
if 'series_id' not in config:

    # get the board wifi mac address as ID
    mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode()

    doc_series = {
            'token' : config['token'],
            'device_id' : mac,
            'device_desc' : config['device_desc'],
            'desc' : config['desc'],
            }

    do_connect(**config['wifi'])

    # Create a new sessions
    try:
        headers = {'content-type': 'application/json'}
        data = json.dumps(doc_series)
        r = urequests.put(config['url'] + '/series/new', data=data, headers=headers)
        if r.status_code == 201:

            # get the series id and save to file
            config['series_id'] = r.json()
            with open('/config.json', 'w') as f:
                f.write(json.dumps(config))

            print('New series created with id {}'.format(config['series_id']))
        else:
            print('Registration of new series failed with code', r.status_code, r.text)
    except Exception as err:
        print('Error: {}'.format(err))
        pass

# if still not here go back to sleep
if 'series_id' not in config:
    machine.deepsleep(config['update_interval_ms'])


###############
# Measurement #
###############

# Initialize the temperature sensor
dat = machine.Pin(config['pins']['temp'])
ds = ds18x20.DS18X20(onewire.OneWire(dat))
roms = ds.scan()
if len(roms) == 0:
    print('Error: Temperature sensor not found!')
    machine.deepsleep(config['update_interval_ms'])

# Initialize the ADC for the battery voltage sensing
adc = machine.ADC(machine.Pin(config['pins']['battery']))          # create ADC object on ADC pin
adc.atten(machine.ADC.ATTN_11DB)    # set 11dB input attentuation (voltage range roughly 0.0v - 3.6v)


# prepare the data structures
doc_point = {
        'token' : config['token'],
        'series_id' : config['series_id'],
        'fields' : {
            'temp_C' : 0.,
            'batt_V' : 0.,
            }
        }

# Perform the measurement here
ds.convert_temp()
time.sleep_ms(750)
doc_point['fields']['temp_C'] = ds.read_temp(roms[0])
# conversion formula is a little bit empirical
doc_point['fields']['batt_V'] = adc.read() / 4096 * 3.3 * 2.02


#############################
# Send the point to the API #
#############################

do_connect(**config['wifi'])

# Connect to API and create new data point
request_failed = True  # assume the worst
try:
    headers = {'content-type': 'application/json'}
    data = json.dumps(doc_point)
    r = urequests.put(config['url'] + '/point/new', data=data, headers=headers)
    if r.status_code == 201:
        request_failed = False  # things turned all right
        point_id = r.json()
        print('New point created with ID={} values={}'.format(point_id, doc_point['fields']))
    else:
        print('Registration of new point failed with code', r.status_code, r.text)
except Exception as err:
    print('Error: {}'.format(err))
    pass

# signal end and go back to sleep
blink(1, t_on=200, t_off=0)
machine.deepsleep(config['update_interval_ms'])

