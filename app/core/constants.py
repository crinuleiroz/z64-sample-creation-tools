from pathlib import Path


PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
OUT_FOLDER: Path = PROJECT_ROOT / 'output'
GUI_FILE: Path = PROJECT_ROOT / 'gui.pyw'