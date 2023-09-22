
#import importlib.resources
#import json
from nicegui import ui
import os
#import pybtex
#import re
import yaml

from citationManager.risTools import \
  parseRis, getRisTypes
from citationManager.biblatexTools import \
  normalizeBiblatex, getPossibleAuthorsFromSurname

config = {}
with open(os.path.expanduser("~/.config/citationManager/config.yaml")) as cFile :
  config = yaml.safe_load(cFile.read())

def setupRisTypes() :
  ui.textarea(
    label='RIS types',
    value=getRisTypes()
  ).props('readonly outlined rows=25').classes('w-full')

globalUI = {
  'confirm'   : None,
  'authors'   : None,
  'reqFields' : None,
  'optFields' : None,
  'citeId'    : None,
  'pdfUrl'    : None,
  'pdfType'   : None,
  'rawEntry'  : None,
}

def parseReference(risRef) :
  risEntry = parseRis(risRef.value)
  authors, reqFields, optFields, citeId = normalizeBiblatex(risEntry)
  globalUI['rawEntry'] = reqFields
  if globalUI['confirm'] and authors :
    globalUI['authors'] = {}
    globalUI['confirm'].clear()
    with globalUI['confirm'] :
      for anAuthor in authors :
        posAuthors = ['new']
        surname = anAuthor.split(',')
        if surname :
          posAuthors = getPossibleAuthorsFromSurname(surname[0], config)
        globalUI['authors'][anAuthor] = ui.select(
          posAuthors,
          value=posAuthors[0]
        )
  
  if globalUI['reqFields'] and reqFields :
    globalUI['reqFields'].value = yaml.dump(reqFields, allow_unicode=True)
  if globalUI['optFields'] and optFields :
    globalUI['optFields'].value = yaml.dump(optFields, allow_unicode=True)
  if globalUI['citeId'] and citeId :
    globalUI['citeId'].value = citeId
  if globalUI['pdfUrl'] and 'url' in reqFields :
      if 0 < len(reqFields['url']) :
        globalUI['pdfUrl'].value = reqFields['url'][0]
  tabs.set_value('Confirm authors')

def setupRisEntry() :
  risRef = ui.textarea(
    label='Reference RIS',
    placeholder='Paste reference RIS here...'
  ).props("outlined rows=25").classes('w-full')

  ui.button(
    'Confirm authors',
    on_click=lambda: parseReference(risRef)
  )

def checkAuthors() :
  print("----------------------------------------")
  authors = globalUI['authors']
  if authors :
    for anAuthor, aSelector in authors.items() :
      print(anAuthor)
      print(aSelector.value)
  tabs.set_value('Required fields')

def setupConfirmAuthors() :
  globalUI['authors'] = None
  with ui.row():
    with ui.card().classes('w-full').props('rows=25') :
      globalUI['confirm'] = ui.scroll_area()
  ui.button(
    'Review required fields',
    on_click=lambda: checkAuthors()
  )

def setupRequiredFields() :
  globalUI['reqFields'] = ui.textarea(
    label='Required fields',
    placeholder='Update required fields here...'
  ).props("outlined rows=25").classes('w-full')
  ui.button(
    'Review optional fields',
    on_click=lambda: tabs.set_value('Optional fields')
  )

def setupOptionalFields() :
  globalUI['optFields'] = ui.textarea(
    label='Optional fields',
    placeholder='Update optional fields here...'
  ).props("outlined rows=25").classes('w-full')
  ui.button(
    'Review citation ID and save',
    on_click=lambda: tabs.set_value('Save reference')
  )

def saveReference() :
  pass

def setupSave() :
  globalUI['citeId'] = ui.input(
    label='Citation ID',
    placeholder='Update citation id here...'
  ).props("outlined").classes('w-full')
  globalUI['pdfUrl'] = ui.input(
    label='PDF url',
    placeholder='Add a valid url for the PDF',
  )
  globalUI['pdfType'] = ui.select([
    'owned', 'public', 'unknown'
  ], value='public')
  ui.button(
    'Save reference',
    on_click=lambda: saveReference()
  )

with ui.header().classes(replace='row items-center') as header:
  with ui.tabs() as tabs:
    ui.tab('RIS types')
    ui.tab('RIS entry')
    ui.tab('Confirm authors')
    ui.tab('Required fields')
    ui.tab('Optional fields')
    ui.tab('Save reference')

with ui.tab_panels(tabs, value='RIS entry').classes('w-full'):
  with ui.tab_panel('RIS types') :
    setupRisTypes()
  with ui.tab_panel('RIS entry'):
    setupRisEntry()
  with ui.tab_panel('Confirm authors'):
    setupConfirmAuthors()
  with ui.tab_panel('Required fields'):
    setupRequiredFields()
  with ui.tab_panel('Optional fields'):
    setupOptionalFields()
  with ui.tab_panel('Save reference') :
    setupSave()

ui.run(
  title='Citation Manager Capture reference',
  reload=True
)
