
import importlib.resources
from pathlib import Path
import re
import textwrap
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

def expandSurname(surname) :
  surnameParts = surname.split()
  vonPart = ""
  jrPart  = ""
  if surnameParts and 1 < len(surnameParts) :
    if 0 < len(surnameParts) : vonPart = surnameParts.pop(0)
    if 0 < len(surnameParts) : surname = surnameParts.pop(0)
    if 0 < len(surnameParts) : jrPart  = surnameParts.pop(0)
  return (surname, vonPart, jrPart)

def getPossiblePeopleFromSurname(surname) : 
  surname, vonPart, jrPart = expandSurname(surname)
  print(f"Searching for author: [{surname}] ({vonPart}) ({jrPart})")
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
    surname, vonPart, jrPart = expandSurname(surname)
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

def savedAuthorToFile(anAuthorDict, theNotes) :
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
    if theNotes :
      authorFile.write(theNotes)
      authorFile.write("\n")
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
  #possibleCitations.add(citeKey)
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
    print(f"CiteID author: {aPerson}")
    surname = aPerson.split(',')
    if surname :
      citeId = citeId+surname[0]
  citeId = citeId.replace(' ', '')
  if 'year' in risEntry :
    citeId = citeId+str(risEntry['year'])
  if 'shorttitle' in risEntry :
    lastPart = toCamelCase(risEntry['shorttitle'].strip())
    lastPart = lowerCaseFirstCharacter(lastPart)
    citeId = citeId+lastPart
  citeId = lowerCaseFirstCharacter(citeId)

  if 'url' in biblatexEntry :
    if not isinstance(biblatexEntry['url'], list) :
      biblatexEntry['url'] = [ biblatexEntry['url'] ]
  else :
    biblatexEntry['url'] = []
  
  return (peopleRoles, biblatexEntry, citeId)

def citationPathExists(aCiteId, refsDir=None) :
  if refsDir :
    return (Path(refsDir) / (citation2urlBase(aCiteId) + '.md')).expanduser().exists()
  return Path(citation2urlBase(aCiteId) + '.md').exists()

def savedCitation(aCiteId, aCitationDict, somePeople, theNotes, pdfType) :
  if not isinstance(aCitationDict, dict) :
    return False

  if 'title' not in aCitationDict :
    return False

  # normalize the citation biblatex
  #
  if 'year-date' in aCitationDict :
    yearDate = aCitationDict['year-date']
    del aCitationDict['year-date']
    if yearDate :
      if -1 < yearDate.find('-') :
        if 'date' not in aCitationDict :
          aCitationDict['date'] = yearDate.strip('/')
        if 'year' not in aCitationDict :
          aCitationDict['year'] = yearDate.split('-')
      else :
        if 'year' not in aCitationDict :
          aCitationDict['year'] = yearDate
    if 'year' in aCitationDict :
      aCitationDict['year'] = str(aCitationDict['year'])

  # make sure the citation path exists
  #
  citePath = Path(citation2urlBase(aCiteId) + '.md')
  if not citePath.exists() :
    citePath.parent.mkdir(parents=True, exist_ok=True)

  # write out the citation
  #
  with open(citePath, 'w') as citeFile :
    citeFile.write(f"""---
title: "{aCitationDict['title']}"
biblatex:
""")
    citeFile.write(f"  title: \"{aCitationDict['title']}\"\n")
    del aCitationDict['title']
    citeFile.write(f"  entrytype: {aCitationDict['entrytype']}\n")
    del aCitationDict['entrytype']
    citeFile.write(f"  citekey: {aCiteId}\n")
    del aCitationDict['citekey']
    citeFile.write(f"  citePath: {citation2urlBase(aCiteId)}.md\n")
    citeFile.write(f"  docType: {pdfType}\n")
    citeFile.write(f"  docPath: {pdfType}/{citation2refUrl(aCiteId)}.pdf\n")
    if 'abstract' in aCitationDict :
      citeFile.write(f"  abstract: >\n")
      theLines = textwrap.wrap(
        aCitationDict['abstract'],
        width=70, break_long_words=False,
        expand_tabs=True)
      for aLine in theLines :
        citeFile.write(f"    {aLine}\n")
      del aCitationDict['abstract']
    thePeople = {}
    for aPersonRole in somePeople :
      aPerson, aRole = getPersonRole(aPersonRole)
      if aRole not in thePeople :
        thePeople[aRole] = []
      thePeople[aRole].append(aPerson)
    for aRole, someNames in thePeople.items() :
      if aRole in aCitationDict : 
        del aCitationDict[aRole]
      citeFile.write(f"  {aRole}: \n")
      for aName in someNames :
        citeFile.write(f"    - {aName}\n")
    theCiteKeys = sorted(list(aCitationDict.keys()))
    for aField in theCiteKeys :
      aValue = aCitationDict[aField]
      citeFile.write(f"  {aField}: ")
      if isinstance(aValue, list) :
        citeFile.write("\n")
        for aSingleValue in aValue :
          citeFile.write(f"    - {aSingleValue}\n")
      else :
        if -1 < aField.find('title') or -1 < aValue.find(':'):
          citeFile.write(f'"{aValue}"\n')
        else :
          citeFile.write(f"{aValue}\n")
    citeFile.write("---\n\n")
    if theNotes :
      citeFile.write(theNotes)
      citeFile.write("\n")

  return True
  
def loadCitation(aCiteId, refsDir=None) :
  headerDict   = {}
  bodyMarkdown = ""

  #print(f"loading: {aCiteId}")
  citePath = Path(citation2urlBase(aCiteId) + '.md')
  if refsDir :
    citePath = Path(refsDir) / citePath
  citePath = citePath.expanduser()
  if not citePath.exists() :
    return (headerDict, bodyMarkdown)
  
  with open(citePath) as citeFile :
    preHeader, headerYaml, bodyMarkdown = \
      citeFile.read().split('---\n')
    if not headerYaml : return (headerDict, bodyMarkdown)
    headerDict = yaml.safe_load(headerYaml)

  return (headerDict, bodyMarkdown)