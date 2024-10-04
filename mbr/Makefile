# https://www.mirbsd.org/cvs.cgi/~checkout~/src/sys/arch/i386/stand/mbr/mbr.S

all: mbrmgr mbrldr

clean:
	rm -f mbrmgr mbrldr

mbrmgr:
	nasm -D__BOOT_VER=\"0AA6\" -DBOOTMANAGER mbr.S -o mbrmgr

# bootloader, without a bootmenu
mbrldr:
	$ nasm -D__BOOT_VER=\"0AA6\" -DBOOT_QUIET mbr.S -o mbrldr
