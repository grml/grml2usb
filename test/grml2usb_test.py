"""
grml2usb basic pytests
~~~~~~~~~~~~~~~~~~~~~~

This script contains basic "unit" tests, implemented for and executed with pytest.

Requirements:
pytest (pip install pytest)
pexpect (pip install pexpect)

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
@pytest.mark.check_for_usb
def test_check_for_usb_invalid_param():
    with pytest.raises(AttributeError):
        assert grml2usb.check_for_usbdevice('foobar')
        assert grml2usb.check_for_usbdevice('/dev/foobar')

@pytest.mark.check_for_usb
def test_check_for_usb_not_removable():
    assert grml2usb.check_for_usbdevice('/dev/sda') == 0


# endregion
