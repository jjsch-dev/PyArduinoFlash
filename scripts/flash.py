#!/usr/bin/python

'''Flash Arduino Firmware utility.'''

VERSION = '0.1.0'

import argparse
import sys

sys.path.append('../')

from intelhex import IntelHex
from arduinobootloader import ArduinoBootloader
import progressbar

parser = argparse.ArgumentParser()
parser.add_argument("--version", action="store_true", help="script version")
parser.add_argument("filename", help="firmware filename in hexadecimal Intel format")
args = parser.parse_args()

if args.version:
    print("version {}".format(VERSION))

print("Update Arduino firmware - filename: {}".format(args.filename))

ih = IntelHex()
ab = ArduinoBootloader()

if ab.open():
    print("AVR device initialized and ready to accept instructions")
    if not ab.board_request():
        ab.close()
        sys.exit(0)

    print("botloader version: {} hardware version: {}".format(ab.sw_version, ab.hw_version))

    if not ab.cpu_signature():
        ab.close()
        sys.exit(0)

    print("cpu name: {}".format(ab.cpu_name))

    print("reading input file: {}".format(args.filename))
    ih.fromfile(args.filename, format='hex')

    print("writing flash: {} bytes".format(ih.maxaddr()))
    bar = progressbar.ProgressBar(max_value=ih.maxaddr(), prefix="writing ")
    bar.start()

    for address in range(0, ih.maxaddr(), ab.cpu_page_size):
        buffer = ih.tobinarray(start=address, size=ab.cpu_page_size)
        if not ab.write_memory(buffer, address):
            print("write error")
            ab.leave_prg_mode()
            ab.close()
            sys.exit(0)

        bar.update(address)

    bar.update(address)
    bar.finish()

    print("reading and verifying flash memory")
    bar = progressbar.ProgressBar(max_value=ih.maxaddr(), prefix="reading ").start()
    bar.start()
    for address in range(0, ih.maxaddr(), ab.cpu_page_size):
        buffer = ih.tobinarray(start=address, size=ab.cpu_page_size)
        read_buffer = ab.read_memory(address, ab.cpu_page_size)
        if not len(read_buffer):
            print("read error")
            break

        if buffer != read_buffer:
            print("rile not match")
            break

        bar.update(address)

    bar.update(address)
    bar.finish()
    print("\nflash done, thank you")

    ab.leave_prg_mode()
    ab.close()
else:
    print("Error, can't connect to the arduino board")