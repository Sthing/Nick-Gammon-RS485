import datetime
from enum import Enum
from typing import Callable

class RS485:
    '''
    RS485 protocol library - non-blocking.

    Originally devised and written by Nick Gammon.
    Date: 4 December 2012
    Version: 1.0
    Adapted for Python by Søren Thing (http://access.thing.dk)
    Date: October 2015

    Licence: Released for public use.


    Can send from 1 to 255 bytes from one node to another with:
    * Packet start indicator (STX)
    * Each data byte is doubled and inverted to check validity
    * Packet end indicator (ETX)
    * Packet CRC (checksum)

    To allow flexibility you must provide three "callback" functions
    which send or receive data.
    * fWrite is requried to transmit data.
    * fAvailable and fRead are required to received data.

    See SerialWrapper for an example.
    '''

    _STX = 2    # Start of text
    _ETX = 3    # End of text

    _MAX_LENGTH = 255

    def __init__(self,
                fWrite : Callable[[int], int] = None,       # Must send a byte
                fAvailable : Callable[[], int] = None,      # Must return number of bytes available for reading
                fRead : Callable[[], int] = None):          # Must return next available byte
        '''Initializes all datastructures.'''
        self._callbackWrite = fWrite
        self._callbackAvailable = fAvailable
        self._callbackRead = fRead
        self._packets = [] # List of completely received packets
        self.errorCount = 0
        self._startTime = None
        self.reset()

    def reset(self):
        '''Discards partially received packet and returns to State.waiting.

        Called from __init__ and after errors.
        '''
        self._data = bytearray()        # Bytes received for the current packet
        self.state = State.waiting      # Waiting for STX
        self._firstNibble = None        # Set to int when first nibble is received


    def sendMsg(self, data : bytes):
        '''Send data as a packet.

        Put STX at start, ETX at end, and add CRC.
        All bytes from data are sent.
        '''
        # We cannot send unless a write callback was supplied.
        if self._callbackWrite is None:
            raise RuntimeError('No fWrite supplied.');

        self._callbackWrite(self._STX)
        for byte in data:
            self._sendComplemented(byte)
        self._callbackWrite(self._ETX)
        self._sendComplemented(self._crc8(data))


    def update(self):
        '''Assembles incoming data, returns true if a complete packet is ready.

        Called periodically from main loop to process data.
        Strips STX and ETX, verifies CRC.
        Finished packets are added to self._packets.
        '''
        # We cannot receive unless the two callbacks were supplied.
        if self._callbackAvailable is None:
            raise RuntimeError('No fAvailable supplied.');
        if self._callbackRead is None:
            raise RuntimeError('No fRead supplied.');

        while self._callbackAvailable() > 0:
            byte = self._callbackRead();

            if byte == self._STX:
                self._startTime = datetime.datetime.now()
                if self.state != State.waiting:
                    self.errorCount += 1
                self.reset()
                self.state = State.receiveData
                continue;

            if byte == self._ETX:
                if self._firstNibble is None:
                    self.state = State.receiveCrc
                else:
                    # ETX should not arrive between two nibbles
                    self.errorCount += 1
                    self.reset()
                continue

            # Wait until packet officially starts
            if self.state == State.waiting:
                continue

            # Check byte is in valid form (4 bits followed by 4 bits complemented)
            if (byte >> 4) != ((byte & 0x0F) ^ 0x0F):
                self.errorCount += 1
                self.reset()
                continue

            # Drop extra complemented bits
            byte >>= 4;

            # First or second nibble?
            if self._firstNibble is None:
                # Remember the MSB nibble until we receive the second nibble
                self._firstNibble = byte
                continue
            # This must be the second (LSB) nibble
            # Assemble the two nibbles into a byte
            byte |= (self._firstNibble << 4)
            self._firstNibble = None

            if self.state == State.receiveData:
                # Add to receive buffer
                if len(self._data) < self._MAX_LENGTH:
                    self._data.append(byte)
                else: # Overflow
                    self.errorCount += 1
                    self.reset()
                continue

            # This must be the CRC
            if self._crc8(self._data) != byte:
                # Bad CRC
                self.errorCount += 1
                self.reset()
                continue

            # Complete packet received - add to list
            self._packets.append(bytes(self._data))
            self.state = State.waiting

        # End of while self._callbackAvailable() > 0

        # Return true if at least one complete packet is ready.
        return self.available()
    # End of def update()


    def available(self):
        '''Returns true if at least one complete packet is ready.
        '''
        return len(self._packets) > 0


    def getPacket(self):
        '''Returns a complete packet
        '''
        return self._packets.pop(0)

    def getErrorCount(self):
        '''Returns the number of errors encountered.
        '''
        return self.errorCount

    def getPacketStartTime(self):
        '''Returns the time when last packet started. Format: datetime.datetime.
        '''
        return self._startTime

    def isPacketStarted(self):
        '''Returns true if a packet has started to be received and no errors have occured yet.
        '''
        return self.state != State.waiting

    def _sendComplemented(self, byte : int):
        '''Sends the byte as complemented nibbles.

        Only values sent would be (in hex):
        0F, 1E, 2D, 3C, 4B, 5A, 69, 78, 87, 96, A5, B4, C3, D2, E1, F0
        '''
        # First nibble (MSB)
        nibble = byte >> 4
        self._callbackWrite((nibble << 4) | (nibble ^ 0x0F))

        # Second nibble (LSB)
        nibble = byte & 0x0F
        self._callbackWrite((nibble << 4) | (nibble ^ 0x0F))


    def _crc8(self, data : bytes):
        '''Returns an 8-bit CRC.
        '''
        crc = 0
        for byte in data:
            for i in range(8):
                mix = (crc ^ byte) & 0x01
                crc >>= 1
                if mix:
                    crc ^= 0x8C
                byte >>= 1
        return crc

class State(Enum):
    waiting     = 1 # Waiting for STX
    receiveData = 2 # ETX not received, receiving data
    receiveCrc  = 3 # ETX received, receiving CRC
