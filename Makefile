all: codecheck doc

doc: doc_man doc_html

doc_html: html-stamp

html-stamp: grml2usb.8.txt grml2iso.8.txt
	asciidoc -b xhtml11 -a icons -a toc -a numbered grml2usb.8.txt
	asciidoc -b xhtml11 -a icons -a toc -a numbered grml2iso.8.txt
	touch html-stamp

doc_man: man-stamp

man-stamp: grml2usb.8.txt grml2iso.8.txt
	# grml2usb:
	asciidoc -d manpage -b docbook grml2usb.8.txt
	xsltproc --novalid --nonet /usr/share/xml/docbook/stylesheet/nwalsh/manpages/docbook.xsl grml2usb.8.xml
	# grml2iso:
	asciidoc -d manpage -b docbook grml2iso.8.txt
	xsltproc --novalid --nonet /usr/share/xml/docbook/stylesheet/nwalsh/manpages/docbook.xsl grml2iso.8.xml
	# we're done
	touch man-stamp

online: all
	scp grml2usb.8.html grml:/var/www/grml/grml2usb/index.html
	scp images/icons/*          grml:/var/www/grml/grml2usb/images/icons/
	scp images/screenshot.png   grml:/var/www/grml/grml2usb/images/

tarball: all
	./tarball.sh

prepare-release:
	./tarball.sh --no-gpg

clean:
	$(MAKE) -C mbr clean
	rm -rf grml2usb.8.html grml2usb.8.xml grml2usb.8
	rm -rf grml2iso.8.html grml2iso.8.xml grml2iso.8
	rm -rf html-stamp man-stamp grml2usb.tar.gz grml2usb.tgz grml2usb.tgz.md5.asc

codecheck:
	flake8 grml2usb
	isort --check-only grml2usb
	black --check grml2usb
	vulture grml2usb test/grml2usb_test.py

test:
	pytest

# graph:
#	sudo pycallgraph grml2usb /grml/isos/grml-small_2008.11.iso /dev/sdb1
