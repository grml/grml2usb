"""
grml2usb basic pytests
~~~~~~~~~~~~~~~~~~~~~~

This script contains basic "unit" tests, implemented for and executed with pytest.

Requirements:
pytest (pip install pytest)
pexpect (pip install pexpect)
pytest-mock (pip install pytest-mock)

Runwith:
<project root>$ pytest [-m {basic}]

:copyright: (c) 2020 by Manuel Rom <roma@https://synpro.solutions/>
:license: GPL v2 or any later version
:bugreports: http://grml.org/bugs/
"""

import pytest
import os

#import "hack", since grml2usb doesn't have the .py file ending
import imp; grml2usb = imp.load_source('grml2usb', 'grml2usb')

# region check_for_usb tests
@pytest.mark.check_for_usbdevice
def test_check_for_usb_invalid_param():
    assert grml2usb.check_for_usbdevice('foobar') == 0
    assert grml2usb.check_for_usbdevice('/dev/foobar') == 0

@pytest.mark.check_for_usbdevice
def test_check_for_usb_not_removable():
    assert grml2usb.check_for_usbdevice('/dev/sda') == 0

@pytest.mark.check_for_usbdevice
def test_extract_device_name_invalid():
    assert grml2usb.extract_device_name('/dev/sda/somethingelse') == None
    assert grml2usb.extract_device_name('/dev/sd*') == None

@pytest.mark.check_for_usbdevice
def test_extract_device_name():
    assert grml2usb.extract_device_name('/dev/sda') == 'sda'
    assert grml2usb.extract_device_name('/dev/hdb') == 'hdb'
    assert grml2usb.extract_device_name('/dev/loop0') == 'loop0'
    assert grml2usb.extract_device_name('/dev/null') == 'null'
    assert grml2usb.extract_device_name('/dev/nvme0n1p1') == 'nvme0n1p1'
    assert grml2usb.extract_device_name('/dev/fd0') == 'fd0'
    assert grml2usb.extract_device_name('/dev/tty0') == 'tty0'
    assert grml2usb.extract_device_name('/dev/mmcblk0') == 'mmcblk0'
    assert grml2usb.extract_device_name('/dev/sda6') == 'sda6'

# o_O moment: is the "if", currently at line 926 correct?
@pytest.mark.check_for_usbdevice
def test_mocked_full(mocker):
    mocker.patch('builtins.open', mocker.mock_open(read_data="1"))
    assert grml2usb.check_for_usbdevice('/dev/sda') == 1



# endregion
