from serial import *
import serial.tools.list_ports
import paho.mqtt.client as mqtt
import time
import sys
import os
import threading

## network parameters

# remote
HOST = '169.254.1.1'

# local
#HOST = '127.1.1.1'

PORT = 1883 # default mqtt port

## serial parameters
# windows
WIN = 0
LINUX = not(WIN)
if WIN:
    SERIALPATH = 'COM15'
    SERIAL_ROOT = ''
    SERIAL_PREFIX = 'COM'
else:
    SERIALPATH = '/dev/ttyACM0'
    SERIAL_ROOT = '/dev/'
    SERIAL_PREFIX = 'ttyACM'

SLEEP_TIME = 0.2
WATCHDOG_TIMEOUT = 5

## mqtt field variables init
distance = 0
anchor_id = ''
bot_id = ''
rssi = 0

## mqtt format
NB_DATA = 9 # number of datatypes sent by the node
NB_DATA_EXTENDED = 13 # number of datatypes sent by the node in EXTENDED_MODE
ROOT = 'SecureLoc/anchors_data/'
COOPERATIVE_ROOT = 'SecureLoc/cooperative_data/'
TOPIC_SERIAL = 'Serial'
MQTT_CONFIG_FILE = 'MQTT_topics.txt'


## serial containers & flags
devices = []
connected_anchors = {}
serial_ports = {}
exit_flag = False


class ClientStub(object):
    def __getattribute__(self,attr):
        def method(*args, **kwargs):
            pass
        return method

    def __setattribute__(self,attr):
        pass




## starting mqtt client
# stubing mqtt if no broker is found
try:
    mqttc = mqtt.Client()
    mqttc.connect(HOST, PORT, 60)
    mqttc.loop_start()
except:
    mqttc = ClientStub()



def on_message(mqttc,obj,msg):
    """handles data resfreshing when a mqtt message is received"""
    labels = msg.topic.split("/")
    serial_message = msg.payload
    anchorID = labels[-2]
    print("Sending serial command to anchor " + anchorID + " :" + serial_message.encode())
    for port_name, ID in connected_anchors.items():
        if ID == anchorID:
            serial_ports[port_name].write(serial_message)


mqttc.on_message = on_message

def getSerialPorts():
    """returns all the serial devices connect as a list"""
    ports = []
    if SERIAL_PREFIX == 'COM':
        # windows system
        files = [port.device for port in list(serial.tools.list_ports.comports())]
    else:
        # linux
        files= os.listdir(SERIAL_ROOT)
    for entry in files:
        if entry.startswith(SERIAL_PREFIX):
            ports.append(entry)

    print('found serial devices: ' + str(ports) )
    return(ports)


def openPort(path = SERIALPATH):
    """open the serial port for the given path"""
    try:
        port = Serial(path, timeout=1, writeTimeout=1)
        print("bytes in the input buffer after opening:")
        print(port.in_waiting)


    except :
        print("No serial device on the given path :" + path)
        sys.exit()

    return(port)


def processLine(line, port):
    """parses the serial line received. If it is a DATA frame, publishes the data on MQTT.
    DEBUG frames will be ignored"""

    if len(line) > 0 and line[0] == '*' and line[-1] == '#':
        data = line.split("|")
        if len(data) < NB_DATA:
            print('received frame is not compliant with the expected data format')
        if len(data) >= NB_DATA:
            anchor_id = data[0][15:17]
            bot_id = data[1][14:17]
            port_name = port.name.split("/")[-1]
            if (port_name in connected_anchors) and not(connected_anchors[port_name]):
                connected_anchors[port_name] = anchor_id
                print("subscribing to " + ROOT + anchor_id + "/" + TOPIC_SERIAL )
                mqttc.subscribe(ROOT + anchor_id + "/" + TOPIC_SERIAL)
            distance = data[2]
            # timestamps
            [ts1,ts2,ts3,ts4] = [data[3], data[4], data[5], data[6] ]
            skew = data[7]
            rssi = data[8]

            if rssi[-1] == '#':
            # rssi was the last element sent
                rssi = rssi[:-1]


            # publishing to MQTT
            mqttc.publish(ROOT + str(anchor_id) + "/" + str(bot_id) + "/distance", distance )
            mqttc.publish(ROOT + str(anchor_id) + "/" + str(bot_id) + "/rssi", rssi )
            mqttc.publish(ROOT + str(anchor_id) + "/" + str(bot_id) + "/skew", skew )
            for i,ts in enumerate([ts1,ts2,ts3,ts4]):
                 mqttc.publish(ROOT + str(anchor_id) + "/" + str(bot_id) + "/ts" + str(i+1), ts )

        if len(data)== NB_DATA_EXTENDED:
            # EXTENDED MODE has to be enabled on DecaWino
            # EXTENDED MODE provides additional physical data, e.g, temperature
            fp_power = data[9]
            fp_ampl2 = data[10]
            std_noise = data[11]
            temperature = data[12][:-1] # removing '#' at the end

            # publishing to MQTT
            mqttc.publish(ROOT + str(anchor_id) + "/" + str(bot_id) + "/fp_power",fp_power)
            mqttc.publish(ROOT + str(anchor_id) + "/" + str(bot_id) + "/fp_ampl2",fp_ampl2)
            mqttc.publish(ROOT + str(anchor_id) + "/" + str(bot_id) + "/std_noise",std_noise)
            mqttc.publish(ROOT + str(anchor_id) + "/" + str(bot_id) + "/temperature",temperature)
    elif len(line) > 0 and line[0] == '^' and line[-1] == '#':
        # received the results of a differential TWR
        data = line.split("|")
        if len(data) < NB_DATA:
            print('received frame is not compliant with the expected data format')
        if len(data) >= NB_DATA:
            anchor_id = data[0][15:17]
            bot_id = data[1][14:17]
            differential_distance = data[2]
            differential_skew = data[7]
            differential_rssi = data[8]

            # publishing to MQTT
            mqttc.publish(ROOT + str(anchor_id) + "/" + str(bot_id) + "/differential_distance", differential_distance)
            mqttc.publish(ROOT + str(anchor_id) + "/" + str(bot_id) + "/differential_rssi", differential_rssi )
            mqttc.publish(ROOT + str(anchor_id) + "/" + str(bot_id) + "/differential_skew", differential_skew )

    elif len(line) > 0 and line[0] == '°' and line[-1] == '#':
        # received the results of a cooperative TWR -> a tag has been verifying another one
        print("Cooperative results received")
        data = line.split("|")
        if len(data) < NB_DATA:
            print('received frame is not compliant with the expected data format')
        if len(data) >= NB_DATA:
            verifier_id = data[0][15:17]
            bot_id = data[1][14:17]
            cooperative_distance = data[2]
            cooperative_skew = data[7]
            cooperative_rssi = data[8]

            # publishing to MQTT
            mqttc.publish(COOPERATIVE_ROOT + str(verifier_id) + "/" + str(bot_id) + "/distance", cooperative_distance)
            mqttc.publish(COOPERATIVE_ROOT + str(verifier_id) + "/" + str(bot_id) + "/rssi", cooperative_rssi )
            mqttc.publish(COOPERATIVE_ROOT + str(verifier_id) + "/" + str(bot_id) + "/skew", cooperative_skew )
            







def rebootTeensy():
    """reboot the TeensyDuino.
    Reflashing Teensyduino is required given that no remote soft reset is provided besides the bootloader"""

    print("Resetting Teensy...")
    os.system('/home/pi/Desktop/teensy_loader_cli -mmcu=mk20dx256 -s -v ' + '/home/pi/Desktop/node*.hex')





def waitSerialDevice(path):
    """waits until the given serial device is connected"""
    print("Waiting for serial device...")
    while ( not(os.path.exists(path)) ):
        time.sleep(1)

    print("Serial device found")


def readSerial(port):
    """reads the given serial port line by line"""
    global exit_flag
    rebooted_once = False
    print('Reading serial port ' + port.name)
    exit_flag = False
    timer = 0
    while not(exit_flag):
        try:
            if (port.in_waiting > 0 ):
                # resetting the timer
                timer = 0
                line = port.readline().decode('utf-8').strip()
                print(line)
                try:
                    processLine(line, port)
                except:
                    print("process line failed")
            else:
                time.sleep(SLEEP_TIME)
                timer += SLEEP_TIME

        except KeyboardInterrupt:
            print("Ctrl + C received, quitting")
            exit_flag = True
        except:
            print('An error occured, did you unplug the device ?')
            break;


        # watchdog for serial disruption
        # reset teensy if nothing is received on serial port after WATCHDOG_TIMEOUT
        # Due to some RaspPi 1 & 3 bugs on serial-over-usb, opening the serial port more than 1s after TeensyDuino boots
        # generates a bug in the serial buffer.
        # In case where this program is launched after that 1s delay resetting the Teensy will be required
        #
        if not(rebooted_once) and (timer > WATCHDOG_TIMEOUT):
            path = port.name
            port.close()
            rebootTeensy()
            rebooted_once = True

            waitSerialDevice(path)
            port = openPort(path)
            serial_ports[port.name.split("/")[-1]] = port
            print(path)


    print('Stopped reading ' + port.name)
    port.close()

def handleSerialDevice(path):
    """opens the serial port and starts reading it"""
    port = openPort(path)
    serial_ports[port.name.split("/")[-1]] = port
    readSerial(port)


# Program

ports = getSerialPorts()
path = SERIALPATH

def serialPool():
    """checks for new serial devices connecting, opens and read device when detected"""
    global exit_flag
    devices = getSerialPorts()
    threads_pool = []
    # checking if any serial device is connected
    if len(devices) > 0:
        for device in devices:
            # creating a thread reading serial port
            threads_pool.append(threading.Thread(target = handleSerialDevice, args = (SERIAL_ROOT + device,) ))
            connected_anchors[device] = None
    else:
        # waiting for any device to connect;
        waitSerialDevice(SERIALPATH)

    # starting threads
    for thread in threads_pool:
        thread.start()

    while not(exit_flag):
        try:
            time.sleep(0.5)
        except KeyboardInterrupt:
            print(" received, quitting program...")
            exit_flag = True
            for thread in threads_pool:
                thread.join()
            sys.exit()





serialPool()
