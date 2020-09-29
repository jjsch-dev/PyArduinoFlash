#!/usr/bin/python

"""Arduino flash memory utility.
   It is used to write / verify and read the flash memory of an Arduino board.
   The input / output file format is Intel Hexadecimal."""

VERSION = '0.1.0'

import argparse
import sys

sys.path.append('../')

from intelhex import IntelHex
from intelhex import AddressOverlapError, HexRecordError
from arduinobootloader import ArduinoBootloader
import progressbar

parser = argparse.ArgumentParser(description="arduino flash utility")
group = parser.add_mutually_exclusive_group()
parser.add_argument("filename", help="filename in hexadecimal Intel format")
parser.add_argument("--version", action="store_true", help="script version")
parser.add_argument("-b", "--baudrate", type=int, required=True, help="old bootolader (57600) Optiboot (115200)")
group.add_argument("-r", "--read", action="store_true", help="read the cpu flash memory")
group.add_argument("-u", "--update", action="store_true", help="update cpu flash memory")
args = parser.parse_args()

if args.version:
    print("version {}".format(VERSION))

if args.update:
    print("update Arduino firmware with filename: {}".format(args.filename))
elif args.read:
    print("save the Arduino firmware in filename: {}".format(args.filename))
else:
    parser.print_help()
    sys.exit()

ih = IntelHex()
ab = ArduinoBootloader()

if ab.open(speed=args.baudrate):
    print("AVR device initialized and ready to accept instructions")
    address = 0
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

        try:
            ih.fromfile(args.filename, format='hex')
        except FileNotFoundError:
            print("error, file not found")
            ab.close()
            sys.exit()
        except (AddressOverlapError, HexRecordError):
            print("error, file format")
            ab.close()
            sys.exit()

        print("writing flash: {} bytes".format(ih.maxaddr()))
        bar = progressbar.ProgressBar(max_value=ih.maxaddr(), prefix="writing ")
        bar.start()
        for address in range(0, ih.maxaddr(), ab.cpu_page_size):
            buffer = ih.tobinarray(start=address, size=ab.cpu_page_size)
            if not ab.write_memory(buffer, address):
                print("error, writing flash memory")
                ab.leave_prg_mode()
                ab.close()
                sys.exit(0)

            bar.update(address)

        bar.update(address)
        bar.finish()

    dict_hex = dict()

    if args.update:
        max_address = ih.maxaddr()
        print("reading and verifying flash memory")
    elif args.read:
        max_address = int(ab.cpu_page_size * ab.cpu_pages)
        print("reading flash memory")
    else:
        max_address = 0

    bar = progressbar.ProgressBar(max_value=max_address, prefix="reading ").start()
    bar.start()

    for address in range(0, max_address, ab.cpu_page_size):
        read_buffer = ab.read_memory(address, ab.cpu_page_size)
        if read_buffer is None:
            print("error, reading flash memory")
            ab.close()
            sys.exit()

        if args.update:
            if read_buffer != ih.tobinarray(start=address, size=ab.cpu_page_size):
                print("file not match")
                ab.close()
                sys.exit()
        elif args.read:
            for i in range(0, ab.cpu_page_size):
                dict_hex[address + i] = read_buffer[i]

        bar.update(address)

    bar.update(address)
    bar.finish()

    if args.read:
        dict_hex["start_addr"] = 0
        ih.fromdict(dict_hex)
        try:
            ih.tofile(args.filename, 'hex')
        except FileNotFoundError:
            print("error, the file cannot be created")
            ab.leave_prg_mode()
            ab.close()
            sys.exit()

    print("\nflash done, thank you")

    ab.leave_prg_mode()
    ab.close()
else:
    print("error, could not connect with arduino board - baudrate: {}".format(args.baudrate))
