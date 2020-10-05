Usage
==========================================
The following paragraph explains the basic flow to update the firmware of an Arduino board from Python.

Requirements
############
If the firmware file is in `Intel hexadecimal format <https://en.wikipedia.org/wiki/Intel_HEX>`_, use the `IntelHex <https://github.com/python-intelhex/intelhex>`_ library.

Select Programmer
#################
Get a instance of the class with

.. code-block:: python

    ab = ArduinoBootloader()

and select the protocol of the programmer with

.. code-block:: python

    prg = ab.select_protocol("Stk500v1")

Connect
#######
To establish the connection with the Arduino bootloader use

.. code-block:: python

    if prg.open(speed=115200):

that returns ``True`` when successful.


CPU information
###############
The library needs the information of the CPU to know the size and count of the flash page, use the method

.. code-block:: python

    if prg.cpu_signature():

that returns ``True`` when success. The properties have the corresponding information

.. code-block:: python

    ab.cpu_page_size
    ab.cpu_pages


Programmer information
######################
Although the information of the programmer is not important for the update process, because the bootoloader is an emulation of the Atmel programmers, you can do it with the method

.. code-block:: python

    prg.board_request()

that returns ``True`` when success.

The properties have the information.

.. code-block:: python

    ab.programmer_name
    ab.sw_version
    ab.hw_version

Open Firmware File
##################
Open the hexadecimal file with the method.
If there are errors in the format or the file path is invalid, exceptions are thrown.

.. code-block:: python

        try:
            ih.fromfile("filename.hex", format='hex')
        except FileNotFoundError:
            print("file not found")
        except (AddressOverlapError, HexRecordError):
            print("error, file format")

Parse the Firmware in Pages
###########################
To obtain the page of the current address, use the

.. code-block:: python

    buffer = ih.tobinarray(start=address, size=ab.cpu_page_size)

Write Pages
###########
For write it in the flash memory, use this method which take the buffer and the address as parameters and returns ``True`` when success.

.. code-block:: python

    if prg.write_memory(buffer, address):

Read Pages
##########
The read for example to verify, is done in the same way, with the exception that the method returns the memory buffer. When errors returns ``None``.

.. code-block:: python

    read_buffer = prg.read_memory(address, ab.cpu_page_size)
    if read_buffer is None:


Save in a File
##############
To save the read firmware to a hexadecimal format file, you need to buffer it in a dictionary where the key is the address of each byte on the page.

.. code-block:: python

    for i in range(0, ab.cpu_page_size):
        dict_hex[address + i] = read_buffer[i]

And when you have finished reading the flash, add the starting address
to generate the hexadecimal and to save the file

.. code-block:: python

    dict_hex["start_addr"] = 0
    ih.fromdict(dict_hex)
    ih.tofile("read_filename.hex", 'hex')

Execute the Firmware
#####################
The bootloader begins the execution of the firmware after a period of time without receiving communication; nevertheless it is convenient to execute the function

.. code-block:: python

    prg.leave_bootloader()

Close Communication
###################
Call the method to release the serial port

.. code-block:: python

    prg.close()