#!/usr/bin/env python
# Filename:      grml2usb
# Purpose:       install grml-system to usb-device
# Authors:       grml-team (grml.org), (c) Michael Prokop <mika@grml.org>
# Bug-Reports:   see http://grml.org/bugs/
# License:       This file is licensed under the GPL v2 or any later version.
################################################################################

prog_version = "0.0.1"

import os, sys
from optparse import OptionParser

# cmdline parsing {{{
usage = "usage: %prog [options] arg1 arg2"
parser = OptionParser(usage=usage)

parser.add_option("--bootoptions", dest="bootoptions", action="store", type="string",
                  help="use specified bootoptions as defaut")
parser.add_option("--dry-run", dest="dryrun", action="store_true",
                  help="do not actually execute any commands")
parser.add_option("--fat16", dest="fat16", action="store_true",
                  help="format specified partition with FAT16")
parser.add_option("--force", dest="force", action="store_true",
                  help="force any actions requiring manual interaction")
parser.add_option("--grub", dest="grub", action="store_true",
                  help="install grub bootloader instead of syslinux")
parser.add_option("--initrd", dest="initrd", action="store", type="string",
                  help="install specified initrd instead of the default")
parser.add_option("--kernel", dest="kernel", action="store", type="string",
                  help="install specified kernel instead of the default")
parser.add_option("--mbr", dest="mbr", action="store_true",
                  help="install master boot record (MBR) on the device")
parser.add_option("--squashfs", dest="squashfs", action="store", type="string",
                  help="install specified squashfs file instead of the default")
parser.add_option("--verbose", dest="verbose", action="store_true",
                  help="enable verbose mode")
parser.add_option("-v", "--version", dest="version", action="store_true",
                  help="display version and exit")

(options, args) = parser.parse_args()
# }}}

# FIXME: implement argument handling
def execute(command):
    """Wrapper for executing a command. Either really executes
    the command (default) or when using --dry-run commandline option
    just displays what would be executed."""
    if options.dryrun:
        print "would execute %s now" % command
    else:
        print "executing %s" % command

def install_syslinux(device):
    """Install syslinux on specified device."""
    print("syslinux %s") % device

def install_grub(device):
    """Install grub on specified device."""
    print("grub-install %s") % device

def install_bootloader(device):
    """Install bootloader on specified device."""
    if options.grub:
        install_grub(device)
    else:
        install_syslinux(device)

def check_uid_root():
    """Check for root permissions"""
    if not os.geteuid()==0:
        sys.exit("Error: please run this script with uid 0 (root).")

def main():
    if options.version:
        print("%s %s")% (os.path.basename(sys.argv[0]), prog_version)
        sys.exit(0)

    if len(args) < 2:
        parser.error("invalid usage")

    # check_uid_root()

    device = args[len(args) - 1]
    isos = args[0:len(args) - 1]

    # FIXME: check for valid blockdevice
    if device is not None:
        install_bootloader(device)

    for iso in isos:
        print("iso = %s") % iso

if __name__ == "__main__":
    main()

## END OF FILE #################################################################
# vim:foldmethod=marker expandtab ai ft=python
