#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
grml2usb
~~~~~~~~

This script installs a grml system to a USB device

:copyright: (c) 2009 by Michael Prokop <mika@grml.org>
:license: GPL v2 or any later version
:bugreports: http://grml.org/bugs/

TODO
----

* implement missing options (--kernel, --initrd, --uninstall,...)
* improve error handling :)
* get rid of "if not dry_run" inside code/functions
* implement mount handling
* log wrapper (-> logging module)
* implement logic for storing information about copied files
  -> register every single file?
* trap handling (like unmount devices when interrupting?)
* get rid of all TODOs in code :)
* graphical version
"""

import os, re, subprocess, sys, tempfile
from optparse import OptionParser
from os.path import exists, join, abspath
from os import pathsep
# TODO string.split() is deprecated - replace?
#      -> http://docs.python.org/library/string.html#deprecated-string-functions
from string import split

PROG_VERSION = "0.0.1"

# cmdline parsing
# TODO
# * --bootloader-only?
usage = "Usage: %prog [options] <ISO[s]> <partition>\n\
\n\
%prog installs a grml ISO to an USB device to be able to boot from it.\n\
Make sure you have at least a grml ISO or a running grml system,\n\
syslinux (just run 'aptitude install syslinux' on Debian-based systems)\n\
and root access."

parser = OptionParser(usage=usage)
parser.add_option("--bootoptions", dest="bootoptions",
                  action="store", type="string",
                  help="use specified bootoptions as defaut")
parser.add_option("--copy-only", dest="copyonly", action="store_true",
                  help="copy files only and do not install bootloader")
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


def execute(f, *args):
    """Wrapper for executing a command. Either really executes
    the command (default) or when using --dry-run commandline option
    just displays what would be executed."""
    # demo: execute(subprocess.Popen, (["ls", "-la"]))
    if options.dryrun:
        print "would execute %s(%s) now" % (f, args)
    else:
        return f(*args)


def is_exe(fpath):
    """Check whether a given file can be executed

    @fpath: full path to file
    @return:"""
    return os.path.exists(fpath) and os.access(fpath, os.X_OK)


def which(program):
    """Check whether a given program is available in PATH

    @program: name of executable"""
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


def check_uid_root():
    """Check for root permissions"""
    if not os.geteuid()==0:
        sys.exit("Error: please run this script with uid 0 (root).")


def install_syslinux(device, dry_run=False):
    # TODO
    """Install syslinux on specified device."""
    print("debug: syslinux %s [TODO]") % device

    # syslinux -d boot/isolinux /dev/usb-sdb1


def generate_grub_config(grml_flavour):
    """Generate grub configuration for use via menu,lst"""

    # TODO
    # * install main part of configuration just *once* and append
    #   flavour specific configuration only
    # * what about systems using grub2 without having grub1 available?
    # * support grub2?

    grml_name = grml_flavour

    return("""\
# misc options:
timeout 30
# color red/blue green/black
splashimage=/boot/grub/splash.xpm.gz
foreground  = 000000
background  = FFCC33

# define entries:
title %(grml_name)s  - Default boot (using 1024x768 framebuffer)
kernel /boot/release/%(grml_name)s/linux26 apm=power-off lang=us vga=791 quiet boot=live nomce module=%(grml_name)s
initrd /boot/release/%(grml_name)s/initrd.gz

# TODO: extend configuration :)
""" % locals())


def generate_isolinux_splash(grml_flavour):
    """Generate bootsplash for isolinux/syslinux"""

    # TODO
    # * adjust last bootsplash line

    grml_name = grml_flavour

    return("""\
17/boot/isolinux/logo.16

Some information and boot options available via keys F2 - F10. http://grml.org/
%(grml_name)s
""" % locals())

def generate_syslinux_config(grml_flavour):
    """Generate configuration for use in syslinux.cfg"""

    # TODO
    # * install main part of configuration just *once* and append
    #   flavour specific configuration only
    # * unify isolinux and syslinux setup ("INCLUDE /boot/...")
    #   as far as possible

    grml_name = grml_flavour

    return("""\
# use this to control the bootup via a serial port
# SERIAL 0 9600
DEFAULT grml
TIMEOUT 300
PROMPT 1
DISPLAY /boot/isolinux/boot.msg
F1 /boot/isolinux/boot.msg
F2 /boot/isolinux/f2
F3 /boot/isolinux/f3
F4 /boot/isolinux/f4
F5 /boot/isolinux/f5
F6 /boot/isolinux/f6
F7 /boot/isolinux/f7
F8 /boot/isolinux/f8
F9 /boot/isolinux/f9
F10 /boot/isolinux/f10

LABEL grml
KERNEL /boot/release/%(grml_name)s/linux26
APPEND initrd=/boot/release/%(grml_name)s/initrd.gz apm=power-off lang=us boot=live nomce module=%(grml_name)s

# TODO: extend configuration :)
""" % locals())


def install_grub(device, dry_run=False):
    """Install grub on specified device."""
    print("grub-install %s") % device


def install_bootloader(partition, dry_run=False):
    """Install bootloader on device."""
    # Install bootloader on the device (/dev/sda),
    # not on the partition itself (/dev/sda1)
    if partition[-1:].isdigit():
        device = re.match(r'(.*?)\d*$', partition).group(1)
    else:
        device = partition

    if options.grub:
        install_grub(device, dry_run)
    else:
        install_syslinux(device, dry_run)


def is_writeable(device):
    """Check if the device is writeable for the current user"""

    if not device:
        return False
        #raise Exception, "no device for checking write permissions"

    if not os.path.exists(device):
        return False

    return os.access(device, os.W_OK) and os.access(device, os.R_OK)

def install_mbr(device, dry_run=False):
    """Install a default master boot record on given device

    @device: device where MBR should be installed to"""

    if not is_writeable(device):
        raise IOError, "device not writeable for user"

    lilo = './lilo/lilo.static' # FIXME

    if not is_exe(lilo):
        raise Exception, "lilo executable not available."

    # to support -A for extended partitions:
    print("debug: ./lilo/lilo.static -S /dev/null -M %s ext") % device
    proc = subprocess.Popen(["./lilo/lilo.static", "-S", "/dev/null", "-M", device, "ext"])
    proc.wait()
    if proc.returncode != 0:
        raise Exception, "error executing lilo"

    # activate partition:
    print("debug: ./lilo/lilo.static -S /dev/null -A %s 1") % device
    if not dry_run:
        proc = subprocess.Popen(["./lilo/lilo.static", "-S", "/dev/null", "-A", device, "1"])
        proc.wait()
        if proc.returncode != 0:
            raise Exception, "error executing lilo"

    # lilo's mbr is broken, use the one from syslinux instead:
    print("debug: cat /usr/lib/syslinux/mbr.bin > %s") % device
    if not dry_run:
        try:
            # TODO use Popen instead?
            retcode = subprocess.call("cat /usr/lib/syslinux/mbr.bin > "+ device, shell=True)
            if retcode < 0:
                print >> sys.stderr, "Error copying MBR to device", -retcode
        except OSError, error:
            print >> sys.stderr, "Execution failed:", error


def mount(source, target, options):
    """Mount specified source on given target

    @source: name of device/ISO that should be mounted
    @target: directory where the ISO should be mounted to
    @options: mount specific options"""

    print("debug: mount %s %s %s [TODO]") % (options, source, target)


def unmount(directory):
    """Unmount specified directory

    @directory: directory where something is mounted on and which should be unmounted"""

    print("debug: umount %s [TODO]") % directory


def check_for_vat(partition):
    """Check whether specified partition is a valid VFAT/FAT16 filesystem

    @partition: device name of partition"""

    try:
        udev_info = subprocess.Popen(["/lib/udev/vol_id", "-t",
            partition],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        filesystem = udev_info.communicate()[0].rstrip()

        if udev_info.returncode == 2:
            print("failed to read device %s - wrong UID / permissions?") % partition
            return 1

        if filesystem != "vfat":
            return(1)

        # TODO
        # * check for ID_FS_VERSION=FAT16 as well?

    except OSError:
        print("Sorry, /lib/udev/vol_id not available.")
        return 1


def mkdir(directory):
    """Simple wrapper around os.makedirs to get shell mkdir -p behaviour"""

    if not os.path.isdir(directory):
        try:
            os.makedirs(directory)
        except OSError:
            # just silently pass as it's just fine it the directory exists
            pass


def copy_grml_files(grml_flavour, iso_mount, target, dry_run=False):
    """Copy files from ISO on given target"""

    # TODO
    # * provide alternative search_file() if file information is stored in a config.ini file?
    # * catch "install: .. No space left on device" & CO
    # * abstract copy logic to make the code shorter and get rid of spaghetti ;)

    print("Copying files. This might take a while....")

    squashfs = search_file(grml_flavour + '.squashfs', iso_mount)
    squashfs_target = target + '/live/'
    execute(mkdir, squashfs_target)

    # use install(1) for now to make sure we can write the files afterwards as normal user as well
    print("cp %s %s") % (squashfs, target + '/live/' + grml_flavour + '.squashfs')
    execute(subprocess.Popen, ["install", "--mode=664", squashfs, squashfs_target + grml_flavour + ".squashfs"])

    filesystem_module = search_file('filesystem.module', iso_mount)
    print("cp %s %s") % (filesystem_module, squashfs_target + grml_flavour + '.module')
    execute(subprocess.Popen, ["install", "--mode=664", filesystem_module, squashfs_target + grml_flavour + '.module'])

    release_target = target + '/boot/release/' + grml_flavour
    execute(mkdir, release_target)

    kernel = search_file('linux26', iso_mount)
    print("cp linux26 %s") % release_target + '/linux26'
    execute(subprocess.Popen, ["install", "--mode=664", kernel, release_target + '/linux26'])

    initrd = search_file('initrd.gz', iso_mount)
    print("debug: copy initrd to %s") % release_target + '/initrd.gz'
    execute(subprocess.Popen, ["install", "--mode=664", initrd, release_target + '/initrd.gz'])

    if not options.copyonly:
        isolinux_target = target + '/boot/isolinux/'
        execute(mkdir, isolinux_target)

        logo = search_file('logo.16', iso_mount)
        print("debug: copy logo.16 to %s") % isolinux_target + 'logo.16'
        execute(subprocess.Popen, ["install", "--mode=664", logo, isolinux_target + 'logo.16'])

        for ffile in 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10':
            bootsplash = search_file(ffile, iso_mount)
            print("debug: copy %s to %s") % (bootsplash, isolinux_target + ffile)
            execute(subprocess.Popen, ["install", "--mode=664", bootsplash, isolinux_target + ffile])

        grub_target = target + '/boot/grub/'
        execute(mkdir, grub_target)

        print("debug: copy grub/splash.xpm.gz to %s") % grub_target + 'splash.xpm.gz'
        execute(subprocess.Popen, ["install", "--mode=664", 'grub/splash.xpm.gz', grub_target + 'splash.xpm.gz'])

        print("debug: copy grub/stage2_eltorito to %s") % grub_target + 'stage2_eltorito'
        execute(subprocess.Popen, ["install", "--mode=664", 'grub/stage2_eltorito', grub_target + 'stage2_eltorito'])

        print("debug: generating grub configuration %s") % grub_target + 'menu.lst'
        if not dry_run:
            grub_config_file = open(grub_target + 'menu.lst', 'w')
            grub_config_file.write(generate_grub_config(grml_flavour))
            grub_config_file.close( )

        syslinux_target = target + '/boot/isolinux/'
        execute(mkdir, syslinux_target)

        print("debug: generating syslinux configuration %s") % syslinux_target + 'syslinux.cfg'
        if not dry_run:
            syslinux_config_file = open(syslinux_target + 'syslinux.cfg', 'w')
            syslinux_config_file.write(generate_syslinux_config(grml_flavour))
            syslinux_config_file.close( )

        print("debug: generating isolinux/syslinux splash %s") % syslinux_target + 'boot.msg'
        if not dry_run:
            isolinux_splash = open(syslinux_target + 'boot.msg', 'w')
            isolinux_splash.write(generate_isolinux_splash(grml_flavour))
            isolinux_splash.close( )


def uninstall_files(device):
    """Get rid of all grml files on specified device"""

    # TODO
    print("TODO: %s") % device


def identify_grml_flavour(mountpath):
    """Get name of grml flavour

    @mountpath: path where the grml ISO is mounted to
    @return: name of grml-flavour"""

    version_file = search_file('grml-version', mountpath)

    if version_file == "":
        print("gucku")

    try:
        tmpfile = open(version_file, 'r')
        grml_info = tmpfile.readline()
        grml_flavour = re.match(r'[\w-]*', grml_info).group()
    except TypeError:
        raise
    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise

    return grml_flavour


def main():
    """Main function [make pylint happy :)]"""

    if options.version:
        print("%s %s")% (os.path.basename(sys.argv[0]), PROG_VERSION)
        sys.exit(0)

    if len(args) < 2:
        parser.error("invalid usage")

    if options.dryrun:
        print("Running in simulate mode as requested via option dry-run.")
    else:
        check_uid_root()

    device = args[len(args) - 1]
    isos = args[0:len(args) - 1]

    if not which("syslinux"):
        print >> sys.stderr, 'Sorry, syslinux not available. Exiting.'
        print >> sys.stderr, 'Please install syslinux or consider using the --grub option.'
        sys.exit(1)

    # TODO
    # * check for valid blockdevice, vfat and mount functions
    # if device is not None:
        # check_for_vat(device)
        # mount_target(partition)

    # TODO
    # * it doesn't need to be a ISO, could be /live/image as well
    for iso in isos:
        print("debug: iso = %s") % iso

        if os.path.isdir(iso):
            print("TODO: /live/image handling not yet implemented") # TODO
        else:
            iso_mountpoint = '/mnt/test'     # FIXME
            # iso_mount = tempfile.mkdtemp()
            mount(iso, iso_mountpoint, "-o loop -t iso9660")
            # device_mountpoint = '/mnt/usb-sdb1'
            # device_mountpoint = tempfile.mkdtemp()
            device_mountpoint = '/dev/shm/grml2usb' # FIXME
            mount(device, device_mountpoint, "")

            try:
                grml_flavour = identify_grml_flavour(iso_mountpoint)
                print("Identified grml flavour \"%s\".") % grml_flavour
            except TypeError:
                print("Fatal: could not identify grml flavour, sorry.")
                sys.exit(1)

            # grml_flavour_short = grml_flavour.replace('-','')
            #p rint("debug: grml_flavour_short = %s") % grml_flavour_short

            copy_grml_files(grml_flavour, iso_mountpoint, device_mountpoint, dry_run=options.dryrun)

            unmount(device_mountpoint)     # TODO
            unmount(iso_mountpoint)  # TODO

            #if os.path.isdir(target):
            #    os.rmdir(target)
            #if os.path.isdir(iso_mount):
            #    os.rmdir(iso_mount)


    if options.mbr:
        # make sure we install MBR on /dev/sdX and not /dev/sdX#
        if device[-1:].isdigit():
            device = re.match(r'(.*?)\d*$', device).group(1)

        try:
            install_mbr(device, dry_run=options.dryrun)
        except IOError, error:
            print >> sys.stderr, "Execution failed:", error
            sys.exit(1)
        except Exception, error:
            print >> sys.stderr, "Execution failed:", error
            sys.exit(1)

    if options.copyonly:
        print("Not installing bootloader and its files as requested via option copyonly.")
    else:
        install_bootloader(device, dry_run=options.dryrun)

    print("Finished execution of grml2usb (%s). Have fun with your grml system.") % PROG_VERSION

if __name__ == "__main__":
    main()

## END OF FILE #################################################################
# vim:foldmethod=marker expandtab ai ft=python tw=120 fileencoding=utf-8
