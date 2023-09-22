import click

from citationManager.capture import capture
from citationManager.scanner import scanner

@click.group()
def cli() :
  print("Hello world!")

cli.add_command(capture)
cli.add_command(scanner, name='scan')
