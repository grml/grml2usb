#!/usr/bin/env python
# Filename:      grml2usb
# Purpose:       install grml system to usb device
# Authors:       grml-team (grml.org), (c) Michael Prokop <mika@grml.org>
# Bug-Reports:   see http://grml.org/bugs/
# License:       This file is licensed under the GPL v2 or any later version.
################################################################################

# TODO:
# * write error messages to stderr
# * log wrapper (log important messages to syslog, depending on loglevel)
# * trap handling (umount devices when interrupting?)
# * integrate https://www.mirbsd.org/cvs.cgi/src/sys/arch/i386/stand/mbr/mbr.S?rev=HEAD;content-type=text%2Fplain
#   -> gcc -D_ASM_SOURCE  -D__BOOT_VER=\"GRML\" -DBOOTMANAGER -c mbr.S; ld
#      -nostdlib -Ttext 0 -N -Bstatic --oformat binary mbr.o -o mbrmgr

prog_version = "0.0.1"

import os, re, subprocess, sys
from optparse import OptionParser
from os.path import exists, join, abspath
from os import pathsep
from string import split

# cmdline parsing {{{
usage = "Usage: %prog [options] <ISO[s]> <partition>\n\
\n\
%prog installs a grml ISO to an USB device to be able to boot from it.\n\
Make sure you have at least a grml ISO or a running grml system,\n\
syslinux (just run 'aptitude install syslinux' on Debian-based systems)\n\
and root access."
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
parser.add_option("--uninstall", dest="uninstall", action="store_true",
                  help="remove grml ISO files")
parser.add_option("--verbose", dest="verbose", action="store_true",
                  help="enable verbose mode")
parser.add_option("-v", "--version", dest="version", action="store_true",
                  help="display version and exit")

(options, args) = parser.parse_args()
# }}}

# wrapper functions {{{
# TODO: implement argument handling
def execute(command):
    """Wrapper for executing a command. Either really executes
    the command (default) or when using --dry-run commandline option
    just displays what would be executed."""
    if options.dryrun:
        print "would execute %s now" % command
    else:
        print "executing %s" % command

def which(program):
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

def search_file(filename, search_path='/bin' + pathsep + '/usr/bin'):
   """Given a search path, find file"""
   file_found = 0
   paths = split(search_path, pathsep)
   for path in paths:
       for current_dir, directories, files in os.walk(path):
           if exists(join(current_dir, filename)):
              file_found = 1
              break
   if file_found:
      return abspath(join(current_dir, filename))
   else:
      return None
# }}}


def check_uid_root():
    """Check for root permissions"""
    if not os.geteuid()==0:
        sys.exit("Error: please run this script with uid 0 (root).")


def install_syslinux(device):
    """Install syslinux on specified device."""
    print("debug: syslinux %s") % device


def install_grub(device):
    """Install grub on specified device."""
    print("grub-install %s") % device


def install_bootloader(partition):
    """Install bootloader on device."""
    # Install bootloader on the device (/dev/sda), not on the partition itself (/dev/sda1)
    if partition[-1:].isdigit():
        device = re.match(r'(.*?)\d*$', partition).group(1)
    else:
        device = partition

    if options.grub:
        install_grub(device)
    else:
        install_syslinux(device)


def install_mbr(target):
    """Install a default master boot record on given target"""
    print("TODO")


def loopback_mount(iso, target):
    """Loopback mount specified ISO on given target"""
    print("mount -o loop %s %s") % (iso, target)


def check_for_vat(partition):
    """Check whether specified partition is VFAT/FAT16 filesystem"""
    try:
        udev_info = subprocess.Popen(["/lib/udev/vol_id", "-t",
            partition],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        filesystem = udev_info.communicate()[0].rstrip()

        if udev_info.returncode == 2:
            print("failed to read device %s - wrong UID / permissions?") % partition
            return 1

        if filesystem != "vfat":
            return(1)

        # TODO: check for ID_FS_VERSION=FAT16?

    except OSError:
        print("Sorry, /lib/udev/vol_id not available.")
        return 1

def copy_grml_files(grml_flavour, iso_mount, target):
    """Copy files from ISO on given target"""

    # TODO: provide alternative search_file() if file information is stored in
    # a config.ini file?
    squashfs = search_file(grml_flavour + '.squashfs', iso_mount)
    print("debug: copy squashfs to %s") % target + '/live/' + grml_flavour + '.squashfs'

    filesystem_module = search_file('filesystem.module', iso_mount)
    print("debug: copy filesystem.module to %s") % target + '/live/' + grml_flavour + '.module'

    kernel = search_file('linux26', iso_mount)
    print("debug: copy kernel to %s") % target + '/boot/release/' + grml_flavour + '/linux26'

    initrd = search_file('initrd.gz', iso_mount)
    print("debug: copy initrd to %s") % target + '/boot/release/' + grml_flavour + '/initrd.gz'

    logo = search_file('logo.16', iso_mount)
    print("debug: copy logo.16 to %s") % target + '/boot/isolinux/' + 'logo.16'

    for file in 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10':
        bootsplash = search_file(file, iso_mount)
        print("debug: copy %s to %s") % (bootsplash, target + '/boot/isolinux/' + file)


def uninstall_files(device):
    print("TODO")


def identify_grml_flavour(mountpath):
    version_file = search_file('grml-version', mountpath)
    file = open(version_file, 'r')
    grml_info = file.readline()
    file.close
    grml_flavour = re.match(r'[\w-]*', grml_info).group()
    return grml_flavour


def main():
    if options.version:
        print("%s %s")% (os.path.basename(sys.argv[0]), prog_version)
        sys.exit(0)

    if len(args) < 2:
        parser.error("invalid usage")

    # check_uid_root()

    device = args[len(args) - 1]
    isos = args[0:len(args) - 1]

    if not which("syslinux"):
        print("Sorry, syslinux not available. Exiting.")
        print("Please install syslinux or consider using the --grub option.")
        sys.exit(1)

    # TODO check for valid blockdevice, vfat and mount functions
    # if device is not None:
        # check_for_vat(device)
        # mount_target(partition)

    target = '/mnt/target'

    # TODO it doesn't need to be a ISO, could be /live/image as well
    for iso in isos:
        print("debug: iso = %s") % iso
        # loopback_mount(iso)
        # copy_grml_files(iso, target)
        # loopback_unmount(iso)
        iso_mount = '/mnt/test' # FIXME

        grml_flavour = identify_grml_flavour(iso_mount)
        print("debug: grml_flavour = %s") % grml_flavour

        grml_flavour_short = grml_flavour.replace('-','')
        print("debug: grml_flavour_short = %s") % grml_flavour_short

        copy_grml_files(grml_flavour, iso_mount, target)

    if options.mbr:
        print("debug: would install MBR now")

    install_bootloader(device)

if __name__ == "__main__":
    main()

## END OF FILE #################################################################
# vim:foldmethod=marker expandtab ai ft=python tw=120
