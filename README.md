PyArduinoFlash
====


PyArduinoFlash is an open source in Python for updating the firmware 
of Arduino boards that use the ATmegaBOOT_168.c bootloader.

For example Arduino Nano.

The intention is to have a class that can be imported into any python project to update the Arduinos through the serial port.

It implements a subset of Atmel's STK-500 protocol, using as reference the source code of all Arduino bootloaders that use Atmel as a processor. 
[ArduinoCore-avr](https://github.com/arduino/ArduinoCore-avr/blob/master/bootloaders/atmega/ATmegaBOOT_168.c)

To have an example of use, there is an APP in [KivyMd](https://gitlab.com/kivymd/KivyMD) and [Kivy](http://kivy.org) that through a GUI exposes all the methods required to update and verify the firmware.

![alt text](https://github.com/jjsch-dev/PyArduinoFlash/tree/master/images/app_main.png?raw=true)

Installation, Documentation and Examples
----------------------------------------


Support
-------

If you need assistance, you can ask for help on our mailing list:

* Email      : juanschiavoni@gmail.com


Contributing
------------


Licenses
--------

- PyArduinoFlash is released under the terms of the MIT License. Please refer to the
  LICENSE file.


