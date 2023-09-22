
# diSimplex Citation Manager

A citation manager for the diSimplex projects which understands our NikolaBase citation system.

## Top level tools

- **capture** to capture raw RIS formatted citation from Zotero/BibItNow into
  our new style database.

- **scanner** to scan one or more (LaTeX) *.aux files for a list of citations.
  The scanner creates a BibTeX file for use by bibtex/latex for a given project.

- **websiteBuilder** to export our internal new style database into external
  static HTML website. (Create an external version which only contains a
  sub-site specified by a simple list of citations (and their associated
  authors))

## Solution

### Reference extraction (for a latex document)

1. Extract "bib" item from our citation bank

2. Use Jinja2 or [Pybtex!](https://pybtex.org/) to format into a specific bbl (or
   bib) format.

### Reference entry

1. use [Zotero](https://www.zotero.org/) and/or
  [bibitnow](https://github.com/Langenscheiss/bibitnow) to capture a reference
  from a give webpage.

2. Copy the reference in RIS format from Zotero and/or bibitnow into our own
   NiceGUI based tool to add into our own database. We can adjust the reference
   information (citeKey) to suit our needs in the NiceGUI editor before saving.

### Reference database

Our reference database will be:

1. A primary collection of author and citation YAML databases (more than one
   author/citation per file). This will be a collection of human readable text
   files which can be version controlled.

   We will need a mapping from RIS to our form of YAML (possibly a 1-1 mapping).

2. A primary collection of author/citation Markdown files containing extra RIS
   notes. The markdown files will be named using the primary collection's keys.

3. A secondary SQLite3 database (re)built from the primary collection, used for
   searching for existing matching authors and/or citations.

Notes: the primary collections will have a multiple directory structure using
the first two characters of each author/citation keys.

### Online access

We will using Jinja2 templates to expand our reference database into a
collection of static HTML files to be used as our online reference system.

We can have two different "versions" of the templates to provide an external as
well as an internal variant.

## Tasks

### Reference extraction

1. build a (sorted) .bib file from our reference system (our own python script)

2. create a .bbl file from our .bib file (bibtex (no utf-8) or bibulous(python) (utf-8)?)

3. use natbib/amsref/raw-bbl-file

### Phase update of existing citation system

1. Start using Zotero/bibItNow. 

   Need to create an ultra simple NiceGui capture tool, possibly simply saving
   the raw RIS as a file for each citation.

2. Write collector to collect our existing data from old citation system and
   transform into new style database.

3. Merge recently captured citations into new style database.

3. Expand NiceGui capture tool to use new style database. 

## Resources

### LaTeX citation systems

- [natbib](https://www.ctan.org/pkg/natbib) (does not create a "Mathematical" citation)

- [amsref](https://www.ams.org/arc/resources/amsrefs-about.html) (Not used by
  TAC, not allowed in ACM, but is probably allowed in AMS journals; this is the
  format used in most mathematical citations)

- [Embedded bbl-files
  (\\bibitems)](https://en.wikibooks.org/wiki/LaTeX/Bibliography_Management#Embedded_system)

### TeX Tools

- [bibtex](https://www.bibtex.org/) (old useful reference but we won't use)

- [biblatex](https://www.ctan.org/pkg/biblatex) /
  [biber](https://github.com/plk/biber) (Not allowed in ACM)

### Python tools

- [MrTango/rispy: Python RIS files parser, provides RIS files as dictionary via
  generator.](https://github.com/mrtango/rispy)

- [Pybtex](https://pybtex.org/) can be used to create a .bbl which can then be
  included in most journals

- [pybtexris: A pybtex plugin for inputting and outputting RIS
  files](https://github.com/rbturnbull/pybtexris)

- [nicegui: Create web-based user interfaces with Python. The nice
  way.](https://github.com/zauberzeug/nicegui)

### Browser tools

- [Zotero Style Repository](https://www.zotero.org/styles?q=tac)

- [Zotero | Your personal research assistant](https://www.zotero.org/)

- [bibitnow: Site adjustors for browser plugin
  "bibitnow"](https://github.com/Langenscheiss/bibitnow)

## Questions

- how easy would it be to combine our own python script with parts from
  pybtex/pybtexris/rispy?

- how easy would it be to hand-translate an existing .bst file to a pybtex
  style file?
