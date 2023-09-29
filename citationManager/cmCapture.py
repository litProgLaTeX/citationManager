
#import importlib.resources
#import json
from nicegui import ui
import os
#import pybtex
#import re
import sys
import yaml

from citationManager.risTools import \
  parseRis, getRisTypes, getBibLatexType
from citationManager.biblatexTools import \
  normalizeBiblatex, \
  getPossibleCitations, \
  citationPathExists, savedCitation, \
  normalizeAuthor, \
  makePersonRole, getPersonRole, \
  getPossiblePeopleFromSurname, \
  authorPathExists, savedAuthorToFile

config = {}
with open(os.path.expanduser("~/.config/citationManager/config.yaml")) as cFile :
  config = yaml.safe_load(cFile.read())

if not config or 'refsDir' not in config :
  print("Sorry you have not specified any references directory!")
  sys.exit(1)

os.chdir(os.path.expanduser(config['refsDir']))
print(f"Working in directory: {config['refsDir']}")

def setupRisTypes() :
  ui.textarea(
    label='RIS types',
    value=getRisTypes()
  ).props('readonly outlined rows=25').classes('w-full')

##########################################################################
# utilities

async def overwriteDialog(aMsg) :
  with ui.dialog() as theDialog, ui.card():
    ui.label(aMsg)
    with ui.row():
      ui.button(
         'No',
        color='green',
        on_click=lambda:  theDialog.submit(False)
      )
      ui.button(
        'Yes',
        color='red',
        on_click=lambda: theDialog.submit(True)
      )
  return await theDialog

##########################################################################
# update interface 

class CmCapture :
  confirmPeopleScroll   = None
  peopleSelectors       = {}
  selectedPeople        = {}
  peopleToAddList       = None
  peopleToAddSelector   = None
  peopleToAddTextArea   = None
  risEntryTextArea      = None
  biblatexEntryTextArea = None
  biblatexEntryChanged  = False
  notesTextArea         = None
  notesChanged          = False
  citeIdSelector        = None
  selectedCiteId        = None
  selectedCiteIdChanged = False
  otherCiteIdInput      = None
  otherCiteIdChanged    = False
  pdfUrlInput           = None
  pdfUrlChanged         = False
  pdfTypeInput          = None
  pdfTypeChanged        = False

cmc = CmCapture()

def clearReference() :
  cmc.confirmPeopleScroll.clear()
  cmc.peopleSelectors = {}
  cmc.selectedPeople  = {}
  cmc.peopleToAddList = None
  cmc.peopleToAddSelector.set_options(["new"], value="new")
  cmc.peopleToAddTextArea.value   = ""
  cmc.risEntryTextArea.value      = ""
  cmc.biblatexEntryTextArea.value = ""
  cmc.biblatexEntryChanged        = False
  cmc.notesTextArea.value         = ""
  cmc.notesChanged                = False
  cmc.citeIdSelector.set_options(['other'], value='other')
  cmc.selectedCiteId              = 'other'
  cmc.selectedCiteIdChanged       = False
  cmc.otherCiteIdInput.value      = ""
  cmc.otherCiteIdChanged          = False
  cmc.pdfUrlInput.value           = ""
  cmc.pdfUrlChanged               = False
  cmc.pdfTypeInput.value          = "public"
  cmc.pdfTypeChanged              = False
  tabs.set_value('risEntry')

def setPeopleSelector(aPersonRole, sel) :
  cmc.selectedPeople[aPersonRole] = sel.value

def setPersonToAdd(aPersonRole) :
  aPersonName, _ = getPersonRole(aPersonRole)
  cmc.peopleToAddTextArea.value = yaml.dump(
    normalizeAuthor(aPersonName),
    allow_unicode=True
  )

def updateReference() :
  aRisString = cmc.risEntryTextArea.value
  biblatexType = getBibLatexType(aRisString)
  risEntry = parseRis(aRisString, biblatexType)
  peopleRoles, biblatexEntry, citeId = normalizeBiblatex(risEntry)

  if cmc.confirmPeopleScroll and peopleRoles :
    with cmc.confirmPeopleScroll :
      for aPersonRole in peopleRoles :
        aName, aRole = getPersonRole(aPersonRole)
        posPeople = ['new']
        surname = aName.split(',')
        if surname :
          posPeople = getPossiblePeopleFromSurname(surname[0]) #, config)

        if aPersonRole in cmc.peopleSelectors : 
          if aPersonRole not in cmc.selectedPeople :
            cmc.selectedPeople[aPersonRole] = posPeople[0]
          cmc.peopleSelectors[aPersonRole].set_options(
            posPeople,
            value=cmc.selectedPeople[aPersonRole]
          )
        else :
          ui.markdown(f"**{aRole}**: {aName}")
          cmc.peopleSelectors[aPersonRole] = ui.select(
            posPeople,
            value=posPeople[0],
            on_change= \
              lambda sel, aPersonRole=aPersonRole : \
                setPeopleSelector(aPersonRole, sel)
          ).props("outlined")
  
  cmc.peopleToAddList = []
  if peopleRoles :
    for aPersonRole, aSelector in cmc.peopleSelectors.items() :
      if aSelector.value == 'new' :
        cmc.peopleToAddList.append(str(aPersonRole))
  if 0 < len(cmc.peopleToAddList) :
    cmc.peopleToAddSelector.set_options(
      cmc.peopleToAddList, value=cmc.peopleToAddList[0]
    )
    setPersonToAdd(cmc.peopleToAddSelector.value)

  if cmc.biblatexEntryTextArea and biblatexEntry and not cmc.biblatexEntryChanged :
    cmc.biblatexEntryTextArea.value = yaml.dump(biblatexEntry, allow_unicode=True)

  selectedCiteId = 'other'
  cmc.citeIdSelector.set_options(
    getPossibleCitations(citeId),
    value=selectedCiteId
  )

  if cmc.otherCiteIdInput and citeId and not cmc.otherCiteIdChanged :
    cmc.otherCiteIdInput.value = citeId

  if cmc.pdfUrlInput and 'url' in biblatexEntry and not cmc.pdfUrlChanged :
      if 0 < len(biblatexEntry['url']) :
        cmc.pdfUrlInput.value = biblatexEntry['url'][0]
        #cmc.pdfUrlChanged = True

##########################################################################
# setup progression through tabs

def sortRIS() :
  aRisString = cmc.risEntryTextArea.value
  risLines = aRisString.splitlines()
  deDupedRisLines = set()
  for aLine in risLines :
    if aLine.startswith('ER  -') : continue
    if aLine.strip() == ''       : continue
    deDupedRisLines.add(aLine)
  cmc.risEntryTextArea.value = "\n".join(sorted(list(deDupedRisLines)))

def progressToConfirmPeople() :
  biblatexType = getBibLatexType(cmc.risEntryTextArea.value)
  if not biblatexType :
    ui.notify('Could not find a valid BibLaTeX type in the RIS-TY field... please specify a known reference type!')
  else :
    updateReference()
    tabs.set_value('confirmPeople')

def setupRisEntry() :
  cmc.risEntryTextArea = ui.textarea(
    label='Reference RIS',
    placeholder='Paste reference RIS here...'
  ).props("clearable outlined rows=25").classes('w-full')

  with ui.row() :
    ui.button(
      'Sort RIS',
      on_click=lambda: sortRIS()
    )
    ui.button(
      'Confirm People',
      color='green',
      on_click=lambda: progressToConfirmPeople()
    )
    ui.button(
      'Restart...',
      color='red',
      on_click=lambda: clearReference()
    )

def progressToCheckPeople() :
  updateReference()
  if 0 < len(cmc.peopleToAddList) :
    tabs.set_value('addPeople')
  else :  
    cmc.peopleToAddList = None
    tabs.set_value('biblatexEntry')

def setupConfirmPeople() :
  cmc.peopleSelectors = {}
  with ui.row():
    with ui.card().classes('w-full').props('rows=25') :
      cmc.confirmPeopleScroll = ui.scroll_area()
  with ui.row() :
    ui.button(
      'Review required fields',
      color='green',
      on_click=lambda: progressToCheckPeople()
    )
    ui.button(
      'Restart...',
      color='red',
      on_click=lambda: clearReference()
    )

async def savePerson() :
  aPersonYaml = cmc.peopleToAddTextArea.value
  if not aPersonYaml :
    ui.notify("No author data has been provided")
    tabs.set_value('confirmPeople')
    return
  try :
    aPersonDict = yaml.safe_load(aPersonYaml)
  except Exception as err :
    ui.notify(f"Could not parse the author's YAML\n{repr(err)}")
    tabs.set_value('confirmPeople')
    return
  
  if authorPathExists(aPersonDict) :
    if not await overwriteDialog(
      f"The author {aPersonDict['cleanname']} already exists, do you want to overwrite this author?"
    ) : 
      tabs.set_value('confirmPeople')
      return
    ui.notify(f'Overwriting author')

  if savedAuthorToFile(aPersonDict) : 
    ui.notify("Author saved")
    updateReference()
  tabs.set_value('confirmPeople')

def setupAddPeople() :
  cmc.peopleToAddSelector = ui.select(
    ['choose author'],
    value='choose author',
    on_change=lambda sel : setPersonToAdd(sel.value)
  )
  cmc.peopleToAddTextArea = ui.textarea(
    label='Add new author',
    placeholder='Add new author details here...'
  ).props("clearable outlined rows=25").classes('w-full')
  with ui.row() :
    ui.button(
     'Save person',
     color='green',
      on_click=lambda: savePerson()
    )
    ui.button(
      'Restart...',
      color='red',
      on_click=lambda: clearReference()
    )

def setBiblatexEntryChanged() :
  if cmc.biblatexEntryTextArea.value :
    cmc.biblatexEntryChanged = True
  else : # has been cleared!
    cmc.biblatexEntryChanged = False

def setupBiblatexEntry() :
  cmc.biblatexEntryTextArea = ui.textarea(
    label='BibLaTeX entry',
    placeholder='Update BibLaTeX entry here...',
    on_change=lambda : setBiblatexEntryChanged()
  ).props("clearable outlined rows=25").classes('w-full')
  with ui.row() :
    ui.button(
      'Review notes',
      color='green',
      on_click=lambda: tabs.set_value('notes')
    )
    ui.button(
      'Restart...',
      color='red',
      on_click=lambda: clearReference()
    )

def setNotesChanged() :
  if cmc.notesTextArea.value :
    cmc.notesChanged = True
  else : # has been cleared!
    cmc.notesChanged = False

def setupNotes() :
  cmc.notesTextArea = ui.textarea(
    label='Notes',
    placeholder='Update notes here...',
    on_change=lambda : setNotesChanged()
  ).props("clearable outlined rows=25").classes('w-full')
  with ui.row() :
    ui.button(
      'Review citation ID and save',
      color='green',
      on_click=lambda: tabs.set_value('saveRef')
    )
    ui.button(
      'Restart...',
      color='red',
      on_click=lambda: clearReference()
    )

def CheckForDuplicateCitations() :
  posCitations = getPossibleCitations(cmc.otherCiteIdInput.value)
  cmc.citeIdSelector.set_options(
    posCitations,
    value=posCitations[0]
  )

async def saveReference() :
  theCiteId = cmc.otherCiteIdInput.value
  if cmc.selectedCiteId != 'other' :
    theCiteId = cmc.selectedCiteId
  if citationPathExists(theCiteId) :
    if not await overwriteDialog(
      f'The citation [{theCiteId}] already exists,\n  do you really want to overwrite this citation?'
    ) : 
      #tabs.set_value('confirmPeople')
      return
    ui.notify(f'Overwriting citation')

  theCitation = {}
  try : 
    theCitation = yaml.safe_load(
      cmc.biblatexEntryTextArea.value
    )
  except Exception as err :
    ui.notify(f"Could not parse the biblatex YAML\n{repr(err)}")
    return
  somePeople = sorted(list(cmc.peopleSelectors.keys()))
  if savedCitation(
    theCiteId,
    theCitation,
    somePeople
  ) :
    ui.notify("Citation saved")

def setSelectedCiteId(sel) :
  cmc.selectedCiteId = sel.value
  cmc.selectedCiteIdChanged = True
def setOtherCiteIdChanged() :
  if cmc.otherCiteIdInput.value :
    cmc.otherCiteIdChanged = True
  else : # has been cleared!
    cmc.otherCiteIdChanged = False
def setPdfUrlChanged() :
  if cmc.pdfUrlInput.value :
    cmc.pdfUrlChanged = True
  else : # has been cleared!
    cmc.pdfUrlChanged = False
def setPdfTypeChanged() :
  cmc.pdfTypeChanged = True

def setupSaveRef() :
  cmc.citeIdSelector = ui.select(
    ['other'],
    value='other',
    on_change=lambda sel : setSelectedCiteId(sel)
  ).props('outlined')
  cmc.selectedCiteId = 'other'
  cmc.otherCiteIdInput = ui.input(
    label='Other citation ID',
    placeholder='Update other citation id here...',
    on_change=lambda : setOtherCiteIdChanged()
  ).props("clearable outlined").classes('w-full')
  cmc.pdfUrlInput = ui.input(
    label='PDF url',
    placeholder='Add a valid url for the PDF',
    on_change=lambda : setPdfUrlChanged()
  ).props("clearable outlined").classes('w-full')
  cmc.pdfTypeInput = ui.select([
    'owned', 'public', 'unknown',
  ], value='public',
    on_change=lambda : setPdfTypeChanged()
  ).props('outlined')
  with ui.row() :
    ui.button(
      'Recheck for duplicates',
      on_click=lambda: CheckForDuplicateCitations()
    )
    ui.button(
      'Save reference',
      color='green',
      on_click=lambda: saveReference()
    )
    ui.button(
      'Restart...',
      color='red',
      on_click=lambda: clearReference()
    )

##########################################################################
# block out the main interface 

with ui.header().classes(replace='row items-center') as header:
  with ui.tabs() as tabs:
    ui.tab('risTypes',      label='RIS types')
    ui.tab('risEntry',      label='RIS entry')
    ui.tab('confirmPeople', label='Confirm People')
    ui.tab('addPeople',     label='Add People')
    ui.tab('biblatexEntry', label='BibLaTeX entry')
    ui.tab('notes',         label='notes')
    ui.tab('saveRef',       label='Save reference')

with ui.tab_panels(tabs, value='risEntry').classes('w-full'):
  with ui.tab_panel('risTypes') :
    setupRisTypes()
  with ui.tab_panel('risEntry'):
    setupRisEntry()
  with ui.tab_panel('confirmPeople'):
    setupConfirmPeople()
  with ui.tab_panel('addPeople') :
    setupAddPeople()
  with ui.tab_panel('biblatexEntry'):
    setupBiblatexEntry()
  with ui.tab_panel('notes'):
    setupNotes()
  with ui.tab_panel('saveRef') :
    setupSaveRef()

##########################################################################
# Run the app

ui.run(
  title='Citation Manager Capture reference',
  reload=True
)
