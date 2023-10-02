
import json
import os
from pathlib import Path
import sys
import yaml

from pybtex.database import \
  BibliographyData, Entry, Person
from pybtex.plugin import find_plugin

from citationManager.biblatexTools import \
  citationPathExists, loadCitation, \
  citation2urlBase, citation2refUrl

def usage() :
  print("""
  usage: cmScan <projBase>

  arguments:
    projBase   The base LaTeX file for which to create Bibliographic entries

  options:
    -h, --help This help text
""")
  sys.exit(1)

typeOfPeople = ['author', 'editor']

def loadConfig(verbose=False) :
  if len(sys.argv) != 2 : usage()

  config = {}
  with open(
    os.path.expanduser('~/.config/citationManager/config.yaml')
  ) as confFile :
    config = yaml.safe_load(confFile.read())

  if 'refsDir' not in config :
    print("ERROR: no references directory has been configured!")
    sys.exit(2)

  if 'entryTypeMapping' not in config :
    config['entryTypeMapping'] = {}

  if 'biblatexFieldMapping' not in config :
    config['biblatexFieldMapping'] = {}

  if 'buildDir' not in config :
    config['buildDir'] = os.path.join('build', 'latex')

  config['bblFile'] = os.path.join(
    config['buildDir'],
    sys.argv[1].replace(r'\..+$','')+'.bbl'
  )
  config['citeFile'] = os.path.join(
    config['buildDir'],
    sys.argv[1].replace(r'\..+$','')+'.cit'
  )

  if verbose :
    print("-------------------------------------------------")
    print(yaml.dump(config))
    print("-------------------------------------------------")

  return config

def cli() :
  config = loadConfig()
  
  knownCitations = {}
  missingCitations = set()
  try :
    with open(config['citeFile']) as citeFile :
      citationData = json.loads(citeFile.read())
      if 'knownCitations' in citationData :
        knownCitations = citationData['knownCitations']
      if 'missingCitations' in citationData :
        missingCitations = set(citationData['missingCitations'])
  except FileNotFoundError as err :
    print(f"Initializing {config['citeFile']} for the first time")
  except Exception as err :
    print(f"ERROR: Oops something went wrong...")
    print(repr(err))
    print(f"(re)Initializing {config['citeFile']} for the first time")
  
  print("")
  newCitations = set()
  for anAuxFilePath in Path(config['buildDir']).glob('**/*.aux') :
    print(f"scanning: {anAuxFilePath}")
    with open(anAuxFilePath) as auxFile :
      for aLine in auxFile.readlines() :
        if aLine.find('\\citation') < 0 : continue
        aCiteId = aLine.replace('\\citation{','').strip().strip('}')
        if aCiteId in knownCitations : continue
        if aCiteId in missingCitations : continue
        newCitations.add(aCiteId)

  citations2load = set()
  citations2load = citations2load.union(missingCitations, newCitations)

  print("")
  for aCiteId in sorted(list(citations2load)) :
    print(f"looking for citation: {aCiteId}")

    if not citationPathExists(aCiteId, refsDir=config['refsDir']) :
      print(f"ERROR: the citation {aCiteId} could not be found!")
      missingCitations.add(aCiteId)
      continue

    citeDict, citeBody = loadCitation(aCiteId, refsDir=config['refsDir'])
    rawBiblatex  = citeDict['biblatex']
    biblatex     = {}
    fieldMapping = config['biblatexFieldMapping']
    for aField, aValue in rawBiblatex.items() :
      if aField in fieldMapping :
        aField = fieldMapping[aField]
      biblatex[aField] = aValue
    knownCitations[aCiteId] = biblatex
    if aCiteId in missingCitations :
      missingCitations.remove(aCiteId)

  # write out the citation data for the next run...
  with open(config['citeFile'], 'w') as citeFile :
    citeFile.write(json.dumps({
      'knownCitations'   : knownCitations,
      'missingCitations' : sorted(list(missingCitations))
    }))

  print("")
  if not newCitations :
    print("no new citations... nothing more to do!")
    return
  else :
    print("new citations found...")

  bibData    = BibliographyData()
  theCiteIds = sorted(list(knownCitations.keys()))
  for aCiteId in theCiteIds :
    biblatex  = knownCitations[aCiteId]
    entryType = biblatex['entrytype']
    if entryType in config['entryTypeMapping'] :
      entryType = config['entryTypeMapping'][entryType]
    theEntry  = Entry(entryType, fields=biblatex)
    for aPersonType in typeOfPeople :
      if aPersonType in biblatex :
        for aPerson in biblatex[aPersonType] :
          theEntry.add_person(Person(aPerson), aPersonType)
    bibData.add_entry(aCiteId, theEntry)
  
  print("")

  ####################################################################
  # USING pybtex to write a bbl file...
  #
  # see pybtex documentation: 
  # https://docs.pybtex.org/api/styles.html#pybtex.style.formatting.BaseStyle
  # and the code in:
  #   pybtex.__init__.py class PybtexEngine::format_from_files
  # 

  # get the style class...
  styleCls = find_plugin('pybtex.style.formatting', 'alpha')

  # initialize a style instance...
  style    = styleCls(
    label_style='alpha',
    name_style='lastfirst',
    sorting_style='author_year_title',
    #abbreviated_names=abbreviatedNames,
    min_crossrefs=2
  )

  # format the bibliography...
  try :
    formattedBibliography = \
      style.format_bibliography(bibData, theCiteIds)
  except Exception as err :
    print(f"ERROR: {repr(err)}")
    return

  # get the 'latex' pybtex backend...
  outputBackend = find_plugin('pybtex.backends', 'latex')

  # write out the bbl file...
  outputBackend('UTF-8').write_to_file(
    formattedBibliography,
    config['bblFile']
  )
