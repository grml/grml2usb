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

import argparse
import importlib
import json
import logging
import os
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

grml2usb = importlib.import_module("grml2usb", ".")


@pytest.fixture(scope="session")
def iso_contents(tmp_path_factory):
    test_root = Path(__file__).absolute().parent
    base_contents_root = test_root / "iso-contents"
    synthesized_iso_root = tmp_path_factory.mktemp("isos")

    for base_iso in base_contents_root.glob("*/"):
        iso_name = base_iso.name
        synthesized_iso = synthesized_iso_root / iso_name
        shutil.copytree(base_iso, synthesized_iso)
        zeroed_file = base_contents_root / (iso_name + ".zeroed")

        for filename in zeroed_file.read_text().splitlines():
            dest_filename = synthesized_iso / Path(filename)
            dest_filename.parent.mkdir(parents=True, exist_ok=True)
            dest_filename.touch()

    yield synthesized_iso_root


def test_which_finds_existing_program():
    """which should find programs existing in PATH"""
    result = grml2usb.which("ls")
    assert result is not None
    assert result.endswith("/ls")
    assert os.path.isfile(result)


def test_which_returns_none_for_nonexistent_program():
    """which should return None for non-existing programs"""
    assert grml2usb.which("nonexistent_program_xyz123") is None


def test_which_skips_non_executable_files(tmp_path, monkeypatch):
    """which skips files that are not executable"""
    non_exe = tmp_path / "program"
    non_exe.touch()
    non_exe.chmod(0o644)
    monkeypatch.setenv("PATH", str(tmp_path))
    assert grml2usb.which("program") is None


def test_write_uuid(tmp_path):
    target_file = tmp_path / "test_uuid.txt"
    returned_uid = grml2usb.write_uuid(target_file)
    assert str(uuid.UUID(returned_uid)) == returned_uid
    assert target_file.read_text() == returned_uid


def test_get_target_bootid_existing(tmp_path):
    conf_dir = tmp_path / "conf"
    conf_dir.mkdir()
    bootid_file = conf_dir / "bootid.txt"
    existing_uuid = "12345678-1234-5678-1234-567812345678"
    bootid_file.write_text(existing_uuid)

    result = grml2usb.get_target_bootid(tmp_path)
    assert result == existing_uuid


def test_get_target_bootid_new(tmp_path, monkeypatch):
    monkeypatch.setattr(grml2usb, "execute", lambda f, *args: f(*args))
    conf_dir = tmp_path / "conf"
    result = grml2usb.get_target_bootid(tmp_path)
    assert str(uuid.UUID(result)) == result
    assert (conf_dir / "bootid.txt").read_text() == result


def test_build_grub_loopbackcfg(tmp_path):
    # Create some config files to be sourced
    grub_dir = tmp_path / "boot" / "grub"
    grub_dir.mkdir(parents=True)
    (grub_dir / "grml64_default.cfg").touch()
    (grub_dir / "grml32_default.cfg").touch()
    (grub_dir / "grml64_options.cfg").touch()

    grml2usb.build_grub_loopbackcfg(str(tmp_path))

    loopback_cfg = grub_dir / "loopback.cfg"
    lines = loopback_cfg.read_text().splitlines()

    assert lines == [
        "# grml2usb generated grub2 configuration file",
        "source /boot/grub/header.cfg",
        "source /boot/grub/grml32_default.cfg",
        "source /boot/grub/grml64_default.cfg",
        "source /boot/grub/grml64_options.cfg",
        "source /boot/grub/addons.cfg",
        "source /boot/grub/footer.cfg",
    ]


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
    with pytest.raises(AttributeError):
        assert grml2usb.extract_device_name("asdf/dev/sda")


def test_search_file(tmp_path):
    filename = "filename"
    (tmp_path / filename).write_text("test")
    assert grml2usb.search_file(filename, str(tmp_path)) == str(tmp_path / filename)


def test_search_file_subdir(tmp_path):
    filename = "filename"
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / filename).write_text("test")
    assert grml2usb.search_file(filename, str(tmp_path)) == str(subdir / filename)


def test_search_file_not_found(tmp_path):
    filename = "filename"
    assert grml2usb.search_file(filename, str(tmp_path)) is None


def test_search_dirs(tmp_path):
    filename = "filename"
    (tmp_path / filename).write_text("test")
    assert grml2usb.search_dirs(filename, str(tmp_path)) == [str(tmp_path / filename)]


def test_search_dirs_subdir(tmp_path):
    filename = "filename"
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / filename).write_text("test")
    assert grml2usb.search_dirs(filename, str(tmp_path)) == [str(subdir / filename)]


def test_search_dirs_not_found(tmp_path):
    filename = "filename"
    assert grml2usb.search_dirs(filename, str(tmp_path)) == []


def _run_x(args, check: bool = True, **kwargs):
    # str-ify Paths, not necessary, but for readability in logs.
    args = [arg if isinstance(arg, str) else str(arg) for arg in args]
    args_str = '" "'.join(args)
    print(f'D: Running "{args_str}"', flush=True)
    return subprocess.run(args, check=check, **kwargs)


def _find_free_loopdev() -> str:
    return _run_x(["losetup", "-f"], capture_output=True).stdout.decode().strip()


def _sfdisk_partitiontable(path) -> dict:
    data = json.loads(_run_x(["/sbin/sfdisk", "--json", path], capture_output=True).stdout.decode().strip())
    return data["partitiontable"]


def check_partition_table(path):
    partitiontable = _sfdisk_partitiontable(path)
    assert partitiontable["label"] == "dos"
    assert len(partitiontable["partitions"]) == 1  # should still have exactly one partition
    assert partitiontable["partitions"][0]["type"] == "ef"  # should still be an EFI partition
    assert partitiontable["partitions"][0]["bootable"] is True  # should still be active/bootable


def test_copy_and_configure_isolinux(tmp_path, monkeypatch, iso_contents: Path):
    options = argparse.Namespace()
    options.bootoptions = []
    options.dryrun = False
    options.removeoption = []
    options.skipsyslinuxconfig = False
    options.syslinuxlibs = []
    monkeypatch.setattr(grml2usb, "options", options)

    iso_name = "grml-full-2025.12-amd64"
    iso_mount = iso_contents / iso_name

    grml_flavours = grml2usb.identify_grml_flavour(str(iso_mount))
    assert grml_flavours == ["grml-full-amd64"]

    syslinux_target = tmp_path / "target" / "boot" / "syslinux"
    grml2usb.copy_and_configure_isolinux(str(iso_mount), str(syslinux_target) + "/", grml_flavours[0], "bootid")

    assert (syslinux_target / "syslinux.c32").exists()
    assert (syslinux_target / "isolinux.bin").exists()
    assert (syslinux_target / "f1").exists()
    assert (syslinux_target / "option_grml_full_amd64.cfg").exists()
    assert (syslinux_target / "defaults.cfg").read_text().strip() == "include grml_full_amd64_default.cfg"
    assert (syslinux_target / "hidden.cfg").exists()


@pytest.fixture
def loopdev_with_partition(tmp_path):
    loop_dev = _find_free_loopdev()
    partition = f"{loop_dev!s}p1"

    sector_size = 512
    start_sectors = 2048
    start_size = start_sectors * sector_size
    part_size = 2 * 1024 * 1024 * 1024  # 2 GB
    part_size_sectors = int(part_size / sector_size)

    loop_backing_file = tmp_path / "loop"
    with loop_backing_file.open("wb") as fh:
        fh.truncate(start_size + part_size)

    # format (see sfdisk manual page):
    # <start>,<size_in_sectors>,<id>,<bootable>
    # 1st partition, EFI (FAT-12/16/32, ID ef) + bootable flag
    sfdisk_template = f"2048,{part_size_sectors},ef,*\n"
    print("Using sfdisk template:\n", sfdisk_template, "\n---")

    sfdisk_input_file = tmp_path / "sfdisk.txt"
    with sfdisk_input_file.open("wt") as fh:
        fh.write(sfdisk_template)
        fh.flush()

    with sfdisk_input_file.open() as fh:
        _run_x(["/sbin/sfdisk", loop_backing_file], stdin=fh)

    check_partition_table(loop_backing_file)

    with loop_backing_file.open("rb") as fh:
        mbr = fh.read(512)
    print("Pristine MBR contents:", mbr.hex())

    _run_x(["losetup", loop_dev, loop_backing_file])
    _run_x(["partprobe", loop_dev])

    try:
        yield (loop_backing_file, loop_dev, partition)
    finally:
        _run_x(["losetup", "-d", loop_dev])


@pytest.fixture(scope="session")
def iso_amd64(tmp_path_factory):
    iso_url = "https://daily.grml.org/grml-small-amd64-unstable/latest/grml-small-amd64-unstable_latest.iso"
    iso_name = tmp_path_factory.mktemp("isos") / "grml-amd64.iso"
    if iso_name.exists():
        print(f"ISO {iso_name} already exists")
    else:
        _run_x(["curl", "-fSl#", "--output", iso_name, iso_url])
    yield str(iso_name)


@pytest.mark.require_root
@pytest.mark.parametrize(
    "options, expect_x86_mbr, expect_bootloader_message",
    [
        pytest.param([], True, "Using grub as bootloader", id="defaults"),
        pytest.param(["--bootloader=efi"], False, None, id="bootloader=efi"),
    ],
)
def test_smoke(
    iso_amd64,
    loopdev_with_partition,
    caplog,
    monkeypatch,
    options,
    expect_x86_mbr,
    expect_bootloader_message,
):
    caplog.set_level(logging.DEBUG)
    monkeypatch.setattr(grml2usb, "handle_logging", lambda: None)

    (loop_backing_file, loop_dev, partition) = loopdev_with_partition

    grml2usb_options = grml2usb.parser.parse_args(["--format", "--force", iso_amd64, partition] + options)
    print("Options:", grml2usb_options)

    grml2usb.main(grml2usb_options)

    with loop_backing_file.open("rb") as fh:
        mbr = fh.read(512)
    print("Finalized MBR contents:", mbr.hex())

    if expect_x86_mbr:
        assert not mbr.startswith(b"\x00\x00"), "MBR starts with zero-bytes, x86 BIOS will not boot"

    check_partition_table(loop_backing_file)

    if expect_bootloader_message:
        assert expect_bootloader_message in caplog.text
