#!/bin/sh
# Filename:      tarball.sh
# Purpose:       generate tarball for using grml2usb on non-Debian systems
# Authors:       grml-team (grml.org), (c) Michael Prokop <mika@grml.org>
# Bug-Reports:   see http://grml.org/bugs/
# License:       This file is licensed under the GPL v2 or any later version.
################################################################################

set -e

VERSION=$(dpkg-parsechangelog | awk '/Version: / { print $2 }')
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

if [ \$(id -u) != 0 ] ; then
   echo "Error: become root before starting \$0" >& 2
   exit 1
fi

BASE="\$(dirname \$0)"

printf "Installing files:\n"

printf "  - /usr/sbin/grml2usb\n"
install -m 755 \${BASE}/grml2usb /usr/sbin/grml2usb

printf "  - /usr/sbin/grml2iso\n"
install -m 755 \${BASE}/grml2iso /usr/sbin/grml2iso

[ -d /usr/share/grml2usb/grub ] || mkdir -p /usr/share/grml2usb/grub
printf "  - /usr/share/grml2usb/grub/splash.xpm.gz\n"
install -m 644 \${BASE}/splash.xpm.gz /usr/share/grml2usb/grub/splash.xpm.gz
printf "  - /usr/share/grml2usb/grub/grml.png\n"
install -m 644 \${BASE}/grml.png      /usr/share/grml2usb/grub/grml.png

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

if [ \$(id -u) != 0 ] ; then
   echo "Error: become root before starting \$0" >& 2
   exit 1
fi

for file in \\
  /usr/sbin/grml2usb \\
  /usr/sbin/grml2iso \\
  /usr/share/grml2usb/grub/splash.xpm.gz \\
  /usr/share/grml2usb/grub/grml.png \\
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
cp grml2usb.8.txt grml2usb-$VERSION/
cp grml2iso.8.txt grml2usb-$VERSION/
gzip -9 --to-stdout grml2usb-$VERSION/grml2usb.8.txt > grml2usb-$VERSION/grml2usb.8.gz
gzip -9 --to-stdout grml2usb-$VERSION/grml2iso.8.txt > grml2usb-$VERSION/grml2iso.8.gz
rm grml2usb-$VERSION/grml2usb.8.txt
rm grml2usb-$VERSION/grml2iso.8.txt

# binaries, grub
cp grml2usb grml2iso mbr/mbrldr mbr/mbrmgr grub/* grml2usb-$VERSION/
sed -i -e "s/PROG_VERSION='\*\*\*UNRELEASED\*\*\*'/PROG_VERSION='${VERSION}'/" grml2usb-$VERSION/grml2usb

tar zcf grml2usb.tgz "${DIR}"

rm -rf "${DIR}"
md5sum grml2usb.tgz > grml2usb.tgz.md5
gpg --clearsign grml2usb.tgz.md5
rm grml2usb.tgz.md5
echo "Generated grml2usb.tgz and grml2usb.tgz.md5.asc of grml2usb $VERSION"

## END OF FILE #################################################################
