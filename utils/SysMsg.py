# Utility script for WAV to ZSOUND.py
import os

# Last updated
LAST_UPDATED = '2025.03.13'

# Create ANSI formatting for terminal messages
# ANSI COLORS: https://talyian.github.io/ansicolors/
RESET  = "\x1b[0m"
BLUE   = "\x1b[38;5;14m"
PINK   = "\x1b[38;5;218m"
GREEN  = "\x1b[38;5;115m"
GREY   = "\x1b[38;5;8m"
YELLOW = "\x1b[33m"

class SystemMessages:
  """
  System messages that get printed to the terminal.
  """
  @staticmethod
  def header():
    print(f'''\
{GREY}[▪]-----------------------------[▪]
 |   {RESET}{PINK}WAV to ZSOUND {GREY}v{LAST_UPDATED}   |
[▪]-----------------------------[▪]{RESET}
''')

  @staticmethod
  def processing_folder(file):
    print(f'''\
{GREY}[{PINK}>{GREY}]:{RESET} Processing samples in folder: {BLUE}"{file}"{RESET}
''')

  @staticmethod
  def processing_multi(file):
    print(f'''\
{GREY}[{PINK}>{GREY}]:{RESET} Processing multi-sample instrument in folder: {BLUE}"{file}"{RESET}
''')

  @staticmethod
  def processing_file(file):
    print(f'''\
{GREY}[{PINK}>{GREY}]:{RESET} Processing sample          {BLUE}"{file}"{RESET}''')

  @staticmethod
  def existing_folder(outfolder):
    print(f'''\
{GREY}[{PINK}>{GREY}]:{RESET} Folder already exists      {BLUE}"{outfolder}"{RESET}
''')

  @staticmethod
  def existing_file(file):
    print(f'''\
{GREY}[{PINK}>{GREY}]:{RESET} Sample already exists      {BLUE}"{file}"{RESET}
''')

  @staticmethod
  def handle_non_wav_file():
    print(f'''\
{GREY}[{PINK}>{GREY}]:{RESET} File is not a .wav file!
''')

  @staticmethod
  def z64audio_start(filepath, filename):
    print(f'''\
{GREY}[{PINK}>{GREY}]:{RESET} Initiating z64audio        {YELLOW}z64audio {GREY}-i {BLUE}"{os.path.basename(filepath)}" {GREY}-o {BLUE}"{filename}.bin" {GREY}-I {RESET}50''')

  @staticmethod
  def renaming_sample(bin_file):
    print(f'''\
{GREY}[{PINK}>{GREY}]:{RESET} Renaming sample            {BLUE}"{bin_file}"{RESET}''')

  @staticmethod
  def converting_predictors(codebook, loopbook=None):
    if loopbook:
      print(f'''\
{GREY}[{PINK}>{GREY}]:{RESET} Converting codebooks       {BLUE}"{codebook}"{RESET}
{GREY}[{PINK}>{GREY}]:{RESET} Converting loopbooks       {BLUE}"{loopbook}"{RESET}''')
    else:
      print(f'''\
{GREY}[{PINK}>{GREY}]:{RESET} Converting codebooks       {BLUE}"{codebook}"{RESET}''')

  @staticmethod
  def writing_xml_bank(filename):
    print(f'''\
{GREY}[{PINK}>{GREY}]:{RESET} Writing XML bank           {BLUE}"{filename}_BANK.xml"{RESET}''')

  @staticmethod
  def moving_files(outfolder):
    print(f'''\
{GREY}[{PINK}>{GREY}]:{RESET} Moving files to out        {BLUE}"{outfolder}"{RESET}''')

  @staticmethod
  def sample_processed():
    print(f'''\
{GREY}[{PINK}>{GREY}]:{RESET} Sample processed
''')

  @staticmethod
  def multi_sample_processed(basefolder):
    print(f'''\

{GREY}[{PINK}>{GREY}]:{RESET} Multi-sample instrument processed and moved to folder: {BLUE}"{basefolder}"{RESET}
''')

  @staticmethod
  def completion():
    print(f'''\
{GREY}[▪]-----------------------------[▪]
 |   {RESET}{GREEN}Process is now completed    {GREY}|
[▪]-----------------------------[▪]{RESET}
''')

if __name__ == '__main__':
  print('This is a utility script meant to be used with the WAV to ZSOUND main script. On its own it has no functionality.')