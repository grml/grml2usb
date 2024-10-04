; $MirOS: src/sys/arch/i386/stand/mbr/mbr.S,v 1.13 2009/03/04 10:50:28 tg Exp $
; Ported to nasm syntax 2024-10-04 by ch@grml.org

; Copyright (c) 2009
;	Thorsten Glaser <tg@mirbsd.org>
;
; Provided that these terms and disclaimer and all copyright notices
; are retained or reproduced in an accompanying document, permission
; is granted to deal in this work without restriction, including un-
; limited rights to use, publicly perform, distribute, sell, modify,
; merge, give away, or sublicence.
;
; This work is provided "AS IS" and WITHOUT WARRANTY of any kind, to
; the utmost extent permitted by applicable law, neither express nor
; implied; without malicious intent or gross negligence. In no event
; may a licensor, author or contributor be held liable for indirect,
; direct, other damage, loss, or other issues arising in any way out
; of dealing in the work, even if advised of the possibility of such
; damage or existence of a defect, except proven that it results out
; of said person's immediate fault when using the work as intended.
;-
; Assemble commands:
;	$ nasm -D__BOOT_VER=\"0AA6\" -DBOOTMANAGER mbr.S -o mbrmgr
;	$ nasm -D__BOOT_VER=\"0AA6\" -DBOOT_QUIET mbr.S -o mbrldr

bits 16
section .text
org 600h
cpu 386

global _start
_start:	xor	eax,eax
	mov	ss,ax
	mov	sp,Lstack
	push	eax
	popfd
	mov	ds,ax
	mov	es,ax
	mov	si,Lbadr
	mov	di,_start
	mov	cx,0x0200	; size of one sector
	push	si		; load / return address
	push	ax
	push	Lmain
	rep	movsb
	retf

	; entry message
Lemsg:	db	"Mir-"
	db	__BOOT_VER
%if %isdef(BOOTMANAGER)
	; Lem<nn> are patch points
	db	": 0="
Lem00:	db	"00 1="
Lem01:	db	"00 2="
Lem02:	db	"00 3="
Lem03:	db	"00 4=hd0 5=fd0  Enter=default (timeout)", 0x0d, 0x0a
%endif
	db	">", 0

	; failure message
Lfmsg:	db	"bad magic", 0x0d, 0x0a, 0

%if 1
	; okay boot message
Lbmsg:	db	" OK", 0x0d, 0
%endif

	; output NUL-terminated string from ds:si
Lotxt0:	mov	ah,0x0E
	mov	bx,7
	int	0x10
Lotxt:	lodsb
	or	al,al
	jnz	Lotxt0
	ret

Lmain:	sti
%if %isdef(BOOTMANAGER)
	; patch the partition type values into the message
	mov	di, Lem00
	mov	al,[Lptab + 0x04]
	call	LpBY
	mov	di, Lem01
	mov	al,[Lptab + 0x14]
	call	LpBY
	mov	di, Lem02
	mov	al,[Lptab + 0x24]
	call	LpBY
	mov	di, Lem03
	mov	al,[Lptab + 0x34]
	call	LpBY
%endif
%if !%isdef(BOOT_QUIET) || %isdef(BOOTMANAGER)
	;mov	si,offset Lemsg
	mov	si, Lemsg
	call	Lotxt
%endif

	; fake invalid partition entry for MBR/FDD boot
	mov	di, Lptab + 0x40
	xor	eax,eax
	stosw
	inc	ax
	stosw
	dec	ax
	stosd
	stosd

	; force bad magic if sector load fails
	mov	[Lbmag],al

%if %isdef(BOOTMANAGER)
%if 0 ; see above, eax is already zero here
	xor	ax,ax		; read CMOS clock ticks since midnight
%endif
	int	0x1A		; 32-bit result in cx:dx
	mov	di,cx		; save it in edi for later
	shl	edi,16
	mov	di,dx
	add	edi,183		; 10 seconds, rounded up one tick
	Lptmo equ $ - 4		; offset of the "183" above

	; input loop with timeout
Lwkey:	mov	ah,1
	int	0x16		; check if a key was pressed
	jnz	Lgkey		; yeap
	; delay loop
	xor	ax,ax
	int	0x1A
	shl	ecx,16
	mov	cx,dx
	or	al,al		; past midnight?
	jz	Lsday		; no
	add	ecx,1573040	; should be 1572480, but according to RBIL…
Lsday:	cmp	ecx,edi		; time is over?
	mov	al,13
	ja	Lfkey		; yep, fake a return keypress
	jmp	Lwkey

	; input loop without timeout
Lgkey:	mov	ah,1
	int	0x16		; check if a key was pressed
	jz	Lgkey
	mov	ah,0
	int	0x16
%endif ; BOOTMANAGER
Lfkey:	mov	bx, Lptab
	mov	dl,0x80		; drive to load from
%if !%isdef(BOOTMANAGER)
	jmp	Lscan
%else
	sub	al,13
	je	Lscan		; CR / Return / Enter
	jb	Lgkey		; invalid input
	sub	al,('0' - 13)
	jb	Lgkey		; invalid input
	cmp	al,5		; floppy
	ja	Lgkey		; invalid input
	jb	LdoHD		; hard disc
	mov	dl,0		; drive to load from
	dec	ax		; 5 -> 4
%endif
LdoHD:	shl	al,4		; 0..4 where 4 is virtual partition
	add	bl,al		; we boot this one
	jmp	Lboot

	; scan the partition table for an active partition
Lscan:	mov	al,[dpart]	; try hard-coded by fdisk(8) 'fdef' first
	cmp	al,3
	jbe	LdoHD
Lspar:	cmp	byte [bx],0x80
	je	Lboot		; found an active partition
	add	bl,0x10
	cmp	bl,0xFE		; BX = 0x07FE = Lptab + 0x40
	jb	Lspar
	; boot the virtual partition #4 (MBR)

Lboot:	; try to boot, first LBA (we're on a HDD) then CHS
	mov	[bx],dl		; drive (0x80 or 0x00)
	mov	si, Lpblk	; LBA parameter block
	mov	di,si
	mov	ax,0x0010
	stosw			; size of LBA parameter block
	mov	al,1
	stosw			; number of sectors to load
	pop	ax
	push	ax
	push	bx
	stosw			; load address offset
	xor	ax,ax
	stosw			; load address segment
	mov	eax,[bx+8]
	stosd			; LBA offset of start sector (low 32 bit)
	xor	ax,ax
	stosw			; high 32 bit
	stosw			; high 32 bit
	mov	ah,0x42		; LBA extended read
	call	Lload		; try to boot that
	pop	si		; edited partition table entry
	pop	bx		; load offset (ES=CS=SS=DS=0000h)
	push	bx
	push	si
	mov	ax,0x0201	; CHS read 0x01 sectors
	mov	cx,[si+2]	; cylinder; sector number
	mov	dx,[si]		; head; drive number
	call	Lload
	mov	si, Lfmsg
	call	Lotxt
%if 0
Lfail:	jmp	Lfail
%else
	xor	ax,ax
	int	0x16
	jmp	0xF000:0xFFF0
%endif

Lload:	mov	bp,4		; number of tries
Lldlp:	pusha
	int	0x13
	popa
	jc	Lldre		; error, try again
	cmp	word [Lbmag],0xAA55
	jne	Lldre		; bad magic, try again
%if 0
	mov	ax,0x0E0D	; output a carriage return
	xor	bx,bx
	int	0x10
%else
	mov	si, Lbmsg
	call	Lotxt
%endif
	pop	si		; Lload return address
	pop	si		; partition table entry
	mov	dl,[si]
	; DS:SI point to partition table entry, DL is set
	cli			; be nice :)
	ret			; jump to 0000:7C00h
Lldre:	pusha
	xor	ax,ax		; reset drive
	int	0x13
	popa
	dec	bp		; another try left?
	jnz	Lldlp
	ret

%if %isdef(BOOTMANAGER)
LpBY:	mov	ah,al
	shr	al,4
	and	ah,0x0F
	add	ax,0x3030
	cmp	al,0x39
	jbe	LpBY1
	add	al,7
LpBY1:	cmp	ah,0x39
	jbe	LpBY2
	add	ah,7
LpBY2:	stosw
	ret
%endif

times 0x01b7 - ($-$$) db 0
;	. = _start + 0x01B7
dpart:	db  0xFF		; default partition [0..3] or none

Lntid:	dd  0		; Microsoft® NT® volume identifier
Lpad1:	dw  0

;	. = _start + 0x01BE
	; partition table
Lptab:	dd	0, 0, 0, 0	; partition entry #0
	dd	0, 0, 0, 0	; partition entry #1
	dd	0, 0, 0, 0	; partition entry #2
	; partition entry #3 + pre-installation hint
	dw	0, 0, 0, 0, 0
;	. = _start + 0x01F8
;	.size	Lhint,2
%if %isdef(BOOTMANAGER)
Lhint:	dw	(Lptmo - _start)
%else
Lhint:	dw	0xFFFF
%endif
Lpad2:	dw	0, 0

;	. = _start + 0x01FE
times 510-($-$$) db 0
Lpmag:	dw	0xAA55		; BIOS boot magic

	Lstack equ 0x4000
	Lpblk equ 0x5000

	Lbadr equ 0x7C00
	Lbmag equ Lbadr + 0x01FE

