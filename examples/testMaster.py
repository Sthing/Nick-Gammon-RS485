# Add parent directory to path so the example can run without the library being installed
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import serial
import rs485

# Open non-blocking port
port = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=0, rtscts=True)

rs485 = rs485.SerialWrapper(port)

packet = "Hello World!\n".encode()

rs485.sendMsg(packet)
