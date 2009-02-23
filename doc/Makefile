all: doc

doc: doc_man doc_html

doc_html: html-stamp

html-stamp: mbr.8.txt
	asciidoc -b xhtml11 -a icons mbr.8.txt
	touch html-stamp

doc_man: man-stamp

man-stamp: mbr.8.txt
	asciidoc -d manpage -b docbook mbr.8.txt
	sed -i 's/<emphasis role="strong">/<emphasis role="bold">/' mbr.8.xml
	xsltproc /usr/share/xml/docbook/stylesheet/nwalsh/manpages/docbook.xsl mbr.8.xml
	# ugly hack to avoid duplicate empty lines in manpage
	# notice: docbook-xsl 1.71.0.dfsg.1-1 is broken! make sure you use 1.68.1.dfsg.1-0.2!
	cp mbr.8 mbr.8.tmp
	uniq mbr.8.tmp > mbr.8
	# ugly hack to avoid '.sp' at the end of a sentence or paragraph:
	sed -i 's/\.sp//' mbr.8
	rm mbr.8.tmp
	touch man-stamp

#online: all
#	scp mbr.8.html grml:/var/www/grml/mbr/index.html
#	scp images/icons/*          grml:/var/www/grml/mbr/images/icons/
#	scp images/screenshot.png   grml:/var/www/grml/mbr/images/

clean:
	rm -rf mbr.8.html mbr.8.xml mbr.8 html-stamp man-stamp
