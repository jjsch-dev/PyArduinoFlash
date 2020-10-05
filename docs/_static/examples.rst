Source Code Example
==========================================

.. code-block:: python

    from intelhex import IntelHex
    from arduinobootloader import ArduinoBootloader

    def update(self):
        ih = IntelHex()
        ab = ArduinoBootloader()
        prg = ab.select_programmer("Stk500v1")

        if prg.open():
            if not prg.board_request():
                prg.close()
                return

            print("botloader name: {} version: {} hardware: {}".format(ab.programmer_name,
                                                                       ab.sw_version,
                                                                       ab.hw_version))

            if not prg.cpu_signature():
                prg.close()
                return

            print("cpu name: {}".format(ab.cpu_name) )

            ih.fromfile("firmware_file.hex", format='hex')

            for address in range(0, ih.maxaddr(), ab.cpu_page_size):
                buffer = ih.tobinarray(start=address, size=ab.cpu_page_size)
                if not prg.write_memory(buffer, address):
                   print("Write error")
                   prg.leave_bootloader()
                   prg.close()
                   return

            for address in range(0, ih.maxaddr(), ab.cpu_page_size):
                buffer = ih.tobinarray(start=address, size=ab.cpu_page_size)
                read_buffer = prg.read_memory(address, ab.cpu_page_size)
                if not len(read_buffer):
                   print("Read error")
                   break

                if buffer != read_buffer:
                   print("File not match")
                   break

            prg.leave_bootloader()
            prg.close()
