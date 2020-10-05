Usage
==========================================

The parsing of the file in `Intel hexadecimal format <https://en.wikipedia.org/wiki/Intel_HEX>`_ is done with the `IntelHex <https://github.com/python-intelhex/intelhex>`_ library.

To have an instance of the class use ``ab = ArduinoBootloader()``
Then select the protocol of the programmer ``prg = ab.select_protocol("Stk500v1")``.  To establish the connection with the bootloader of the Arduino board use ``prg.open()`` that returns ``True`` when it is successful.

As the library needs the information of the CPU to know the size and count of the flash page, use the method ``prg.board_request()`` and ``prg.cpu_signature()``

If the previous was successfully (they return ``True``), now open the hexadecimal file with the ``ih.fromfile("firmware_file.hex", format='hex')`` function. If there are errors in the format or the file path is invalid, exceptions are thrown.

To obtain the page of the current address, use the  ``ih.tobinarray(start=address, size=ab.cpu_page_size)`` .

For write it in the flash memory, use the method ``prg.write_memory(buffer, address)`` which take the buffer and the address as parameters. Returns ``True`` when success.
