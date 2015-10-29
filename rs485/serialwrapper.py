import serial
import rs485
from typing import Callable

class SerialWrapper(rs485.RS485):
    '''Wrapper for using a pySerial object with RS485.'''

    def __init__(self, serial : serial.Serial):
        self.serial = serial
        super().__init__(fWrite=self._write, fAvailable=self._available, fRead=self._read)

    def _write(self, aByte : int) -> int:
        return self.serial.write(bytes([aByte]))

    def _available(self) -> int:
        return self.serial.inWaiting()

    def _read(self) -> int:
        data = self.serial.read(1)
        return data[0]
