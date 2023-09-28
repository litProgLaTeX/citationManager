
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
  normalizeBiblatex, normalizeAuthor, \
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
  citeIdInput           = None
  citeIdChanged         = False
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
  cmc.citeIdInput.value           = ""
  cmc.citeIdChanged               = False
  cmc.pdfUrlInput.value           = ""
  cmc.pdfUrlChanged               = False
  cmc.pdfTypeInput.value          = ""
  cmc.pdfTypeChanged              = False
  tabs.set_value('risEntry')

def setPeopleSelector(aPerson, sel) :
  print(f"setting selectedPeople[{aPerson}] = {sel.value}")
  cmc.selectedPeople[aPerson] = sel.value

def updateReference() :
  print("=======================================")
  aRisString = cmc.risEntryTextArea.value
  biblatexType = getBibLatexType(aRisString)
  risEntry = parseRis(aRisString, biblatexType)
  people, biblatexEntry, citeId = normalizeBiblatex(risEntry)

  if cmc.confirmPeopleScroll and people :
    #cmc.confirmPeopleScroll.clear()
    with cmc.confirmPeopleScroll :
      for aPersonType in people :
        for aPerson in people[aPersonType] :
          print(aPerson)
          posPeople = ['new']
          surname = aPerson.split(',')
          if surname :
            posPeople = getPossiblePeopleFromSurname(surname[0]) #, config)

          print(yaml.dump(posPeople))
          if aPerson in cmc.peopleSelectors : 
            if aPerson not in cmc.selectedPeople \
              or cmc.selectedPeople[aPerson] == 'new' :
              print(f"resetting selectedPeople[{aPerson}] = {posPeople[0]}")
              cmc.selectedPeople[aPerson] = posPeople[0]
            print("----------------")
            print(yaml.dump(cmc.selectedPeople))
            cmc.peopleSelectors[aPerson].set_options(
              posPeople,
              value=cmc.selectedPeople[aPerson]
            )
          else :
            ui.markdown(f"**{aPersonType}**: {aPerson}")
            cmc.peopleSelectors[aPerson] = ui.select(
              posPeople,
              value=posPeople[0],
              on_change=lambda sel, aPerson=aPerson : setPeopleSelector(aPerson, sel)
            ).props("outlined")
  
  cmc.peopleToAddList = []
  if people :
    for aPerson, aSelector in cmc.peopleSelectors.items() :
      if aSelector.value == 'new' :
        cmc.peopleToAddList.append(aPerson)
  if 0 < len(cmc.peopleToAddList) :
    cmc.peopleToAddSelector.set_options(
      cmc.peopleToAddList, value=cmc.peopleToAddList[0]
    )
    cmc.peopleToAddTextArea.value = yaml.dump(
      normalizeAuthor(
        cmc.peopleToAddSelector.value
      ),
      allow_unicode=True
    )

  if cmc.biblatexEntryTextArea and biblatexEntry and not cmc.biblatexEntryChanged :
    cmc.biblatexEntryTextArea.value = yaml.dump(biblatexEntry, allow_unicode=True)

  if cmc.citeIdInput and citeId and not cmc.citeIdChanged :
    cmc.citeIdInput.value = citeId
    #cmc.citeIdChanged = True

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
    with ui.dialog() as overwriteDialog, ui.card():
      ui.label('The author already exists, do you want to overwrite this author?')
      with ui.row():
        ui.button(
          'Yes',
          color='green',
          on_click=lambda: overwriteDialog.submit(True)
        )
        ui.button(
          'No',
          color='red',
          on_click=lambda:  overwriteDialog.submit(False)
        )

    if not await overwriteDialog : 
      tabs.set_value('confirmPeople')
      return
    ui.notify(f'Overwriting author')

  if savedAuthorToFile(aPersonDict) : 
    ui.notify("Author saved")
    updateReference()
  tabs.set_value('confirmPeople')

def setupAddPeople() :
  cmc.peopleToAddSelector = ui.select(
    ['choose author'], value='choose author'
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

def saveReference() :
  pass

def setCiteIdChanged() :
  if cmc.citeIdInput.value :
    cmc.citeIdChanged = True
  else : # has been cleared!
    cmc.citeIdChanged = False
def setPdfUrlChanged() :
  if cmc.pdfUrlInput.value :
    cmc.pdfUrlChanged = True
  else : # has been cleared!
    cmc.pdfUrlChanged = False
def setPdfTypeChanged() :
  if cmc.pdfTypeInput.value :
    cmc.pdfTypeChanged = True
  else : # has been cleared!
    cmc.pdfTypeChanged = False

def setupSaveRef() :
  cmc.citeIdInput = ui.input(
    label='Citation ID',
    placeholder='Update citation id here...',
    on_change=lambda : setCiteIdChanged()
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
  )
  with ui.row() :
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
