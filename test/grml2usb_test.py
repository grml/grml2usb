"""
grml2usb basic pytests
~~~~~~~~~~~~~~~~~~~~~~

This script contains basic "unit" tests, implemented for and executed with pytest.

Requirements:
pytest (pip install pytest)
pytest-mock (pip install pytest-mock)

Runwith:
<project root>$ pytest [-m {basic}]

:copyright: (c) 2020 by Manuel Rom <roma@https://synpro.solutions/>
:license: GPL v2 or any later version
:bugreports: http://grml.org/bugs/
"""


import pytest
import os
import imp

#import "hack", since grml2usb doesn't have the .py file ending
grml2usb = imp.load_source('grml2usb', 'grml2usb')


# region check_for_usb tests

@pytest.mark.check_for_usbdevice
def test_extract_device_name():
    """Assert, that 'extract_device_name' returns a device name for a given path"""
    assert grml2usb.extract_device_name('/dev/sda') == 'sda'
    assert grml2usb.extract_device_name('/dev/sdb') == 'sdb'

@pytest.mark.check_for_usbdevice
def test_extract_device_name_invalid():
    """Assert, that 'extract_device_name' raises an Error, when given an incorrect string"""
    with pytest.raises(AttributeError):
        assert grml2usb.extract_device_name('/dev')
    with pytest.raises(AttributeError):
        assert grml2usb.extract_device_name('foobar')
