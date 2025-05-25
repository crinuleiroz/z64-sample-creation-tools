# Zelda64 Sample Creation Tools
Creates an APDCM file compatible with Zelda64 and a SEQ64 XML instrument bank using a WAV file and z64audio.

## 🔧 How To Use
To use this script, follow the steps below:

> 1. Place the following files/folders in the same directory:
>      - `💻 z64audio.exe` — the executable used to convert the WAV file to an ADPCM file
>      - `📄 WAV to ZSOUND.py` — the main script
>      - `📁/utils` — the folder containing utility scripts
> 2. Run `Install Requirements to VENV.bat` to install the requirements from `requirements.txt` into a virtual environment.
> 3. Drag and drop any number of WAV files or folders onto `WAV to ZSOUND.py`

That's it — there should now be folders containing the ADPCM binary file (`.zsound`) and a SEQ64 XML instrument bank in a folder with the input file or folder's name!

> [!IMPORTANT]
> If an audio sample does not have a root note of 60, the script will attempt to automatically detect its pitch using the fast fourier transform algorithm. This will hopefully avoid any shenanigans with Polyphone incorrectly assigning the MIDI unity note to an audio sample. This comes at the requirements of third-party libraries Numpy and Scipy. You can install the requirements ot a VENV using the batch script, which the script will then use. If it can't import the required modules for whatever reason, it will fallback to using the WAV file's MIDI unity note.

## 🎶 Multi-Sample Instrument Banks
This script allows for the creation of multi-sample instruments. To create a multi-sample instrument, place all the WAV files you want to be apart of the instrument into a folder, then drag the folder onto the script.

> [!NOTE]
> There is functionality for bulk converting entire folders. However, it requires more than 3 audio samples to be present in the folder — and it will search the folder recursively. If there are 3 or less audio samples in the folder, it will treat them as a single multi-sample instrument. Use caution when bulk converting, because that is the only check the script makes to convert folders and create multi-sample instruments.

## 📝 Credits
[z64audio](https://github.com/z64tools/z64audio) — "Somewhat flexible audio converter" from z64tools
