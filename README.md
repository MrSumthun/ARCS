# ARCS

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/) [![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-brightgreen)]() [![Version](https://img.shields.io/badge/Version-1.1.0-purple)]() [![Status](https://img.shields.io/badge/Status-Beta-yellow)]() [![Qt](https://img.shields.io/badge/Qt-2CDE85?logo=Qt&logoColor=fff)](#)

Lightweight RFQ/quoting app built with PyQt6. Add parts, set PO#, save/load quotes as JSON, and export printable PDFs.

## Quick start

End user (recommended)

- Run a packaged release executable (preferred):
  - macOS: open the built app from `dist/` or run `./dist/ARCS` after building
  - Windows: run `dist\ARCS.exe`
- Build using the helper scripts if you need to create a packaged app:
  - macOS: `./buildtools/macOSBuild`
  - Windows: `./buildtools/windowsBuild.bat`

Developer / contributor (optional)

1. Install Python 3.8+.
2. pip3 install -r data/requirements.txt
3. (Dev only) Run: `python3 arcs.py`

Core features

- Add/edit/delete parts (part #, description, qty, unit cost, list price, source)
- Save/load quotes to `data/quotes.json` (user data stored in `~/.arcsoftware/quotes.json` when packaged)
- Export/import single quotes (JSON) and export printable PDF (ReportLab or HTML fallback)
- PO# toolbar, notes area, and totals

Developer notes

- Main module: `arcs.py`.
- Use `get_resource_path()` from `arcs_utils` to locate bundled resources under PyInstaller (`sys._MEIPASS`).
- Linting: repo uses `flake8` (max line length 120). Auto-formatting with `black` is recommended.
- Use `purchase_list.py` for CLI-based purchase lists.
