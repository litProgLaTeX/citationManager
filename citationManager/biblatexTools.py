
import importlib.resources
from pathlib import Path
import re
import yaml

#####################################################################
# Utilities

def getBibLatexTypes() :
  return importlib.resources.files(
    "citationManager.resources"
  ).joinpath(
    "biblatexTypes.yaml"
  ).open(
    'r', encoding='utf-8'
  ).read()

def getBibLatexFields() :
  return importlib.resources.files(
    "citationManager.resources"
  ).joinpath(
    "biblatexFields.yaml"
  ).open(
    'r', encoding='utf-8'
  ).read()

lowerCaseFirstCharacter = lambda s: s[:1].lower() + s[1:] if s else ''

def toCamelCase(text):
    s = text.replace("-", " ").replace("_", " ")
    s = s.split()
    if len(text) == 0:
        return text
    return s[0] + ''.join(i.capitalize() for i in s[1:])

#####################################################################
# Citations

def getAPerson(risEntry, aPersonType) :
  somePeople = []
  if aPersonType in risEntry :
    somePeople = risEntry[aPersonType]
    if isinstance(somePeople, str) :
      somePeople = [ somePeople ]
    del risEntry[aPersonType]
  return somePeople

def normalizeBiblatex(risEntry) :
  biblatexType = risEntry['entrytype']
  people = {
    'author'     : [],
    'editor'     : [],
    'translator' : []
  }
  people['author']     = getAPerson(risEntry, 'author')
  people['editor']     = getAPerson(risEntry, 'editor')
  people['translator'] = getAPerson(risEntry, 'translator')

  biblatexTypes = yaml.safe_load(getBibLatexTypes())
  biblatexEntry = risEntry
  if biblatexType in biblatexTypes :
    reqBiblatexFields = biblatexTypes[biblatexType]['requiredFields']
    for aField in reqBiblatexFields :
      if aField not in biblatexEntry : biblatexEntry[aField] = ''

  citeId = ''
  for anAuthor in people['author'] :
    surname = anAuthor.split(',')
    if surname :
      citeId = citeId+surname[0]
  if 'year' in risEntry :
    citeId = citeId+str(risEntry['year'])
  if 'shorttitle' in risEntry :
    lastPart = toCamelCase(risEntry['shorttitle'].strip())
    lastPart = lowerCaseFirstCharacter(lastPart)
    citeId = citeId+lastPart
  citeId = lowerCaseFirstCharacter(citeId)

  return (people, biblatexEntry, citeId)

def saveCitation(aCitation) :
  pass

#####################################################################
# People

def getPossiblePeopleFromSurname(surname, config) :
  baseDir = Path('.')
  if 'oldRefs' in config and 'baseDir' in config['oldRefs'] :
    baseDir = Path(config['oldRefs']['baseDir']).expanduser()
  authorDir = baseDir / 'author'
  possibleAuthors = []
  for anAuthor in authorDir.glob(f'*/*{surname}*') :
    anAuthor = str(anAuthor.name).removesuffix('.md')
    possibleAuthors.append(anAuthor)
  possibleAuthors.append("new")
  possibleAuthors.sort()
  return possibleAuthors

removeMultipleSpaces    = re.compile(r"\s+")
removeSpacesBeforeComma = re.compile(r"\s+\,")

def normalizeAuthor(anAuthor) :
  authorDict = {
    'cleanname' : anAuthor,
    'surname'   : '',
    'firstname' : '',
    'von'       : '',
    'jr'        : '',
    'email'     : '',
    'institute' : '',
    'url'       : []
  }

  nameParts = anAuthor.split(',')
  if nameParts :
    surname = nameParts[0].strip()
    surnameParts = surname.split()
    vonPart = ""
    jrPart  = ""
    if surnameParts and 1 < len(surnameParts) :
      if 0 < len(surnameParts) : vonPart = surnameParts.pop(0)
      if 0 < len(surnameParts) : surname = surnameParts.pop(0)
      if 0 < len(surnameParts) : jrPart  = surnameParts.pop(0)
    firstname = ""
    if 1 < len(nameParts) :
      firstname = nameParts[1].replace('.', ' ').strip()
    cleanName = f" {vonPart} {surname} {jrPart}, {firstname}"
    cleanName = removeMultipleSpaces.sub(" ", cleanName)
    cleanName = removeSpacesBeforeComma.sub(",", cleanName)
    cleanName = cleanName.strip()
    authorDict['cleanname'] = cleanName
    authorDict['surname']   = surname
    authorDict['firstname'] = firstname
    authorDict['von']       = vonPart
    authorDict['jr']        = jrPart
  return authorDict

def saveAuthor(anAuthorDict) :
  pass