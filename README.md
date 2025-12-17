# ARCS

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/) [![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-brightgreen)]() [![Status](https://img.shields.io/badge/Status-Beta-yellow)]() [![UI](https://img.shields.io/badge/UI-Tkinter-orange)]()

Lightweight RFQ/quoting app built with Tkinter. Add parts, set PO#, save/load quotes as JSON, and export printable PDFs.

Quick start 🚀

End user (recommended)

- Run a packaged release executable (preferred):
  - macOS: open the built app from `dist/` or run `./dist/ARCS` after building
  - Windows: run `dist\ARCS.exe`
- Build using the helper scripts if you need to create a packaged app:
  - macOS: `./macOSBuild`
  - Windows: `windowsBuild.bat`

Developer / contributor (optional)

1. Install Python 3.8+.
2. pip3 install -r requirements.txt
3. (Dev only) Run: `python3 arcs.py`

Core features ✨

- Add/edit/delete parts (part #, description, qty, unit cost, list price, source)
- Save/load quotes to `data/quotes.json` (user data stored in `~/.arcsoftware/quotes.json` when packaged)
- Export/import single quotes (JSON) and export printable PDF (ReportLab or HTML fallback)
- PO# toolbar, notes area, and totals

Build notes 🛠️

Use the included helper scripts to build distributables:

- macOS: run `./macOSBuild` (on macOS; script wraps PyInstaller and includes the data assets)
- Windows: run `windowsBuild.bat` (on Windows; script wraps PyInstaller and includes the data assets)

If you prefer to run PyInstaller manually, consult the PyInstaller docs — the helper scripts show a recommended configuration.
Developer notes 🔧

- Main module: `arcs.py` (replaced `arcsoftware.py`). Build scripts and spec updated.
- Use `resource_path()` in the code to locate bundled resources under PyInstaller (`sys._MEIPASS`).
- Linting: repo uses `flake8` (max line length 120). Auto-formatting with `black` is used.


