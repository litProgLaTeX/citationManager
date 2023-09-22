
import importlib.resources
import re
import yaml

def getRisTypes() :
  return importlib.resources.files(
    "citationManager.resources"
  ).joinpath(
    "risTypes.yaml"
  ).open(
    'r', encoding='utf-8'
  ).read()

def getRisFields() :
  return importlib.resources.files(
    "citationManager.resources"
  ).joinpath(
    "risFields.yaml"
  ).open(
    'r', encoding='utf-8'
  ).read()

risTagRegExp = re.compile(r'^\S+')
def parseRis(aRisString) :
  risFields = yaml.safe_load(getRisFields())
  
  risEntry = {}
  for aLine in aRisString.splitlines() :
    if not aLine : continue
    aTag = risTagRegExp.match(aLine).group(0)
    if aTag == 'ER' : continue
    contents = aLine.replace(aTag, '').strip().removeprefix('-').strip()
    if aTag in risFields and risFields[aTag]['biblatex'] :
      aTag = risFields[aTag]['biblatex']
    if aTag in risEntry :
      if not isinstance(risEntry[aTag], list) :
        oldEntry = risEntry[aTag]
        risEntry[aTag] = [oldEntry]
      risEntry[aTag].append(contents)
    else :
      risEntry[aTag] = contents
  if 'firstpage' in risEntry and 'lastpage' in risEntry :
    risEntry['pages'] = f"{risEntry['firstpage']}-{risEntry['lastpage']}"
    del risEntry['firstpage']
    del risEntry['lastpage']
  if 'firstpage' in risEntry :
    risEntry['pages'] = risEntry['firstpage']
    del risEntry['firstPage']
  if 'lastpage'  in risEntry :
    risEntry['pages'] = risEntry['lastpage']
    del risEntry['lastpage']
  return risEntry
