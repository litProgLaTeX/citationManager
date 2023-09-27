
#import importlib.resources
#import json
from nicegui import ui
import os
#import pybtex
#import re
import yaml

from citationManager.risTools import \
  parseRis, getRisTypes, getBibLatexType
from citationManager.biblatexTools import \
  normalizeBiblatex, normalizeAuthor, \
  getPossiblePeopleFromSurname

config = {}
with open(os.path.expanduser("~/.config/citationManager/config.yaml")) as cFile :
  config = yaml.safe_load(cFile.read())

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

def setPeopleSelector(aPerson, sel) :
  cmc.selectedPeople[aPerson] = sel.value

def updateReference() :
  aRisString = cmc.risEntryTextArea.value
  biblatexType = getBibLatexType(aRisString)
  risEntry = parseRis(aRisString, biblatexType)
  people, biblatexEntry, citeId = normalizeBiblatex(risEntry)

  if cmc.confirmPeopleScroll and people :
    #cmc.confirmPeopleScroll.clear()
    with cmc.confirmPeopleScroll :
      for aPersonType in people :
        for aPerson in people[aPersonType] :
          posPeople = ['new']
          surname = aPerson.split(',')
          if surname :
            posPeople = getPossiblePeopleFromSurname(surname[0], config)

          if aPerson in cmc.peopleSelectors : 
            if aPerson not in cmc.selectedPeople :
              cmc.selectedPeople[aPerson] = posPeople[0]
            cmc.peopleSelectors[aPerson].set_options(
              posPeople,
              value=cmc.selectedPeople[aPerson]
            )
          else :
            ui.markdown(f"**{aPersonType}**: {aPerson}")
            cmc.peopleSelectors[aPerson] = ui.select(
              posPeople,
              value=posPeople[0],
              on_change=lambda sel : setPeopleSelector(aPerson, sel)
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
    cmc.citeIdChanged = True

  if cmc.pdfUrlInput and 'url' in biblatexEntry and not cmc.pdfUrlChanged :
      if 0 < len(biblatexEntry['url']) :
        cmc.pdfUrlInput.value = biblatexEntry['url'][0]
        cmc.pdfUrlChanged = True

##########################################################################
# setup progression through tabs

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
  ).props("outlined rows=25").classes('w-full')

  ui.button(
    'Confirm People',
    on_click=lambda: progressToConfirmPeople()
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
  ui.button(
    'Review required fields',
    on_click=lambda: progressToCheckPeople()
  )

def savePerson() :
  pass

def setupAddPeople() :
  cmc.peopleToAddSelector = ui.select(
    ['choose author'], value='choose author'
  )
  cmc.peopleToAddTextArea = ui.textarea(
    label='Add new author',
    placeholder='Add new author details here...'
  ).props("outlined rows=25").classes('w-full')
  ui.button(
    'Save person',
    on_click=lambda: savePerson()
  )

def setBiblatexEntryChanged() :
  cmc.biblatexEntryChanged = True

def setupBiblatexEntry() :
  cmc.biblatexEntryTextArea = ui.textarea(
    label='BibLaTeX entry',
    placeholder='Update BibLaTeX entry here...',
    on_change=lambda : setBiblatexEntryChanged()
  ).props("outlined rows=25").classes('w-full')
  ui.button(
    'Review notes',
    on_click=lambda: tabs.set_value('notes')
  )

def setNotesChanged() :
  cmc.notesChanged = True

def setupNotes() :
  cmc.notesTextArea = ui.textarea(
    label='Notes',
    placeholder='Update notes here...',
    on_change=lambda : setNotesChanged()
  ).props("outlined rows=25").classes('w-full')
  ui.button(
    'Review citation ID and save',
    on_click=lambda: tabs.set_value('saveRef')
  )

def saveReference() :
  pass

def setCiteIdChanged() :
  cmc.citeIdChanged = True
def setPdfUrlChanged() :
  cmc.pdfUrlChanged = True
def setPdfTypeChanged() :
  cmc.pdfTypeChanged = True

def setupSaveRef() :
  cmc.citeIdInput = ui.input(
    label='Citation ID',
    placeholder='Update citation id here...',
    on_change=lambda : setCiteIdChanged()
  ).props("outlined").classes('w-full')
  cmc.pdfUrlInput = ui.input(
    label='PDF url',
    placeholder='Add a valid url for the PDF',
    on_change=lambda : setPdfUrlChanged()
  )
  cmc.pdfTypeInput = ui.select([
    'owned', 'public', 'unknown',
  ], value='public',
    on_change=lambda : setPdfTypeChanged()
  )
  ui.button(
    'Save reference',
    on_click=lambda: saveReference()
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
