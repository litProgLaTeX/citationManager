
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
# People

removeStrangeChars      = re.compile(r"[\'\",\.\{\} \t\n\r]+")
removeMultipleDashes    = re.compile(r"\-+")
removeLeadingDashes     = re.compile(r"^\-+")
removeTrailingDashes    = re.compile(r"\-+$")
removeMultipleSpaces    = re.compile(r"\s+")
removeSpacesBeforeComma = re.compile(r"\s+\,")

def author2urlBase(authorName) :
  authorFileName = authorName[:] # (makes a *copy*)
  authorFileName = removeStrangeChars.sub('-', authorFileName)
  authorFileName = removeMultipleDashes.sub('-', authorFileName)
  authorFileName = removeLeadingDashes.sub('', authorFileName)
  authorFileName = removeTrailingDashes.sub('', authorFileName)
  #print(f"author/{authorFileName[0:2]}/{authorFileName}")
  return f"author/{authorFileName[0:2]}/{authorFileName}"

def getPossiblePeopleFromSurname(surname) : 
  authorDir = Path('author')
  possibleAuthors = []
  for anAuthor in authorDir.glob(f'*/*{surname}*') :
    anAuthor = str(anAuthor.name).removesuffix('.md')
    possibleAuthors.append(anAuthor)
  possibleAuthors.append("new")
  possibleAuthors.sort()
  return possibleAuthors

def makePersonRole(anAuthor, aRole) :
  return f"{aRole}:{anAuthor}"

def getPersonRole(anAuthorRole) :
  aRole = 'unknown'
  anAuthor = anAuthorRole
  if -1 < anAuthorRole.find(':') :
    theParts = anAuthorRole.split(':')
    aRole = theParts[0].strip()
    anAuthor = theParts[1].strip()
  return (anAuthor, aRole)

def normalizeAuthor(anAuthorRole) :
  anAuthor, aRole = getPersonRole(anAuthorRole)
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

def authorPathExists(anAuthorDict) :
  return Path(author2urlBase(anAuthorDict['cleanname']) + '.md').exists()

def savedAuthorToFile(anAuthorDict) :
  if not isinstance(anAuthorDict, dict) : return False
  if 'cleanname' not in anAuthorDict    : return False
  
  authorPath = Path(author2urlBase(anAuthorDict['cleanname']) + '.md')

  if not authorPath.exists() :
    authorPath.parent.mkdir(parents=True, exist_ok=True)

  with open(authorPath, 'w') as authorFile :
    authorFile.write(f"""---
title: {anAuthorDict['cleanname']}
biblatex:
  cleanname: {anAuthorDict['cleanname']}
  von: {anAuthorDict['von']}
  surname: {anAuthorDict['surname']}
  jr: {anAuthorDict['jr']}
  firstname: {anAuthorDict['firstname']}
  email: {anAuthorDict['email']}
  institute: {anAuthorDict['institute']}
""")
    if anAuthorDict['url'] :
      if isinstance(anAuthorDict['url'], str) :
        authorFile.write(f"  url: {anAuthorDict['url']}\n")
      else :
        authorFile.write("  url:\n")
        for aUrl in anAuthorDict['url'] :
          authorFile.write(f"    - {aUrl}\n")
    else :
      authorFile.write("  url: []\n")
    authorFile.write("---\n\n")

  return True

#####################################################################
# Citations

removeLeadingDigitsWhiteSpace = re.compile(r"^[0-9]+[ \t]+")

def citation2refUrl(citeKey) :
  citeKeyLocal = removeLeadingDigitsWhiteSpace.sub('', citeKey)
  return f"{citeKeyLocal[0:2]}/{citeKeyLocal}"

def citation2urlBase(citeKey) :
  citeKeyLocal = removeLeadingDigitsWhiteSpace.sub('', citeKey)
  return "cite/" + citation2refUrl(citeKey)

def getPossibleCitations(citeKey) :
  possibleCitations = set()
  possibleCitations.add(citeKey)
  for aCitation in Path("cite").glob(f"*/*{citeKey[0:5]}*") :
    aCitation = str(aCitation.name).removesuffix('.md')
    possibleCitations.add(aCitation)
  possibleCitations = sorted(list(possibleCitations))
  possibleCitations.append("other")
  return possibleCitations

def getSomePeople(risEntry, aPersonRole) :
  somePeople = []
  if aPersonRole in risEntry :
    somePeople = risEntry[aPersonRole]
    if isinstance(somePeople, str) :
      somePeople = [ somePeople ]
    del risEntry[aPersonRole]
  somePeopleRoles = []
  for aPersonName in somePeople :
    somePeopleRoles.append(makePersonRole(aPersonName, aPersonRole))
  return somePeopleRoles

def normalizeBiblatex(risEntry) :
  biblatexType = risEntry['entrytype']
  peopleRoles = []
  peopleRoles.extend(getSomePeople(risEntry, 'author'))
  peopleRoles.extend(getSomePeople(risEntry, 'editor'))
  peopleRoles.extend(getSomePeople(risEntry, 'translator'))

  biblatexTypes = yaml.safe_load(getBibLatexTypes())
  biblatexEntry = risEntry
  if biblatexType in biblatexTypes :
    reqBiblatexFields = biblatexTypes[biblatexType]['requiredFields']
    for aField in reqBiblatexFields :
      if aField not in biblatexEntry : biblatexEntry[aField] = ''

  citeId = ''
  for aPersonRole in peopleRoles :
    aPerson, aRole = getPersonRole(aPersonRole)
    if aRole != 'author' : continue
    surname = aPerson.split(',')
    if surname :
      citeId = citeId+surname[0]
  if 'year' in risEntry :
    citeId = citeId+str(risEntry['year'])
  if 'shorttitle' in risEntry :
    lastPart = toCamelCase(risEntry['shorttitle'].strip())
    lastPart = lowerCaseFirstCharacter(lastPart)
    citeId = citeId+lastPart
  citeId = lowerCaseFirstCharacter(citeId)

  return (peopleRoles, biblatexEntry, citeId)

def citationPathExists(aCiteId) :
  return Path(citation2urlBase(aCiteId) + '.md').exists()

def savedCitation(aCiteId, aCitation, somePeople) :
  print("saving citation")
  print("----------------------------------")
  print(aCiteId)
  print("----------------------------------")
  print(yaml.dump(aCitation))
  print("----------------------------------")
  print(yaml.dump(somePeople))
  print("----------------------------------")
  return False
