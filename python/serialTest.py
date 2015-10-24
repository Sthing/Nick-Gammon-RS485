import RPi.GPIO as GPIO
import serial


"""
On the GPIO Header we use the following pins for serial:
        Pin   Signal
         6    GND
         8    GPIO14 Tx
        10    GPIO15 Rx
        12    GPIO18 - used for the nRE/DE direction pins on the MAX3483.
"""
# Use Broadcom numbering - ie not pin numbers but GPIO numbers.
GPIO.setmode(GPIO.BCM)
# Set Pin 12 as output, low means do NOT drive RS845 output.
GPIO.setup(18, GPIO.OUT, initial=GPIO.LOW)

# Open non-blocking port
port = serial.Serial("/dev/ttyAMA0", baudrate=9600, timeout=0)

got_data = 0
while True:
    cnt = port.inWaiting()
    if cnt:
        # print("Der er ", cnt, "bytes til os")
        rcv = port.read(cnt)
        print(rcv)
        got_data = 1
    elif got_data:
        if rcv == 'STOP'.encode():
            break
        port.write("Tak for kaffe\n".encode());
        got_data = 0

    #port.write("\r\nYou sent:" + repr(rcv))

# Cleanup - revert all pins to inputs, no pull up/down.
GPIO.cleanup()
