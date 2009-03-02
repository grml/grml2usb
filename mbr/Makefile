all: mbrmgr mbrldr

clean:
	rm -f mbrmgr mbrldr mbrmgr.elf mbr.o

mbrmgr:
	gcc -D_ASM_SOURCE -DBOOTMANAGER -D__BOOT_VER=\"0AA6\" -c mbr.S
	ld -nostdlib -Ttext 0x0600 -N -Bstatic -e _start -o mbrmgr.elf mbr.o
	objcopy -O binary mbrmgr.elf mbrmgr

# bootloader, without a bootmenu
mbrldr:
	gcc -D_ASM_SOURCE -UBOOTMANAGER -D__BOOT_VER=\"0AA6\" -c mbr.S
	ld -nostdlib -Ttext 0x0600 -N -Bstatic -e _start -o mbrmgr.elf mbr.o
	objcopy -O binary mbrmgr.elf mbrldr
