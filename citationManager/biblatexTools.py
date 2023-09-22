
import importlib.resources
from pathlib import Path
import yaml

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

def getPossibleAuthorsFromSurname(surname, config) :
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

lowerCaseFirstCharacter = lambda s: s[:1].lower() + s[1:] if s else ''

def toCamelCase(text):
    s = text.replace("-", " ").replace("_", " ")
    s = s.split()
    if len(text) == 0:
        return text
    return s[0] + ''.join(i.capitalize() for i in s[1:])

def normalizeBiblatex(risEntry) :
  authors = []
  if 'author' in risEntry :
    authors = risEntry['author']
    del risEntry['author']
  citeId = ''
  for anAuthor in authors :
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
  return (authors, risEntry, "", citeId)
