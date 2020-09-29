#!/usr/bin/python

'''Arduino flash memory utility.'''

VERSION = '0.1.0'

import argparse
import sys

sys.path.append('../')

from intelhex import IntelHex
from arduinobootloader import ArduinoBootloader
import progressbar

parser = argparse.ArgumentParser(description="arduino flash utility")
group = parser.add_mutually_exclusive_group()
parser.add_argument("filename", help="filename in hexadecimal Intel format")
parser.add_argument("--version", action="store_true", help="script version")
group.add_argument("-r", "--read", action="store_true", help="read the cpu flash memory")
group.add_argument("-u", "--update", action="store_true", help="update cpu flash memory")
args = parser.parse_args()

if args.version:
    print("version {}".format(VERSION))

if args.update:
    print("Update Arduino firmware with filename: {}".format(args.filename))
elif args.read:
    print("Save the Arduino firmware in filename: {}".format(args.filename))
else:
    parser.print_help()
    sys.exit()

ih = IntelHex()
ab = ArduinoBootloader()

if ab.open():
    print("AVR device initialized and ready to accept instructions")
    if not ab.board_request():
        ab.close()
        sys.exit(0)

    print("bootloader version: {} hardware version: {}".format(ab.sw_version, ab.hw_version))

    if not ab.cpu_signature():
        ab.close()
        sys.exit(0)

    print("cpu name: {}".format(ab.cpu_name))

    if args.update:
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

    if args.update:
        max_address = ih.maxaddr()
        print("reading and verifying flash memory")
    elif args.read:
        max_address = int(ab.cpu_page_size * ab.cpu_pages)
        dict_hex = dict()
        print("reading flash memory")

    bar = progressbar.ProgressBar(max_value=max_address, prefix="reading ").start()
    bar.start()

    for address in range(0, max_address, ab.cpu_page_size):
        if args.update:
            buffer = ih.tobinarray(start=address, size=ab.cpu_page_size)

        read_buffer = ab.read_memory(address, ab.cpu_page_size)
        if read_buffer is None:
            print("read error")
            ab.close()
            sys.exit()

        if args.update and buffer != read_buffer:
            print("file not match")
            ab.close()
            sys.exit()
        elif args.read:
            for i in range(0, ab.cpu_page_size):
                dict_hex[address + i] = read_buffer[i]

        bar.update(address)

    if args.read:
        dict_hex["start_addr"] = 0
        ih.fromdict(dict_hex)
        ih.tofile(args.filename, 'hex')

    bar.update(address)
    bar.finish()

    print("\nflash done, thank you")

    ab.leave_prg_mode()
    ab.close()
else:
    print("Error, can't connect to the arduino board")