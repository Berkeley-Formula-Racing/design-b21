import socket
import json
import threading

import serial
from serial import SerialException
from serial.tools import list_ports

PORT = 7223
READ_TIMEOUT = 1
SCAN_TIMEOUT = 3

class PortNotOpenException(Exception):
    pass

class CommsErrorException(Exception):
    pass

class SerialConnection():
    DEFAULT_WRITE_TIMEOUT = 3
    DEFAULT_READ_TIMEOUT = 1
    timeout = DEFAULT_READ_TIMEOUT
    writeTimeout = DEFAULT_WRITE_TIMEOUT

    ser = None

    def __init__(self, **kwargs):
        pass

    def get_available_devices(self):
        print("SerialConnection: getting available devices")
        devices = [x[0] for x in list_ports.comports()]
        devices.sort()
        filtered_devices = filter(lambda device: not device.startswith('/dev/ttyUSB') and not device.startswith('/dev/ttyS') and not device.startswith('/dev/cu.Bluetooth-Incoming-Port'), devices)
        return list(filtered_devices)

    def isOpen(self):
        return self.ser != None

    def open(self, device):
        self.ser = serial.Serial(device, timeout=self.timeout, write_timeout=self.writeTimeout)

    def close(self):
        if self.ser != None:
            self.ser.close()
        self.ser = None

    def read(self, count):
        ser = self.ser
        if ser == None: raise PortNotOpenException()
        try:
            return ser.read(count)
        except SerialException as e:
            if str(e).startswith('device reports readiness'):
                return ''
            else:
                raise

    def read_line(self):
        msg = ''
        while True:
            c = self.read(1)
            c = c.decode('utf8')
            if c == '':
                return None
            msg += c
            if msg[-2:] == '\r\n':
                msg = msg[:-2]
                return msg

    def write(self, data):
        try:
            return self.ser.write(data.encode('utf8'))
        except SerialException as e:
            raise CommsErrorException(cause=e)

    def flushInput(self):
        try:
            self.ser.flushInput()
        except SerialException as e:
            raise CommsErrorException(cause=e)

    def flushOutput(self):
        try:
            self.ser.flushOutput()
        except SerialException as e:
            raise CommsErrorException(cause=e)

class SocketConnection(object):

    def __init__(self):
        self.socket = None

    def get_available_devices(self):
        """
        Listens for RC WiFi's UDP beacon, if found it returns the ips that the RC wifi beacon says it's available on
        :return: List of ip addresses
        """
        # Logger.info("SocketConnection: listening for RC wifi...")
        print("SocketConnection: getting available devices")
        # Listen for UDP beacon from RC wifi
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(SCAN_TIMEOUT)

        # Bind the socket to the port
        server_address = ('0.0.0.0', PORT)
        sock.bind(server_address)

        try:
            data, address = sock.recvfrom(4096)

            if data:
                # Logger.info("SocketConnection: got UDP data {}".format(data))
                # print(f"got data: {data}")
                print(data)
                message = json.loads(data)
                if message['beacon'] and message['beacon']['ip']:
                    sock.close()
                    return message['beacon']['ip']
        except socket.timeout:
            sock.close()
            # Logger.info("SocketConnection: found no RC wifi (timeout listening for UDP beacon)")
            print("found no RC wifi")
            return []

    def isOpen(self):
        """
        Returns True or False if socket is open or not
        :return: Boolean
        """
        return self.socket is not None

    def open(self, address):
        """
        Opens a socket connection to the specified address
        :param address: IP address to connect to
        :return: None
        """
        # Connect to ip address here
        rc_address = (address, 7223)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(rc_address)
        self.socket.settimeout(READ_TIMEOUT)

    def close(self):
        """
        Closes the socket connection
        :return: None
        """
        self.socket.close()
        self.socket = None

    def read(self, keep_reading):
        """
        Reads data from the socket. Will continue to read until either "\r\n" is found in the data read from the
        socket or keep_reading.is_set() returns false
        :param keep_reading: Event object that is checked while data is read
        :type keep_reading: threading.Event
        :return: String or None
        """
        msg = ''
        # Logger.info("SocketConnection: reading...")
        print("reading...")

        while keep_reading.is_set():
            try:
                data = self.socket.recv(4096)
                data = data.decode('utf8')
                if data == '':
                    return None

                msg += data

                print(data)

                if msg[-2:] == '\r\n':
                    if msg != '':
                        # Logger.info("SocketConnection: returning data {}".format(msg))
                        # print(f"returning data: {data}")
                        return msg
                    else:
                        return None
            except socket.timeout:
                print("here")

    def write(self, data):
        """
        Writes data to the socket
        :param data: Data to write
        :type data: String
        :return: None
        """
        self.socket.send(data.encode('utf8'))

    def flushInput(self):
        pass
    
    def flushOutput(self):
        pass


def open_socket():
    should_read = threading.Event()
    should_read.set()

    sock = SocketConnection()
    devices = sock.get_available_devices()
    print(devices)
    sock.open(devices[0])

    # cmd = {'s':None}
    # cmd = {'getCapabilities': None}
    cmd = {'s':{'meta':1}}
    cmdStr = json.dumps(cmd, separators=(',', ':')) + '\r'
    sock.write(cmdStr)

    sock.read(should_read)

def open_serial():
    serial = SerialConnection()
    devices = serial.get_available_devices()
    print(devices)
    serial.open(devices[0])

    cmd = {'s':{'meta':1}}
    cmdStr = json.dumps(cmd, separators=(',', ':')) + '\r'
    serial.write(cmdStr)

    print(serial.read_line())


if __name__ == '__main__':
    # open_socket()
    open_serial()

'''
b'{"beacon":{"name":"RCP_MK3","port":7223,"serial":"3F005A000B51343034323934","ip":["192.168.4.1"]}}\r\n'
['192.168.4.1']
'''

'''
IMU on channel 1 will return:
{"imuCfg":{"1":{"nm":"AccelY","ut":"G","min":-3.0,"max":3.0,"prec":2,"sr":25,"mode":1,"chan":1,"zeroVal":-248,"alpha":0.1}}}

{"capabilities":{"flags":["activetrack","adc","bt","can","can_term","cell","gpio","gps","imu","lua","obd2","telemstream","timer","tracks","usb","wifi","sd","camctl"],"channels":{"analog":9,"imu":6,"gpio":3,"timer":4,"can":2,"obd2":20,"canChan":100},"sampleRates":{"gps":50,"sensor":1000},"db":{"script":16384,"tracks":50,"sectors":20}}}
'''

'''
Sample data: 's'

{"s":{"t":0,"d":[304359,0,302,302,0,0.0,4.26,-0.24,-0.28,0.69,12,-29,122,0.37,0,0.0,0.0,0.0,0.0,0,0,0.0,0,0.0,-1,0.0,0.0,0.0,0,0.0,5.0726,2147483647]}}
'''
