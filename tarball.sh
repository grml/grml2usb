#!/bin/sh
# Filename:      tarball.sh
# Purpose:       generate tarball for using grml2usb-compat on non-Debian systems
# Authors:       grml-team (grml.org), (c) Michael Prokop <mika@grml.org>
# Bug-Reports:   see http://grml.org/bugs/
# License:       This file is licensed under the GPL v2 or any later version.
################################################################################

set -e

VERSION="$(awk '/^PROG_VERSION/ { print $3}' grml2usb-compat | tr -d \" | sed 's/-.*//')"

DIR="grml2usb-compat-${VERSION}"
[ -d "$DIR" ] || mkdir "$DIR"

cat > "${DIR}"/README << EOF
README
------

grml2usb-compat installs grml ISO(s) on usb device for booting.

This tarball provides all the necessary files for running grml2usb-compat.
Execute the script install.sh with root permissions to install the
files provided by the tarball in the filesystem.

Updating is possible via downloading the most recent tarball and
executing install.sh again.

If you want to remove grml2usb-compat from your system just execute
the provided uninstall.sh script with root permissions.

Note:

If you are using Debian (or a Debian based system like grml, Ubuntu,...)
consider using the provided grml2usb-compat Debian package:
http://deb.grml.org/ => http://deb.grml.org/pool/main/g/grml2usb-compat/

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

printf "  - /usr/sbin/grml2usb-compat\n"
install -m 755 \${BASE}/grml2usb-compat /usr/sbin/grml2usb-compat

printf "  - /usr/sbin/grml2iso-compat\n"
install -m 755 \${BASE}/grml2iso-compat /usr/sbin/grml2iso-compat

[ -d /usr/share/grml2usb-compat/grub ] || mkdir -p /usr/share/grml2usb-compat/grub
printf "  - /usr/share/grml2usb-compat/grub/splash.xpm.gz\n"
install -m 644 \${BASE}/splash.xpm.gz /usr/share/grml2usb-compat/grub/splash.xpm.gz
printf "  - /usr/share/grml2usb-compat/grub/grml.png\n"
install -m 644 \${BASE}/grml.png      /usr/share/grml2usb-compat/grub/grml.png

[ -d /usr/share/grml2usb-compat/lilo ] || mkdir -p /usr/share/grml2usb-compat/lilo
printf "  - /usr/share/grml2usb-compat/lilo/lilo.static.amd64\n"
install -m 755 \${BASE}/lilo.static.amd64 /usr/share/grml2usb-compat/lilo/lilo.static.amd64
printf "  - /usr/share/grml2usb-compat/lilo/lilo.static.i386\n"
install -m 755 \${BASE}/lilo.static.i386  /usr/share/grml2usb-compat/lilo/lilo.static.i386

[ -d /usr/share/grml2usb-compat/mbr ] || mkdir -p /usr/share/grml2usb-compat/mbr
printf "  - /usr/share/grml2usb-compat/mbr/mbrmgr\n"
install -m 644 \${BASE}/mbrmgr /usr/share/grml2usb-compat/mbr/mbrmgr
printf "  - /usr/share/grml2usb-compat/mbr/mbrldr\n"
install -m 644 \${BASE}/mbrldr /usr/share/grml2usb-compat/mbr/mbrldr

[ -d /usr/share/man/man8/ ] || mkdir -p /usr/share/man/man8
printf "  - /usr/share/man/man8/grml2usb-compat.8.gz\n"
install -m 644 \${BASE}/grml2usb-compat.8.gz /usr/share/man/man8/grml2usb-compat.8.gz

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
  /usr/sbin/grml2usb-compat \\
  /usr/sbin/grml2iso-compat \\
  /usr/share/grml2usb-compat/grub/splash.xpm.gz \\
  /usr/share/grml2usb-compat/grub/grml.png \\
  /usr/share/grml2usb-compat/lilo/lilo.static.amd64 \\
  /usr/share/grml2usb-compat/lilo/lilo.static.i386 \\
  /usr/share/grml2usb-compat/mbr/mbrmgr \\
  /usr/share/grml2usb-compat/mbr/mbrldr \\
  /usr/share/man/man8/grml2usb-compat.8.gz \\
; do
  printf "Removing \$file: "
  rm -f \$file && printf "done\n" || printf "failed\n"
done
EOF

chmod 755 "${DIR}"/uninstall.sh

fakeroot debian/rules build

# manpage
cp grml2usb-compat.8.txt grml2usb-compat-$VERSION/
cp grml2iso-compat.8.txt grml2usb-compat-$VERSION/
gzip -9 --to-stdout grml2usb-compat-$VERSION/grml2usb-compat.8.txt > grml2usb-compat-$VERSION/grml2usb-compat.8.gz
gzip -9 --to-stdout grml2usb-compat-$VERSION/grml2iso-compat.8.txt > grml2usb-compat-$VERSION/grml2iso-compat.8.gz
rm grml2usb-compat-$VERSION/grml2usb-compat.8.txt
rm grml2usb-compat-$VERSION/grml2iso-compat.8.txt

# binaries, grub, lilo
cp grml2usb-compat grml2iso-compat mbr/mbrldr mbr/mbrmgr grub/* lilo/lilo.static.* grml2usb-compat-$VERSION/

tar zcf grml2usb-compat.tgz "${DIR}"

rm -rf "${DIR}"
md5sum grml2usb-compat.tgz > grml2usb-compat.tgz.md5
gpg --clearsign grml2usb-compat.tgz.md5
rm grml2usb-compat.tgz.md5
echo "Generated grml2usb-compat.tgz and grml2usb-compat.tgz.md5.asc of grml2usb-compat $VERSION"

## END OF FILE #################################################################
