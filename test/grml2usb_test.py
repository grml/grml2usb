"""
grml2usb basic pytests
~~~~~~~~~~~~~~~~~~~~~~

This script contains basic "unit" tests, implemented for and executed with pytest.

Requirements:
pytest (pip install pytest)

Runwith:
<project root>$ pytest [-m {basic}]

:copyright: (c) 2020 by Manuel Rom <roma@synpro.solutions>
:license: GPL v2 or any later version
:bugreports: http://grml.org/bugs/
"""

import importlib
import os
import subprocess

import pytest

grml2usb = importlib.import_module("grml2usb", ".")


@pytest.mark.check_for_usbdevice
def test_extract_device_name():
    """Assert, that 'extract_device_name' returns a device name for a given path"""
    assert grml2usb.extract_device_name("/dev/sda") == "sda"
    assert grml2usb.extract_device_name("/dev/sdb") == "sdb"
    assert grml2usb.extract_device_name("/dev/sdb4") == "sdb"


@pytest.mark.check_for_usbdevice
def test_extract_device_name_invalid():
    """Assert, that 'extract_device_name' raises an Error, when given an incorrect string"""
    with pytest.raises(AttributeError):
        assert grml2usb.extract_device_name("/dev")
    with pytest.raises(AttributeError):
        assert grml2usb.extract_device_name("foobar")


def _run_x(args, check: bool = True, **kwargs):
    # str-ify Paths, not necessary, but for readability in logs.
    args = [arg if isinstance(arg, str) else str(arg) for arg in args]
    args_str = '" "'.join(args)
    print(f'D: Running "{args_str}"', flush=True)
    return subprocess.run(args, check=check, **kwargs)


def _find_free_loopdev() -> str:
    return _run_x(["losetup", "-f"], capture_output=True).stdout.decode().strip()


def _identify_file(path) -> str:
    return _run_x(["file", path], capture_output=True).stdout.decode().strip().split(": ", 1)[1]


@pytest.mark.require_root
def test_smoke(tmp_path):
    loop_dev = _find_free_loopdev()
    partition = f"{loop_dev!s}p1"

    iso_url = "https://daily.grml.org/grml-small-amd64-unstable/latest/grml-small-amd64-unstable_latest.iso"
    iso_name = "grml.iso"
    if not os.path.exists(iso_name):
        _run_x(["curl", "-fSl#", "--output", iso_name, iso_url])

    grml2usb_options = grml2usb.parser.parse_args(["--format", "--force", iso_name, partition])
    print("Options:", grml2usb_options)

    part_size = 1 * 1024 * 1024  # 1 GB
    part_size_sectors = int(part_size * (1024 / 512))
    dd_size = str(int((part_size / 1024) + 100))

    # format (see sfdisk manual page):
    # <start>,<size_in_sectors>,<id>,<bootable>
    # 1st partition, EFI (FAT-12/16/32, ID ef) + bootable flag
    sfdisk_template = f"2048,{part_size_sectors},ef,*\n"
    print("Using sfdisk template:\n", sfdisk_template, "\n---")
    loop_backing_file = tmp_path / "loop"

    _run_x(["dd", "if=/dev/zero", f"of={loop_backing_file!s}", "bs=1M", f"count={dd_size}"])
    sfdisk_input_file = tmp_path / "sfdisk.txt"
    with sfdisk_input_file.open("wt") as fh:
        fh.write(sfdisk_template)
        fh.flush()

    with sfdisk_input_file.open() as fh:
        _run_x(["/sbin/sfdisk", loop_backing_file], stdin=fh)

    _run_x(["losetup", loop_dev, loop_backing_file])
    _run_x(["partprobe", loop_dev])

    try:
        grml2usb.main(grml2usb_options)
    finally:
        _run_x(["losetup", "-d", loop_dev])

    assert _identify_file(loop_backing_file).startswith("DOS/MBR boot sector; partition 1 : ID=0xef, active")
