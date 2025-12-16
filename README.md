# ARC Software

Simple quoting / RFQ utility built with Tkinter.

Quick notes (recent changes):

- **Default window size:** 1000x700 (constants `DEFAULT_WIDTH` / `DEFAULT_HEIGHT` in `arcsoftware.py`).
- **App title:** configured via `APP_TITLE` in `arcsoftware.py`.
- **Persistence:** quotes are stored in `data/quotes.json` (helper functions `load_quotes` / `save_quotes`).
- **UI:** macOS-like dark-themed toolbar, PO# entry on the toolbar, notes area, and modern fonts.
- **Export/Import:** per-quote JSON export/import from the Load dialog; PDF export uses ReportLab when available, with an HTML fallback that opens in the browser.
- **Exit behavior:** app will prompt to save the current quote on exit.

How to customize:

- Change the default window size by editing `DEFAULT_WIDTH` / `DEFAULT_HEIGHT` in `arcsoftware.py`.
- Update `APP_TITLE` or `VERSION` at the top of `arcsoftware.py` to reflect branding/versioning.

If you want, I can add a README section describing other developer notes (tests, CI, or packaging).

## Developer Notes 🔧

- Run the app: `python3 arcsoftware.py` (requires Python 3.8+).
- Optional dependencies:
	- `Pillow` — improves icon loading and resizing
	- `reportlab` — used for direct PDF export (fallback: HTML opened in browser)
	- `pytest` — only needed if adding unit tests
	Install with: `pip3 install pillow reportlab pytest`
- Important files:
	- `arcsoftware.py` — main application (UI, persistence, export/import)
	- `data/quotes.json` — persistent store for saved quotes (created on first save)
	- `data/employees.json` — default employee list used for seeding
- Key configuration constants in `arcsoftware.py`:
	- `DEFAULT_WIDTH` / `DEFAULT_HEIGHT` — default window size
	- `APP_TITLE`, `VERSION` — app metadata
	- `QUOTES_FILE` — path to the persistent JSON file
- Export and Import:
	- Use the **Load Quote** dialog to Export a single quote to JSON or Import a previously exported quote.
	- Export to PDF uses ReportLab when present, otherwise writes HTML to a temp file and opens it in the browser for printing.
- Tests & CI:
	- There are no automated tests or CI workflows included by default. Add `tests/` with `pytest` tests and a GitHub Actions workflow under `.github/workflows/` if you want CI.

If you'd like, I can add a `requirements.txt` or a `pyproject.toml` entry for these optional dev dependencies.

## macOS Build (PyInstaller)

When building a macOS GUI app with PyInstaller, build on macOS and include your `data/` folder and an `.icns` icon.

Recommended command:

```bash
pyinstaller --onefile --noconsole --icon=data/app.icns --add-data "data:./data" arcsoftware.py
```

Notes:
- Use `:` as the `--add-data` separator on macOS/Linux. The `--icon` for macOS should be an `.icns` file.
- The app should use a `resource_path()` helper (already in `arcsoftware.py`) so bundled resources are located via `sys._MEIPASS` at runtime.

Convert a PNG to `.icns` on macOS:

```bash
# prepare a 1024x1024 PNG named icon.png
mkdir MyIcon.iconset
sips -z 16 16 icon.png --out MyIcon.iconset/icon_16x16.png
sips -z 32 32 icon.png --out MyIcon.iconset/icon_16x16@2x.png
sips -z 32 32 icon.png --out MyIcon.iconset/icon_32x32.png
sips -z 64 64 icon.png --out MyIcon.iconset/icon_32x32@2x.png
sips -z 128 128 icon.png --out MyIcon.iconset/icon_128x128.png
sips -z 256 256 icon.png --out MyIcon.iconset/icon_128x128@2x.png
sips -z 256 256 icon.png --out MyIcon.iconset/icon_256x256.png
sips -z 512 512 icon.png --out MyIcon.iconset/icon_256x256@2x.png
sips -z 512 512 icon.png --out MyIcon.iconset/icon_512x512.png
sips -z 1024 1024 icon.png --out MyIcon.iconset/icon_512x512@2x.png
iconutil -c icns MyIcon.iconset -o data/app.icns
```

If you prefer a non-onefile build for easier debugging of bundled resources, omit `--onefile`.

## Features ✅

- Add / edit / delete parts for a quote (part number, description, qty, unit cost, list price, source)
- Save and load quotes to `data/quotes.json`
- Export single quotes to JSON for sharing or backup
- Export to PDF (uses `reportlab` when available, otherwise opens an HTML print view)
- PO# field in the toolbar, notes area, and simple totals calculation
- macOS-friendly, dark-themed toolbar and modern fonts

## Quick Start 🚀

1. Ensure Python 3.8+ is installed.
2. (Optional) Install dev dependencies: `pip3 install pillow reportlab pytest`
3. Run the app: `python3 arcsoftware.py`
4. Create a new quote, add parts, and use **Save Quote** to persist it to `data/quotes.json`.
5. Use **Load Quote** to load, export (JSON), or import a single quote.

## Keyboard Shortcuts ⌨️

- Ctrl+Q — Exit the app (prompts to save current quote)

## Troubleshooting ⚠️

- If icons don't appear correctly on macOS, install `Pillow` to improve icon handling (`pip3 install pillow`).
- If PDF export does not work, either install `reportlab` or print via the browser when the HTML fallback opens.
- If the app fails to start, run `python3 -m py_compile arcsoftware.py` to check for syntax errors.

## Contributing 🤝

- Feel free to open issues or PRs if you want features or bug fixes. Keep changes small and focused.
- If you add tests, use `pytest` and consider adding a simple GitHub Actions workflow for CI (optional).
 
**Note:** Please do **not** commit local data files (for example `data/quotes.json`) — user data is ignored via `.gitignore`.

