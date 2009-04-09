#!/bin/sh
# Filename:      tarball.sh
# Purpose:       generate tarball for using grml2usb on non-Debian systems
# Authors:       grml-team (grml.org), (c) Michael Prokop <mika@grml.org>
# Bug-Reports:   see http://grml.org/bugs/
# License:       This file is licensed under the GPL v2 or any later version.
################################################################################

set -e

VERSION="$(awk '/^PROG_VERSION/ { print $3}' grml2usb | tr -d \")"

DIR="grml2usb-${VERSION}"
[ -d "$DIR" ] || mkdir "$DIR"

cat > "${DIR}"/README << EOF
README
------

grml2usb installs grml ISO(s) on usb device for booting.

This tarball provides all the necessary files for running grml2usb.
Execute the script install.sh with root permissions to install the
files provided by the tarball in the filesystem.

Updating is possible via downloading the most recent tarball and
executing install.sh again.

If you want to remove grml2usb from your system just execute
the provided uninstall.sh script with root permissions.

Note:

If you are using Debian (or a Debian based system like grml, Ubuntu,...)
consider using the provided grml2usb Debian package:
http://deb.grml.org/ => http://deb.grml.org/pool/main/g/grml2usb/

Please report bugs and feedback to Michael Prokop <mika@grml.org>.
EOF

cat > "${DIR}"/install.sh << EOF
#!/bin/sh

set -e

if [ "\$UID" != 0 ] ; then
   echo "Error: become root before starting $0" >& 2
   exit 1
fi

BASE="\$(dirname \$0)"

printf "Installing files:\n"

printf "  - /usr/sbin/grml2usb\n"
install -m 755 \${BASE}/grml2usb /usr/sbin/grml2usb

[ -d /usr/share/grml2usb/grub ] || mkdir -p /usr/share/grml2usb/grub
printf "  - /usr/share/grml2usb/grub/splash.xpm.gz\n"
install -m 644 \${BASE}/splash.xpm.gz /usr/share/grml2usb/grub/splash.xpm.gz
printf "  - /usr/share/grml2usb/grub/grml.png\n"
install -m 644 \${BASE}/grml.png      /usr/share/grml2usb/grub/grml.png

[ -d /usr/share/grml2usb/lilo ] || mkdir -p /usr/share/grml2usb/lilo
printf "  - /usr/share/grml2usb/lilo/lilo.static.amd64\n"
install -m 755 \${BASE}/lilo.static.amd64 /usr/share/grml2usb/lilo/lilo.static.amd64
printf "  - /usr/share/grml2usb/lilo/lilo.static.i386\n"
install -m 755 \${BASE}/lilo.static.i386  /usr/share/grml2usb/lilo/lilo.static.i386

[ -d /usr/share/grml2usb/mbr ] || mkdir -p /usr/share/grml2usb/mbr
printf "  - /usr/share/grml2usb/mbr/mbrmgr\n"
install -m 644 \${BASE}/mbrmgr /usr/share/grml2usb/mbr/mbrmgr
printf "  - /usr/share/grml2usb/mbr/mbrldr\n"
install -m 644 \${BASE}/mbrldr /usr/share/grml2usb/mbr/mbrldr

[ -d /usr/share/man/man8/ ] || mkdir -p /usr/share/man/man8
printf "  - /usr/share/man/man8/grml2usb.8.gz\n"
install -m 644 \${BASE}/grml2usb.8.gz /usr/share/man/man8/grml2usb.8.gz

printf "Finished installation.\n"
EOF

chmod 755 "${DIR}"/install.sh

cat > "${DIR}"/uninstall.sh << EOF
#!/bin/sh

set -e

if [ "\$UID" != 0 ] ; then
   echo "Error: become root before starting $0" >& 2
   exit 1
fi

for file in \\
  /usr/sbin/grml2usb \\
  /usr/share/grml2usb/grub/splash.xpm.gz \\
  /usr/share/grml2usb/grub/grml.png \\
  /usr/share/grml2usb/lilo/lilo.static.amd64 \\
  /usr/share/grml2usb/lilo/lilo.static.i386 \\
  /usr/share/grml2usb/mbr/mbrmgr \\
  /usr/share/grml2usb/mbr/mbrldr \\
  /usr/share/man/man8/grml2usb.8.gz \\
; do
  printf "Removing \$file: "
  rm -f \$file && printf "done\n" || printf "failed\n"
done
EOF

chmod 755 "${DIR}"/uninstall.sh

fakeroot debian/rules build

# manpage
cp grml2usb.8.txt grml2usb-0.9.5/
gzip -9 --to-stdout grml2usb-0.9.5/grml2usb.8.txt > grml2usb-0.9.5/grml2usb.8.gz
rm grml2usb-0.9.5/grml2usb.8.txt

# binaries, grub, lilo
cp grml2usb mbr/mbrldr mbr/mbrmgr grub/* lilo/lilo.static.* grml2usb-0.9.5/

tar zcf grml2usb.tgz "${DIR}"

rm -rf "${DIR}"
md5sum grml2usb.tgz > grml2usb.tgz.md5
gpg --clearsign grml2usb.tgz.md5
rm grml2usb.tgz.md5
echo "Generated grml2usb.tgz and grml2usb.tgz.md5.asc of grml2usb $VERSION"

## END OF FILE #################################################################
