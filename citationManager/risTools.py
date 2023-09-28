
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

# check for the RIS-Type line ('TY' two spaces a dash and a space)
risTypeRegExp = re.compile(r'^TY\s\s-\s(\S+)', re.MULTILINE)

def getBibLatexType(aRisString) :
  aMatch = risTypeRegExp.search(aRisString)
  if not aMatch : return None

  aRisTypeTag = aMatch.group(1).upper()
  risTypes = yaml.safe_load(getRisTypes())
  if aRisTypeTag not in risTypes : return None

  biblatexType = risTypes[aRisTypeTag]['biblatex']
  if not biblatexType : return None

  return biblatexType

risTagRegExp = re.compile(r'^\S+')
def parseRis(aRisString, biblatexType) :
  risFields = yaml.safe_load(getRisFields())
  
  risEntry = {}
  for aLine in aRisString.splitlines() :
    if not aLine : continue
    aTag = risTagRegExp.match(aLine).group(0)
    if aTag == 'ER' : continue
    if aTag == 'TY' :
      risEntry['entrytype'] = biblatexType
      continue
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
