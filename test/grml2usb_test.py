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



