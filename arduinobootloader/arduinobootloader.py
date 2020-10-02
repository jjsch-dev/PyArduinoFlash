'''
It is Python Class for updating the firmware of Arduino boards that use
the ATmegaBOOT_168.c bootloader.
For example Arduino Nano.

The project implements the essential parts that Avrdude uses for the
STK500 protocol for Arduino.
'''

import serial
import serial.tools.list_ports
import time

RESP_STK_OK = 0x10
RESP_STK_IN_SYNC = 0x14

""" The manufacturer byte is always the same (Atmel).
"""
SIG1_ATMEL = 0x1E

""" The dictionary key is made up of SIG2 and SIG3
    The value is a list with the name of the CPU the page size in byte 
    and the flash pages.
"""
AVR_ATMEL_CPUS = {(0x97, 0x03): ["ATmega1280", (128*2), 512],
                  (0x97, 0x04): ["ATmega1281", (128*2), 512],
                  (0x97, 0x03): ["ATmega128", (128*2), 512],
                  (0x97, 0x02): ["ATmega64", (128*2), 256],
                  (0x95, 0x02): ["ATmega32", (64*2), 256],
                  (0x94, 0x03): ["ATmega16", (64*2), 128],
                  (0x93, 0x07): ["ATmega8", (32*2), 128],
                  (0x93, 0x0A): ["ATmega88", (32*2), 128],
                  (0x94, 0x06): ["ATmega168", (64*2), 256],
                  (0x95, 0x0F): ["ATmega328P", (64*2), 256],
                  (0x95, 0x14): ["ATmega328", (64*2), 256],
                  (0x94, 0x04): ["ATmega162", (64*2), 128],
                  (0x94, 0x02): ["ATmega163", (64*2), 128],
                  (0x94, 0x05): ["ATmega169", (64*2), 128],
                  (0x93, 0x06): ["ATmega8515", (32*2), 128],
                  (0x93, 0x08): ["ATmega8535", (32*2), 128]}

"""STK message constants for Stk500v2"""
MESSAGE_START = 0x1B        # = ESC = 27 decimal
TOKEN = 0x0E
CMD_SIGN_ON = 0x01
CMD_GET_PARAMETER = 0x03

"""Options for get parameter"""
OPT_HW_VERSION = b'\x90'
OPT_SW_MAJOR = b'\x91'
OPT_SW_MINOR = b'\x92'

class ArduinoBootloader(object):
    def __init__(self, *args, **kwargs):
        self.device = None
        self.port = None
        self._hw_version = 0
        self._sw_major = 0
        self._sw_minor = 0
        self._cpu_name = ""
        self._cpu_page_size = 0
        self._cpu_pages = 0
        self._programmer_name = ""
        self._programmer = None

    @property
    def hw_version(self):
        return str(self._hw_version)

    @property
    def sw_version(self):
        return "{}.{}".format(self._sw_major, self._sw_minor)

    @property
    def cpu_name(self):
        return self._cpu_name

    @property
    def cpu_page_size(self):
        return self._cpu_page_size

    @property
    def cpu_pages(self):
        return self._cpu_pages

    def sel_programmer(self, type):
        if type == "Stk500v1":
            self._programmer = self.Stk500v1(self)
        elif type == "Stk500v2":
            self._programmer = self.Stk500v2(self)
        else:
            self._programmer = None

        return self._programmer

    def _find_device_port(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if ("VID:PID=1A86:7523" in port.hwid) or ("VID:PID=2341:0043" in port.hwid):
                return port.device
        return ""

    def open(self, port=None, speed=57600):
        """ Find and open the communication port where the Arduino is connected.
        Generate the reset sequence with the DTR / RTS pins.
        Send the sync command to verify that there is a valid bootloader.
        """
        if not port:
            port = self._find_device_port()

        if not port:
            return False
        else:
            self.device = serial.Serial(port, speed, 8, 'N', 1, timeout=1)

        self.port = port

        ''' Clear DTR and RTS to unload the RESET capacitor
            (for example in Arduino) '''
        self.device.dtr = True
        self.device.rts = True
        time.sleep(1 / 20)

        ''' Set DTR and RTS back to high '''
        self.device.dtr = False
        self.device.rts = False
        time.sleep(1 / 20)

        return True

    def close(self):
        """Close the serial communication port."""
        if self.device.is_open:
            self.device.close()
            self.device = None

    class Stk500v1(object):
        """It encapsulates the communication protocol that Arduino uses for the first
           versions of bootoloader, which can write up to 128 K bytes of flash memory.
           For example: Nano, Uno, etc"""
        def __init__(self, ab):
            self._ab = ab
            self._answer = None

        def open(self, port=None, speed=57600):
            """Find and open the communication port where the Arduino is connected.
               Generate the reset sequence with the DTR / RTS pins.
               Send the sync command to verify that there is a valid bootloader."""
            if self._ab.open(port, speed):
                return self.get_sync()

            return False

        def close(self):
            """Close the communication port."""
            self._ab.close()

        def get_sync(self):
            """Send the sync command whose function is to discard the reception buffers of both serial units.
              The first time you send the sync command to get rid of the line noise with a 200mS timeout.
            """
            self._ab.device.timeout = 1 / 5
            for i in range(1, 2):
                self._cmd_request(b"0 ", answer_len=2)

            self._ab.device.timeout = 1
            for i in range(1, 3):
                if self._cmd_request(b"0 ", answer_len=2):
                    return True
            return False

        def board_request(self):
            """Get the firmware and hardware version of the bootloader."""
            if not self._cmd_request(b"A\x80 ", answer_len=3):
                return False

            self._ab._hw_version = self._answer[1]

            if not self._cmd_request(b"A\x81 ", answer_len=3):
                return False

            self._ab._hw_version = self._answer[1]

            if not self._cmd_request(b"A\x82 ", answer_len=3):
                return False

            self._ab._sw_minor = self._answer[1]

            return True

        def cpu_signature(self):
            """Get information about the CPU, name and size of the flash memory page"""
            if self._cmd_request(b"u ", answer_len=5):
                if self._answer[1] == SIG1_ATMEL:
                    try:
                        list_cpu = AVR_ATMEL_CPUS[(self._answer[2], self._answer[3])]
                        self._ab._cpu_name = list_cpu[0]
                        self._ab._cpu_page_size = list_cpu[1]
                        self._ab._cpu_pages = list_cpu[2]
                        return True
                    except KeyError:
                        self._ab._cpu_name = "SIG2: {:02x} SIG3: {:02x}".format(self._answer[2], self._answer[3])
                        self._ab._cpu_page_size = 0
                        self._ab._cpu_pages = 0
            return False

        def write_memory(self, buffer, address, flash=True):
            """Write the buffer to the requested address of the flash memory or eeprom."""

            if self.set_address(address, flash):
                buff_len = len(buffer)

                cmd = bytearray(4)
                cmd[0] = ord('d')
                cmd[1] = ((buff_len >> 8) & 0xFF)
                cmd[2] = (buff_len & 0xFF)
                cmd[3] = ord('F') if flash else ord('E')

                cmd.extend(buffer)
                cmd.append(ord(' '))

                return self._cmd_request(cmd, answer_len=2)
            return False

        def read_memory(self, address, count, flash=True):
            """Read flash memory or eeprom from requested address."""

            if self.set_address(address, flash):
                cmd = bytearray(5)
                cmd[0] = ord('t')
                cmd[1] = ((count >> 8) & 0xFF)
                cmd[2] = (count & 0xFF)
                cmd[3] = ord('F') if flash else ord('E')
                cmd[4] = ord(' ')

                if self._cmd_request(cmd, answer_len=count+2):
                    # The answer start with RESP_STK_IN_SYNC and finish with RESP_STK_OK
                    buffer = bytearray(self._answer[1:count+1])

                    return buffer
            return None

        def set_address(self, address, flash):
            """The bootloader address flash is in words, and the eeprom in bytes."""
            if flash:
                address = int(address / 2)

            """The address is in little endian format"""
            cmd = bytearray(4)
            cmd[0] = ord('U')
            cmd[1] = (address & 0xFF)
            cmd[2] = ((address >> 8) & 0xFF)
            cmd[3] = ord(' ')

            return self._cmd_request(cmd, answer_len=2)

        def leave_prg_mode(self):
            """Tells the bootloader to leave programming mode and start executing the stored firmware"""
            return self._cmd_request(b"Q ", answer_len=2)

        def _cmd_request(self, msg, answer_len):
            """send and receive a command in stk500v1 format"""
            if self._ab.device:
                self._ab.device.write(msg)
                self._answer = self._ab.device.read(answer_len)

                if len(self._answer) == answer_len and \
                        self._answer[0] == RESP_STK_IN_SYNC and self._answer[answer_len - 1] == RESP_STK_OK:
                    return True
            return False

    class Stk500v2(object):
        """It encapsulates the communication protocol that Arduino uses in bootloaders
        with more than 128K bytes of flash memory. For example: Mega 2560 etc"""
        def __init__(self, ab):
            self._ab = ab
            self._answer = None
            self._sequence_number = 0

        def open(self, port=None, speed=115200):
            """Find and open the communication port where the Arduino is connected.
               Generate the reset sequence with the DTR / RTS pins.
               Send the sync command to verify that there is a valid bootloader."""
            if self._ab.open(port, speed):
                return self.get_sync()

            return False

        def close(self):
            """Close the communication port."""
            self._ab.close()

        def get_sync(self):
            """send the sync command and see if we can get there"""
            if self._send_command(CMD_SIGN_ON):
                if self._recv_answer(CMD_SIGN_ON):
                    prog_name_len = self._answer[0]
                    del self._answer[0]

                    self._ab._programmer_name = self._answer.decode("utf-8")
                    return True
            return False

        def board_request(self):
            """Get the firmware and hardware version of the bootloader."""

            if not self._get_params(OPT_HW_VERSION):
                return False

            self._ab._hw_version = self._answer[0]

            if not self._get_params(OPT_SW_MAJOR):
                return False

            self._ab._hw_version = self._answer[0]

            if not self._get_params(OPT_SW_MINOR):
                return False

            self._ab._sw_minor = self._answer[0]

            return True

        def _get_params(self, option):
            if self._send_command(CMD_GET_PARAMETER, option):
                return self._recv_answer(CMD_GET_PARAMETER)
            return False

        def _send_command(self, cmd, data=None):
            """The command is composed of a fixed header of 5 bytes plus the data with the checksum."""
            if self._ab.device:
                self._sequence_number += 1

                buff = bytearray(5)
                checksum = 0
                data_len = 1 if data is None else len(data) + 1

                buff[0] = MESSAGE_START
                buff[1] = self._sequence_number
                buff[2] = ((data_len >> 8) & 0xFF)
                buff[3] = (data_len & 0xFF)
                buff[4] = TOKEN
                buff.append(cmd)
                if not data is None:
                    buff.extend(data)

                for val in buff:
                    checksum ^= val

                buff.append(checksum)

                self._ab.device.write(buff)
                return True
            return False

        def _recv_answer(self, cmd):
            """the response is composed of a fixed size header, and the first two
            bytes of the data contain the command and the status of the operation."""
            head = bytearray(self._ab.device.read(5))

            """For the header to be valid, the beginning and end, plus the sequence number, must match."""
            if len(head) == 5 and head[0] == MESSAGE_START and\
                head[4] == TOKEN and self._sequence_number == head[1]:

                """one is added because the length does not include the checksum byte"""
                len_data = ((head[2] << 8) | head[3]) + 1

                """The minimum response contains the command and the status of the operation."""
                if len_data >= 3:
                    self._answer = bytearray(self._ab.device.read(len_data))
                    if len(self._answer) == len_data and\
                        self._answer[0] == cmd and self._answer[1] == 0:
                        answ_chk = self._answer[-1]
                        del self._answer[-1]

                        head.extend(self._answer)
                        checksum = 0
                        for val in head:
                            checksum ^= val
                        """discards the command and status from the response."""
                        del self._answer[0]
                        del self._answer[0]

                        """if the calculation matches the checksum, the answer is valid."""
                        return checksum == answ_chk
                return False