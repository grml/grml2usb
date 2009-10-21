all: doc

doc: doc_man doc_html

doc_html: html-stamp

html-stamp: grml2usb-compat.8.txt grml2iso-compat.8.txt
	asciidoc -b xhtml11 -a icons -a toc -a numbered grml2usb-compat.8.txt
	asciidoc -b xhtml11 -a icons -a toc -a numbered grml2iso-compat.8.txt
	touch html-stamp

doc_man: man-stamp

man-stamp: grml2usb-compat.8.txt grml2iso-compat.8.txt
	# grml2usb-compat:
	asciidoc -d manpage -b docbook grml2usb-compat.8.txt
	sed -i 's/<emphasis role="strong">/<emphasis role="bold">/' grml2usb-compat.8.xml
	xsltproc /usr/share/xml/docbook/stylesheet/nwalsh/manpages/docbook.xsl grml2usb-compat.8.xml
	# ugly hack to avoid duplicate empty lines in manpage
	# notice: docbook-xsl 1.71.0.dfsg.1-1 is broken! make sure you use 1.68.1.dfsg.1-0.2!
	cp grml2usb-compat.8 grml2usb-compat.8.tmp
	uniq grml2usb-compat.8.tmp > grml2usb-compat.8
	# ugly hack to avoid '.sp' at the end of a sentence or paragraph:
	sed -i 's/\.sp//' grml2usb-compat.8
	rm grml2usb-compat.8.tmp
	# grml2iso-compat:
	asciidoc -d manpage -b docbook grml2iso-compat.8.txt
	sed -i 's/<emphasis role="strong">/<emphasis role="bold">/' grml2iso-compat.8.xml
	xsltproc /usr/share/xml/docbook/stylesheet/nwalsh/manpages/docbook.xsl grml2iso-compat.8.xml
	# ugly hack to avoid duplicate empty lines in manpage
	# notice: docbook-xsl 1.71.0.dfsg.1-1 is broken! make sure you use 1.68.1.dfsg.1-0.2!
	cp grml2iso-compat.8 grml2iso-compat.8.tmp
	uniq grml2iso-compat.8.tmp > grml2iso-compat.8
	# ugly hack to avoid '.sp' at the end of a sentence or paragraph:
	sed -i 's/\.sp//' grml2iso-compat.8
	rm grml2iso-compat.8.tmp
	# we're done
	touch man-stamp

online: all
	scp grml2usb-compat.8.html  grml:/var/www/grml/grml2usb-compat/index.html
	scp images/icons/*          grml:/var/www/grml/grml2usb-compat/images/icons/
	scp images/screenshot.png   grml:/var/www/grml/grml2usb-compat/images/

tarball: all
	./tarball.sh

tarball-online: tarball
	scp grml2usb-compat.tgz grml2usb-compat.tgz.md5.asc grml:/var/www/grml/grml2usb/

clean:
	rm -rf grml2usb-compat.8.html grml2usb-compat.8.xml grml2usb-compat.8
	rm -rf grml2iso-compat.8.html grml2iso-compat.8.xml grml2iso-compat.8
	rm -rf html-stamp man-stamp grml2usb-compat.tar.gz grml2usb-compat.tgz grml2usb-compat.tgz.md5.asc

codecheck:
	pylint --include-ids=y --max-line-length=120 grml2usb-compat
	# pylint --include-ids=y --disable-msg-cat=C0301 --disable-msg-cat=W0511 grml2usb-compat
	# pylint --reports=n --include-ids=y --disable-msg-cat=C0301 grml2usb-compat

# graph:
#	sudo pycallgraph grml2usb-compat /grml/isos/grml-small_2008.11.iso /dev/sdb1
