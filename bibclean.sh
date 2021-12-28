# Download bibtex-tidy from https://github.com/FlamingTempura/bibtex-tidy
# Check bibtex-tidy is above v1.8.5 with ./bibtex-tidy-master/bin/bibtex-tidy --version
./bibtex-tidy-master/bin/bibtex-tidy --sort=type,-year,author,key --no-escape --align=13 --curly --tab --duplicates=citation --sort-fields=title,subtitle,author,year,journal,fjournal,booktitle,booksubtitle,publisher,address,series,volume,number,pages,editor,edition,note,url,doi --no-remove-dupe-fields DirectionalStats.bib
