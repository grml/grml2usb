#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
grml2usb
~~~~~~~~

This script installs a grml system (running system / ISO[s]) to a USB device

:copyright: (c) 2009 by Michael Prokop <mika@grml.org>
:license: GPL v2 or any later version
:bugreports: http://grml.org/bugs/

TODO
----

* code improvements:
  - improve error handling :)
  - get rid of all TODOs in code :)
  - use 'with open("...", "w") as f: ... f.write("...")'
  - simplify functions/code as much as possible -> audit
* implement missing options (--kernel, --initrd, --uninstall,...)
* validate partition schema/layout: is the partition schema ok and the bootable flag set?
* implement logic for storing information about copied files -> register every file in a set()
* the last line in bootsplash (boot.msg) should mention all installed grml flavours
* extend flavour's syslinux configuration
* graphical version? :)
"""

from __future__ import with_statement
import os, re, subprocess, sys, tempfile
from optparse import OptionParser
from os.path import exists, join, abspath
from os import pathsep
from inspect import isroutine, isclass
import logging
import datetime, time

# global variables
PROG_VERSION = "0.0.1"
skip_mbr = False # By default we don't want to skip it; TODO - can we get rid of that?
mounted = set()  # register mountpoints
tmpfiles = set() # register tmpfiles
datestamp= time.mktime(datetime.datetime.now().timetuple()) # unique identifier for syslinux.cfg

# cmdline parsing
usage = "Usage: %prog [options] <[ISO[s] | /live/image]> </dev/ice>\n\
\n\
%prog installs a grml ISO to an USB device to be able to boot from it.\n\
Make sure you have at least a grml ISO or a running grml system (/live/image),\n\
syslinux (just run 'aptitude install syslinux' on Debian-based systems)\n\
and root access."

parser = OptionParser(usage=usage)
parser.add_option("--bootoptions", dest="bootoptions",
                  action="store", type="string",
                  help="use specified bootoptions as defaut")
parser.add_option("--bootloader-only", dest="bootloaderonly", action="store_true",
                  help="do not copy files only but just install a bootloader")
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
parser.add_option("--quiet", dest="quiet", action="store_true",
                  help="do not output anything than errors on console")
parser.add_option("--squashfs", dest="squashfs", action="store", type="string",
                  help="install specified squashfs file instead of the default")
parser.add_option("--uninstall", dest="uninstall", action="store_true",
                  help="remove grml ISO files")
parser.add_option("--verbose", dest="verbose", action="store_true",
                  help="enable verbose mode")
parser.add_option("-v", "--version", dest="version", action="store_true",
                  help="display version and exit")
(options, args) = parser.parse_args()


def cleanup():
    """TODO
    """

    logging.info("Cleaning up")
    proc = subprocess.Popen(["sync"])
    proc.wait()

    try:
        for device in mounted:
            unmount(device, "")
    # ignore: RuntimeError: Set changed size during iteration
    except:
        pass

def get_function_name(obj):
    if not (isroutine(obj) or isclass(obj)):
        obj = type(obj)
    return obj.__module__ + '.' + obj.__name__


def execute(f, *args):
    """Wrapper for executing a command. Either really executes
    the command (default) or when using --dry-run commandline option
    just displays what would be executed."""
    # demo: execute(subprocess.Popen, (["ls", "-la"]))
    if options.dryrun:
        logging.debug('dry-run only: %s(%s)' % (get_function_name(f), ', '.join(map(repr, args))))
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
    paths = search_path.split(pathsep)
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

    # syslinux -d boot/isolinux /dev/sdb1
    logging.info("Installing syslinux as bootloader")
    logging.debug("syslinux -d boot/syslinux %s" % device)
    proc = subprocess.Popen(["syslinux", "-d", "boot/syslinux", device])
    proc.wait()
    if proc.returncode != 0:
        raise Exception, "error executing syslinux"


def generate_grub_config(grml_flavour):
    """Generate grub configuration for use via menu,lst"""

    # TODO
    # * install main part of configuration just *once* and append
    #   flavour specific configuration only
    # * what about systems using grub2 without having grub1 available?
    # * support grub2?

    return("""\
# misc options:
timeout 30
# color red/blue green/black
splashimage=/boot/grub/splash.xpm.gz
foreground  = 000000
background  = FFCC33

# define entries:
title %(grml_flavour)s  - Default boot (using 1024x768 framebuffer)
kernel /boot/release/%(grml_flavour)s/linux26 apm=power-off lang=us vga=791 quiet boot=live nomce module=%(grml_flavour)s
initrd /boot/release/%(grml_flavour)s/initrd.gz

# TODO: extend configuration :)
""" % locals())


def generate_isolinux_splash(grml_flavour):
    """Generate bootsplash for isolinux/syslinux"""

    # TODO
    # * adjust last bootsplash line

    grml_name = grml_flavour

    return("""\
17/boot/syslinux/logo.16

Some information and boot options available via keys F2 - F10. http://grml.org/
%(grml_name)s
""" % locals())

def generate_main_syslinux_config(grml_flavour, grml_bootoptions):
    """Generate main configuration for use in syslinux.cfg"""

    # TODO
    # * install main part of configuration just *once* and append
    #   flavour specific configuration only
    # * unify isolinux and syslinux setup ("INCLUDE /boot/...")
    #   as far as possible

    local_datestamp = datestamp

    return("""\
## main syslinux configuration - generated by grml2usb [main config generated at: %(local_datestamp)s]
# use this to control the bootup via a serial port
# SERIAL 0 9600
DEFAULT grml
TIMEOUT 300
PROMPT 1
DISPLAY /boot/syslinux/boot.msg
F1 /boot/syslinux/boot.msg
F2 /boot/syslinux/f2
F3 /boot/syslinux/f3
F4 /boot/syslinux/f4
F5 /boot/syslinux/f5
F6 /boot/syslinux/f6
F7 /boot/syslinux/f7
F8 /boot/syslinux/f8
F9 /boot/syslinux/f9
F10 /boot/syslinux/f10
## end of main configuration

# flavour specific configuration for grml
LABEL  grml
KERNEL /boot/release/%(grml_flavour)s/linux26
APPEND initrd=/boot/release/%(grml_flavour)s/initrd.gz apm=power-off boot=live nomce quiet module=%(grml_flavour)s %(grml_bootoptions)s

""" % locals())

def generate_flavour_specific_syslinux_config(grml_flavour, bootoptions):
    """Generate flavour specific configuration for use in syslinux.cfg"""

    local_datestamp = datestamp

    return("""\

# flavour specific configuration for %(grml_flavour)s [grml2usb for %(grml_flavour)s: %(local_datestamp)s]
LABEL  %(grml_flavour)s
KERNEL /boot/release/%(grml_flavour)s/linux26
APPEND initrd=/boot/release/%(grml_flavour)s/initrd.gz apm=power-off boot=live nomce quiet module=%(grml_flavour)s %(bootoptions)s
""" % locals())


def install_grub(device, dry_run=False):
    """Install grub on specified device."""
    logging.critical("TODO: grub-install %s"  % device)


def install_bootloader(partition, dry_run=False):
    """Install bootloader on device."""

    # Install bootloader on the device (/dev/sda),
    # not on the partition itself (/dev/sda1)?
#    if partition[-1:].isdigit():
#        device = re.match(r'(.*?)\d*$', partition).group(1)
#    else:
#        device = partition

    if options.grub:
        install_grub(partition, dry_run)
    else:
        install_syslinux(partition, dry_run)


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

    lilo = '/grml/git/grml2usb/lilo/lilo.static' # FIXME

    if not is_exe(lilo):
        raise Exception, "lilo executable not available."

    # to support -A for extended partitions:
    logging.info("Installing MBR")
    logging.debug("%s -S /dev/null -M %s ext" % (lilo, device))
    proc = subprocess.Popen([lilo, "-S", "/dev/null", "-M", device, "ext"])
    proc.wait()
    if proc.returncode != 0:
        raise Exception, "error executing lilo"

    # activate partition:
    logging.debug("%s -S /dev/null -A %s 1" % (lilo, device))
    if not dry_run:
        proc = subprocess.Popen([lilo, "-S", "/dev/null", "-A", device, "1"])
        proc.wait()
        if proc.returncode != 0:
            raise Exception, "error executing lilo"

    # lilo's mbr is broken, use the one from syslinux instead:
    logging.debug("cat /usr/lib/syslinux/mbr.bin > %s" % device)
    if not dry_run:
        try:
            # TODO -> use Popen instead?
            retcode = subprocess.call("cat /usr/lib/syslinux/mbr.bin > "+ device, shell=True)
            if retcode < 0:
                logging.critical("Error copying MBR to device (%s)" % retcode)
        except OSError, error:
            logging.critical("Execution failed:", error)


def register_tmpfile(path):
    """TODO
    """

    tmpfiles.add(path)


def unregister_tmpfile(path):
    """TODO
    """

    if path in tmpfiles:
        tmpfiles.remove(path)


def register_mountpoint(target):
    """TODO
    """

    mounted.add(target)


def unregister_mountpoint(target):
    """TODO
    """

    if target in mounted:
        mounted.remove(target)


def mount(source, target, options):
    """Mount specified source on given target

    @source: name of device/ISO that should be mounted
    @target: directory where the ISO should be mounted to
    @options: mount specific options"""

#   notice: dry_run does not work here, as we have to locate files, identify flavour,...
    logging.debug("mount %s %s %s" % (options, source, target))
    proc = subprocess.Popen(["mount"] + list(options) + [source, target])
    proc.wait()
    if proc.returncode != 0:
        raise Exception, "Error executing mount"
    else:
        logging.debug("register_mountpoint(%s)" % target)
        register_mountpoint(target)

def unmount(target, options):
    """Unmount specified target

    @target: target where something is mounted on and which should be unmounted
    @options: options for umount command"""

    # make sure we unmount only already mounted targets
    target_unmount = False
    mounts = open('/proc/mounts').readlines()
    mountstring = re.compile(".*%s.*" % re.escape(target))
    for line in mounts:
        if re.match(mountstring, line):
            target_unmount = True

    if not target_unmount:
        logging.debug("%s not mounted anymore" % target)
    else:
        logging.debug("umount %s %s" % (list(options), target))
        proc = subprocess.Popen(["umount"] + list(options) + [target])
        proc.wait()
        if proc.returncode != 0:
            raise Exception, "Error executing umount"
        else:
            logging.debug("unregister_mountpoint(%s)" % target)
            unregister_mountpoint(target)


def check_for_usbdevice(device):
    """Check whether the specified device is a removable USB device

    @device: device name, like /dev/sda1 or /dev/sda
    """

    usbdevice = re.match(r'/dev/(.*?)\d*$', device).group(1)
    usbdevice = os.path.realpath('/sys/class/block/' + usbdevice + '/removable')
    if os.path.isfile(usbdevice):
        is_usb = open(usbdevice).readline()
        if is_usb == "1":
            return 0
        else:
            return 1


def check_for_fat(partition):
    """Check whether specified partition is a valid VFAT/FAT16 filesystem

    @partition: device name of partition"""

    try:
        udev_info = subprocess.Popen(["/lib/udev/vol_id", "-t", partition],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        filesystem = udev_info.communicate()[0].rstrip()

        if udev_info.returncode == 2:
            raise Exception, "Failed to read device %s - wrong UID / permissions?" % partition

        if filesystem != "vfat":
            raise Exception, "Device %s does not contain a FAT16 partition" % partition

    except OSError:
        raise Exception, "Sorry, /lib/udev/vol_id not available."


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

    if not options.bootloaderonly:
	    logging.info("Copying files. This might take a while....")

	    squashfs = search_file(grml_flavour + '.squashfs', iso_mount)
	    squashfs_target = target + '/live/'
	    execute(mkdir, squashfs_target)

	    # use install(1) for now to make sure we can write the files afterwards as normal user as well
	    logging.debug("cp %s %s" % (squashfs, target + '/live/' + grml_flavour + '.squashfs'))
	    proc = execute(subprocess.Popen, ["install", "--mode=664", squashfs, squashfs_target + grml_flavour + ".squashfs"])
	    proc.wait()

	    filesystem_module = search_file('filesystem.module', iso_mount)
	    logging.debug("cp %s %s" % (filesystem_module, squashfs_target + grml_flavour + '.module'))
	    proc = execute(subprocess.Popen, ["install", "--mode=664", filesystem_module, squashfs_target + grml_flavour + '.module'])
	    proc.wait()

	    release_target = target + '/boot/release/' + grml_flavour
	    execute(mkdir, release_target)

	    kernel = search_file('linux26', iso_mount)
	    logging.debug("cp %s %s" % (kernel, release_target + '/linux26'))
	    proc = execute(subprocess.Popen, ["install", "--mode=664", kernel, release_target + '/linux26'])
	    proc.wait()

	    initrd = search_file('initrd.gz', iso_mount)
	    logging.debug("cp %s %s" % (initrd, release_target + '/initrd.gz'))
	    proc = execute(subprocess.Popen, ["install", "--mode=664", initrd, release_target + '/initrd.gz'])
	    proc.wait()

    if not options.copyonly:
        syslinux_target = target + '/boot/syslinux/'
        execute(mkdir, syslinux_target)

        logo = search_file('logo.16', iso_mount)
        logging.debug("cp %s %s" % (logo, syslinux_target + 'logo.16'))
        proc = execute(subprocess.Popen, ["install", "--mode=664", logo, syslinux_target + 'logo.16'])
        proc.wait()

        for ffile in 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10':
            bootsplash = search_file(ffile, iso_mount)
            logging.debug("cp %s %s" % (bootsplash, syslinux_target + ffile))
            proc = execute(subprocess.Popen, ["install", "--mode=664", bootsplash, syslinux_target + ffile])
            proc.wait()

        grub_target = target + '/boot/grub/'
        execute(mkdir, grub_target)

        logging.debug("cp /grml/git/grml2usb/grub/splash.xpm.gz %s" % grub_target + 'splash.xpm.gz') # FIXME - path of grub
        proc = execute(subprocess.Popen, ["install", "--mode=664", '/grml/git/grml2usb/grub/splash.xpm.gz', grub_target + 'splash.xpm.gz']) # FIXME
        proc.wait()

        logging.debug("cp /grml/git/grml2usb/grub/stage2_eltorito to %s" % grub_target + 'stage2_eltorito') # FIXME - path of grub
        proc = execute(subprocess.Popen, ["install", "--mode=664", '/grml/git/grml2usb/grub/stage2_eltorito', grub_target + 'stage2_eltorito']) # FIXME
        proc.wait()

        if not dry_run:
            logging.debug("Generating grub configuration")
            #with open("...", "w") as f:
            #f.write("bla bla bal")
            grub_config_file = open(grub_target + 'menu.lst', 'w')
            grub_config_file.write(generate_grub_config(grml_flavour))
            grub_config_file.close()

            logging.info("Generating syslinux configuration")
            syslinux_cfg = syslinux_target + 'syslinux.cfg'

            # install main configuration only *once*, no matter how many ISOs we have:
            if os.path.isfile(syslinux_cfg):
                string = open(syslinux_cfg).readline()
                main_identifier = re.compile(".*main config generated at: %s.*" % re.escape(str(datestamp)))
                if not re.match(main_identifier, string):
                    syslinux_config_file = open(syslinux_cfg, 'w')
                    logging.info("Notice: grml flavour %s is being installed as the default booting system." % grml_flavour)
                    syslinux_config_file.write(generate_main_syslinux_config(grml_flavour, options.bootoptions))
                    syslinux_config_file.close()
            else:
                    syslinux_config_file = open(syslinux_cfg, 'w')
                    syslinux_config_file.write(generate_main_syslinux_config(grml_flavour, options.bootoptions))
                    syslinux_config_file.close()


            # install flavour specific configuration only *once* as well
            # ugly - I'm pretty sure this could be smoother...
            flavour_config = True
            if os.path.isfile(syslinux_cfg):
                string = open(syslinux_cfg).readlines()
                logging.info("Notice: you can boot flavour %s using '%s' on the commandline." % (grml_flavour, grml_flavour))
                flavour = re.compile("grml2usb for %s: %s" % (re.escape(grml_flavour), re.escape(str(datestamp))))
                for line in string:
                    if flavour.match(line):
                        flavour_config = False


            if flavour_config:
                syslinux_config_file = open(syslinux_cfg, 'a')
                syslinux_config_file.write(generate_flavour_specific_syslinux_config(grml_flavour, options.bootoptions))
                syslinux_config_file.close( )

            logging.debug("Generating isolinux/syslinux splash %s" % syslinux_target + 'boot.msg')
            isolinux_splash = open(syslinux_target + 'boot.msg', 'w')
            isolinux_splash.write(generate_isolinux_splash(grml_flavour))
            isolinux_splash.close( )


    # make sure we sync filesystems before returning
    proc = subprocess.Popen(["sync"])
    proc.wait()

def uninstall_files(device):
    """Get rid of all grml files on specified device"""

    # TODO
    logging.critical("TODO: %s" % device)


def identify_grml_flavour(mountpath):
    """Get name of grml flavour

    @mountpath: path where the grml ISO is mounted to
    @return: name of grml-flavour"""

    version_file = search_file('grml-version', mountpath)

    if version_file == "":
        logging.critical("Error: could not find grml-version file.")
        raise

    try:
        tmpfile = open(version_file, 'r')
        grml_info = tmpfile.readline()
        grml_flavour = re.match(r'[\w-]*', grml_info).group()
    except TypeError:
        raise
    except:
        logging.critical("Unexpected error:", sys.exc_info()[0])
        raise

    return grml_flavour

def handle_iso(iso, device):
    """TODO
    """

    logging.info("Using ISO %s" % iso)

    if os.path.isdir(iso):
        logging.critical("TODO: /live/image handling not yet implemented") # TODO
    else:
        iso_mountpoint = tempfile.mkdtemp()
        register_tmpfile(iso_mountpoint)
        remove_iso_mountpoint = True

        mount(iso, iso_mountpoint, ["-o", "loop", "-t", "iso9660"])

        if os.path.isdir(device):
            logging.info("Specified target is a directory, not mounting therefore.")
            device_mountpoint = device
            remove_device_mountpoint = False
            skip_mbr = True

        else:
            device_mountpoint = tempfile.mkdtemp()
            register_tmpfile(device_mountpoint)
            remove_device_mountpoint = True
            try:
                mount(device, device_mountpoint, "")
            except Exception, error:
                logging.critical("Fatal: %s" % error)
                cleanup()

        try:
            grml_flavour = identify_grml_flavour(iso_mountpoint)
            logging.info("Identified grml flavour \"%s\"." % grml_flavour)
            copy_grml_files(grml_flavour, iso_mountpoint, device_mountpoint, dry_run=options.dryrun)
        except TypeError:
            logging.critical("Fatal: a critical error happend during execution, giving up")
            sys.exit(1)
        finally:
            if os.path.isdir(iso_mountpoint) and remove_iso_mountpoint:
                unmount(iso_mountpoint, "")

                os.rmdir(iso_mountpoint)
                unregister_tmpfile(iso_mountpoint)

            if remove_device_mountpoint:
                unmount(device_mountpoint, "")

                if os.path.isdir(device_mountpoint):
                    os.rmdir(device_mountpoint)
                    unregister_tmpfile(device_mountpoint)

        # grml_flavour_short = grml_flavour.replace('-','')
        # logging.debug("grml_flavour_short = %s" % grml_flavour_short)


def main():
    """Main function [make pylint happy :)]"""

    if options.version:
        print os.path.basename(sys.argv[0]) + " " + PROG_VERSION
        sys.exit(0)

    if len(args) < 2:
        parser.error("invalid usage")

    # log handling
    if options.verbose:
        FORMAT = "%(asctime)-15s %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    elif options.quiet:
        FORMAT = "Critial: %(message)s"
        logging.basicConfig(level=logging.CRITICAL, format=FORMAT)
    else:
        FORMAT = "Info: %(message)s"
        logging.basicConfig(level=logging.INFO, format=FORMAT)

    if options.dryrun:
        logging.info("Running in simulate mode as requested via option dry-run.")
    else:
        check_uid_root()

    # specified arguments
    device = args[len(args) - 1]
    isos = args[0:len(args) - 1]

    # make sure we can replace old grml2usb script and warn user when using old way of life:
    if device.startswith("/mnt/external") or device.startswith("/mnt/usb"):
        print "Warning: the semantics of grml2usb has changed."
        print "Instead of using grml2usb /path/to/iso %s you might" % device
        print "want to use grml2usb /path/to/iso /dev/... instead."
        print "Please check out the grml2usb manpage for details."
        f = raw_input("Do you really want to continue? y/N ")
        if f == "y" or f == "Y":
           pass
        else:
            sys.exit(1)

    # make sure we have syslinux available
    if not which("syslinux") and not options.copyonly:
        logging.critical('Sorry, syslinux not available. Exiting.')
        logging.critical('Please install syslinux or consider using the --grub option.')
        sys.exit(1)

    # check for vfat filesystem
    if device is not None and not os.path.isdir(device):
        try:
            check_for_fat(device)
        except Exception, error:
            logging.critical("Execution failed: %s", error)
            sys.exit(1)

    if not check_for_usbdevice(device):
        print "Warning: the specified device %s does not look like a removable usb device." % device
        f = raw_input("Do you really want to continue? y/N ")
        if f == "y" or f == "Y":
           pass
        else:
            sys.exit(1)

    # main operation (like installing files)
    for iso in isos:
        handle_iso(iso, device)

    # install MBR
    if not options.mbr or skip_mbr:
        logging.info("You are not using the --mbr option. Consider using it to get a working USB setup.")
    else:
        # make sure we install MBR on /dev/sdX and not /dev/sdX#
        if device[-1:].isdigit():
            mbr_device = re.match(r'(.*?)\d*$', device).group(1)

        try:
            install_mbr(mbr_device, dry_run=options.dryrun)
        except IOError, error:
            logging.critical("Execution failed: %s", error)
            sys.exit(1)
        except Exception, error:
            logging.critical("Execution failed: %s", error)
            sys.exit(1)

    # Install bootloader only if not using the --copy-only option
    if options.copyonly:
        logging.info("Not installing bootloader and its files as requested via option copyonly.")
    else:
        install_bootloader(device, dry_run=options.dryrun)

    # finally be politely :)
    logging.info("Finished execution of grml2usb (%s). Have fun with your grml system." % PROG_VERSION)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Received KeyboardInterrupt")
        cleanup()

## END OF FILE #################################################################
# vim:foldmethod=marker expandtab ai ft=python tw=120 fileencoding=utf-8
