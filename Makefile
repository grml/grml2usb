all: codecheck doc

doc: doc_man doc_html

doc_html: html-stamp

html-stamp: grml2usb.8.adoc grml2iso.8.adoc
	asciidoc -b xhtml11 -a icons -a toc -a numbered grml2usb.8.adoc
	asciidoc -b xhtml11 -a icons -a toc -a numbered grml2iso.8.adoc
	touch html-stamp

doc_man: man-stamp

man-stamp: grml2usb.8.adoc grml2iso.8.adoc
	# grml2usb:
	asciidoc -d manpage -b docbook grml2usb.8.adoc
	xsltproc --novalid --nonet /usr/share/xml/docbook/stylesheet/nwalsh/manpages/docbook.xsl grml2usb.8.xml
	# grml2iso:
	asciidoc -d manpage -b docbook grml2iso.8.adoc
	xsltproc --novalid --nonet /usr/share/xml/docbook/stylesheet/nwalsh/manpages/docbook.xsl grml2iso.8.xml
	# we're done
	touch man-stamp

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
	ruff check grml2usb
	ruff format --check grml2usb
	vulture grml2usb test/grml2usb_test.py

test:
	pytest

# graph:
#	sudo pycallgraph grml2usb /grml/isos/grml-small_2008.11.iso /dev/sdb1
