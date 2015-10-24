import serial
import rs485



# Open non-blocking port
port = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=0, rtscts=True)

rs485 = rs485.SerialWrapper(port)

# written = port.write("Hej\n".encode())

rs485.sendMsg("Hej\n".encode())
