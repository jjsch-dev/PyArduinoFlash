from setuptools import setup
from os import path

DIR = path.dirname(path.abspath(__file__))

with open(path.join(DIR, 'README.md')) as f:
    README = f.read()
with open(path.join(DIR, 'requirements.txt')) as f:
    INSTALL_PACKAGES = f.read().splitlines()

setup(
    name='arduinobootloader',
    version='0.0.5',
    package_dir={'': 'arduinobootloader'},
    py_modules=['arduinobootloader'],
    url='https://github.com/jjsch-dev/PyArduinoFlash',
    install_requires=INSTALL_PACKAGES,
    license='MIT',
    author='Juan Schiavoni',
    author_email='juanschiavoni@gmail.com',
    description='Update the firmware of Arduino boards based on Atmel AVR',
    long_description=README,
    long_description_content_type='text/markdown',
    python_requires='>=3',
    keywords='arduino, flash, bootloader, upgrade',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
