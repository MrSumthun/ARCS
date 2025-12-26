import json
import os
import tempfile
import datetime
import webbrowser
import logging

from PyQt6 import QtGui, QtWidgets
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

from arcs_utils import (
    get_resource_path,
    user_data_dir,
    load_json_file,
    save_json_file,
    create_quote,
    normalize_quote_name,
    safe_filename,
)

# Le constants
# Mr_SuMtHuN 2025
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
VERSION = "v1.0.6-Beta"
APP_NAME = "ARCS"
APP_TITLE = "ARCS Quote Manager"
MAIN_WINDOW_X = 1400
MAIN_WINDOW_Y = 780

UI_BG = "#0b1220"
TOOLBAR_BG = "#590101"
PANEL_BG = "#000000"
ALT_PANEL_BG = "#12233a"
FG = "#ffffff"
ACCENT = "#590101"
ACCENT2 = "#ffffff"
ACCENT3 = "#ffffff"

BUNDLED_QUOTES_FILE = get_resource_path(os.path.join("data", "quotes.json"))
APP_ICON = get_resource_path(os.path.join("data", "app.ico"))
APP_ICNS = get_resource_path(os.path.join("data", "app.icns"))
QUOTES_FILE = os.path.join(user_data_dir(), "quotes.json")
LOG_FILE = os.path.join(user_data_dir(), "arcsoftware.log")
logger = logging.getLogger("arcsoftware")


if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)


def load_quotes():
    try:
        data = load_json_file(QUOTES_FILE)
        logger.debug("Loaded %d quotes from %s", len(data), QUOTES_FILE)
        if data:
            return data
    except Exception:
        logger.debug("Failed to load user quotes from %s", QUOTES_FILE, exc_info=True)

    data = load_json_file(BUNDLED_QUOTES_FILE)
    logger.debug("Loaded %d bundled quotes from %s", len(data), BUNDLED_QUOTES_FILE)
    return data or []


def load_pixmap(path: str) -> "QtGui.QPixmap | None":
    if not path or not os.path.exists(path):
        return None

    iconPixMap = QtGui.QPixmap(path)
    return iconPixMap if not iconPixMap.isNull() else None


def save_quotes(quotes):
    try:
        save_json_file(QUOTES_FILE, quotes)
        logger.info("Saved %d quotes to %s", len(quotes), QUOTES_FILE)
    except Exception:
        logger.exception("Failed to save quotes to %s", QUOTES_FILE)


class AddEditPartDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, item=None):
        super().__init__(parent)
        self.setWindowTitle("Add Part" if item is None else "Edit Part")
        self.setModal(True)
        layout = QtWidgets.QFormLayout(self)

        self.part_edit = QtWidgets.QLineEdit()
        self.part_edit.setMinimumWidth(280)
        self.part_edit.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self.desc_edit = QtWidgets.QLineEdit()
        self.desc_edit.setMinimumWidth(420)
        self.desc_edit.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self.qty_spin = QtWidgets.QSpinBox()
        self.qty_spin.setMinimum(1)
        self.qty_spin.setMaximum(10_000_000)
        self.unit_spin = QtWidgets.QDoubleSpinBox()
        self.unit_spin.setMaximum(10_000_000.0)
        self.unit_spin.setDecimals(2)
        self.list_spin = QtWidgets.QDoubleSpinBox()
        self.list_spin.setMaximum(10_000_000.0)
        self.list_spin.setDecimals(2)
        self.margin_label = QtWidgets.QLabel("N/A")
        self.source_edit = QtWidgets.QLineEdit()
        self.tax_exempt_cb = QtWidgets.QCheckBox("Tax Exempt (Supplier)")
        self.tax_exempt_cb.setChecked(False)
        self._editing_item = bool(item)
        self.source_edit.textChanged.connect(self._source_changed)

        layout.addRow("Part #", self.part_edit)
        layout.addRow("Description", self.desc_edit)
        layout.addRow("Qty", self.qty_spin)
        layout.addRow("Unit Cost", self.unit_spin)
        layout.addRow("List Price", self.list_spin)
        layout.addRow("Margin %", self.margin_label)
        layout.addRow("Source", self.source_edit)
        layout.addRow("Tax Exempt", self.tax_exempt_cb)

        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)

        self.unit_spin.valueChanged.connect(self.update_margin)
        self.list_spin.valueChanged.connect(self.update_margin)

        if item:
            self.part_edit.setText(item.get("part_number", ""))
            self.desc_edit.setText(item.get("description", ""))
            self.qty_spin.setValue(int(item.get("quantity", 1)))
            self.unit_spin.setValue(float(item.get("unit_cost", 0.0)))
            self.list_spin.setValue(float(item.get("list_price", 0.0)))
            self.source_edit.setText(item.get("source", ""))
            self.tax_exempt_cb.setChecked(bool(item.get("tax_exempt", False)))
            self.update_margin()

    def _source_changed(self, txt: str):
        if self._editing_item:
            return
        try:
            parent = self.parent()
            if not parent:
                return
            q = (
                getattr(parent, "current", {}).get("quote")
                if getattr(parent, "current", None)
                else None
            )
            if not q:
                return
            suppliers = q.get("suppliers", {})
            s = txt.strip() or "<unknown>"
            if s in suppliers:
                self.tax_exempt_cb.setChecked(
                    bool(suppliers.get(s, {}).get("tax_exempt", False))
                )
        except Exception:
            pass

    def get_data(self):
        return {
            "part_number": self.part_edit.text().strip(),
            "description": self.desc_edit.text().strip(),
            "quantity": int(self.qty_spin.value()),
            "unit_cost": float(self.unit_spin.value()),
            "list_price": float(self.list_spin.value()),
            "source": self.source_edit.text().strip(),
            "tax_exempt": bool(self.tax_exempt_cb.isChecked()),
            "line_total": round(
                int(self.qty_spin.value()) * float(self.unit_spin.value()), 2
            ),
        }

    def update_margin(self):
        try:
            cost = float(self.unit_spin.value())
            lst = float(self.list_spin.value())
            if lst == 0.0:
                if cost == 0.0:
                    self.margin_label.setText("0.00%")
                else:
                    self.margin_label.setText("N/A")
                return
            margin = ((lst - cost) / lst) * 100.0
            self.margin_label.setText(f"{margin:.2f}%")
        except Exception:
            self.margin_label.setText("N/A")


class LoadQuoteDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, quotes=None):
        super().__init__(parent)
        self.setWindowTitle("Load Quote")
        self.setModal(True)
        self.selected = None
        self.quotes = quotes or []
        layout = QtWidgets.QVBoxLayout(self)

        self.list_widget = QtWidgets.QListWidget()
        for quote_item in self.quotes:
            po = quote_item.get("po_number")
            po_str = f" [PO:{po}]" if po else ""
            label = f"{quote_item.get('name')}{po_str} ({len(quote_item.get('items', []))} items)"
            item = QtWidgets.QListWidgetItem(label)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        btn_layout = QtWidgets.QHBoxLayout()
        self.load_btn = QtWidgets.QPushButton("Load")
        self.delete_button = QtWidgets.QPushButton("Delete")
        self.export_button = QtWidgets.QPushButton("Export")
        self.import_button = QtWidgets.QPushButton("Import")
        btn_layout.addWidget(self.export_button)
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.delete_button)
        btn_layout.addWidget(self.import_button)
        btn_layout.addStretch()
        self.close_btn = QtWidgets.QPushButton("Close")
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

        self.load_btn.clicked.connect(self._load)
        self.delete_button.clicked.connect(self._delete)
        self.export_button.clicked.connect(self._export)
        self.import_button.clicked.connect(self._import)
        self.close_btn.clicked.connect(self.close)

    def _load(self):
        sel = self.list_widget.currentRow()
        if sel < 0:
            return
        self.selected = self.quotes[sel]
        self.accept()

    def _delete(self):
        sel = self.list_widget.currentRow()
        if sel < 0:
            QtWidgets.QMessageBox.information(
                self, "Delete Quote", "No quote selected."
            )
            return
        q = self.quotes[sel]
        if not QtWidgets.QMessageBox.question(
            self, "Delete Quote", f"Delete quote '{q.get('name')}'?"
        ):
            return
        del self.quotes[sel]
        try:
            save_quotes(self.quotes)
            self.list_widget.takeItem(sel)
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Delete Quote", f"Failed to delete quote: {e}"
            )

    def _export(self):
        sel = self.list_widget.currentRow()
        if sel < 0:
            QtWidgets.QMessageBox.information(
                self, "Export Quote", "No quote selected."
            )
            return
        q = self.quotes[sel]
        suggested = safe_filename(normalize_quote_name(q))
        fn, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Quote",
            f"{suggested}.json",
            "JSON files (*.json);;All Files (*)",
        )
        if not fn:
            return
        try:
            with open(fn, "w") as f:
                json.dump(q, f, indent=4, default=str)
            QtWidgets.QMessageBox.information(
                self, "Export Quote", f"Quote exported to {fn}"
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Export Quote", f"Failed to export: {e}"
            )

    def _import(self):
        fn, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import Quote", "", "JSON files (*.json);;All Files (*)"
        )
        if not fn:
            return
        try:
            with open(fn, "r") as f:
                payload = json.load(f)
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Import Quote", f"Failed to read file: {e}"
            )
            return
        if not isinstance(payload, dict) or "items" not in payload:
            QtWidgets.QMessageBox.critical(
                self, "Import Quote", "File does not appear to be a valid quote JSON."
            )
            return
        existing_ids = {x.get("id") for x in self.quotes}
        if payload.get("id") in existing_ids:
            payload["id"] = int(
                datetime.datetime.now(datetime.timezone.utc).timestamp()
            )
        try:
            payload["name"] = normalize_quote_name(payload)
        except Exception:
            logger.debug(
                "Failed to normalize imported quote name for id=%s", payload.get("id")
            )
        self.quotes.append(payload)
        save_quotes(self.quotes)
        po = payload.get("po_number")
        po_str = f" [PO:{po}]" if po else ""
        label = f"{payload.get('name')}{po_str} ({len(payload.get('items', []))} items)"
        self.list_widget.addItem(label)
        QtWidgets.QMessageBox.information(
            self, "Import Quote", f"Imported quote '{payload.get('name')}'"
        )


class SuppliersDialog(QtWidgets.QDialog):
    """Dialog for managing supplier-level settings (e.g., tax exempt)."""

    def __init__(self, parent=None, suppliers=None, existing=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Suppliers")
        self.setModal(True)
        self.suppliers = suppliers or []
        self.existing = existing or {}
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        self._checks: dict[str, QtWidgets.QCheckBox] = {}
        for s in sorted(self.suppliers):
            cb = QtWidgets.QCheckBox("Tax Exempt")
            cb.setChecked(bool(self.existing.get(s, {}).get("tax_exempt", False)))
            form.addRow(s, cb)
            self._checks[s] = cb
        layout.addLayout(form)
        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_mapping(self):
        """Return a mapping of supplier->tax_exempt bool."""
        return {s: bool(cb.isChecked()) for s, cb in self._checks.items()}


class ArcsWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(MAIN_WINDOW_X, MAIN_WINDOW_Y)

        try:
            pix = (
                load_pixmap(APP_ICON) if APP_ICON and os.path.exists(APP_ICON) else None
            )
            if pix is not None and not pix.isNull():
                self.setWindowIcon(QtGui.QIcon(pix))
            else:
                if APP_ICON and os.path.exists(APP_ICON):
                    qicon = QtGui.QIcon(APP_ICON)
                    if not qicon.isNull():
                        self.setWindowIcon(qicon)
        except Exception:
            logger.debug("Failed to set window icon", exc_info=True)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)

        self.toolbar = QtWidgets.QToolBar()
        self.addToolBar(self.toolbar)
        self.toolbar.setMovable(False)
        self.toolbar.setStyleSheet("QToolBar { padding: 4px 6px; }")

        try:
            if hasattr(self, "windowIcon") and not self.windowIcon().isNull():
                pix = self.windowIcon().pixmap(18, 18)
                if pix and not pix.isNull():
                    brand_lbl = QtWidgets.QLabel()
                    brand_lbl.setPixmap(pix)
                    brand_lbl.setContentsMargins(6, 8, 8, 6)
                    first_action = (
                        self.toolbar.actions()[0] if self.toolbar.actions() else None
                    )
                    if first_action:
                        self.toolbar.insertWidget(first_action, brand_lbl)
                    else:
                        self.toolbar.addWidget(brand_lbl)
                    self._brand_label = brand_lbl
        except Exception:
            logger.debug("Failed to add toolbar brand icon", exc_info=True)

        self.btn_new = QtGui.QAction("New Quote", self)
        self.btn_add = QtGui.QAction("Add Part", self)
        self.btn_edit = QtGui.QAction("Edit Item", self)
        self.btn_del = QtGui.QAction("Delete Item", self)
        self.btn_save = QtGui.QAction("Save Quote", self)
        self.btn_load = QtGui.QAction("Load Quote", self)
        self.btn_suppliers = QtGui.QAction("Suppliers", self)
        self.btn_pdf = QtGui.QAction("Export PDF", self)
        self.btn_exit = QtGui.QAction("Exit", self)

        # We hate tooltips, this removes them. AS THEY SHOULD BE.
        for act in [
            self.btn_new,
            self.btn_add,
            self.btn_edit,
            self.btn_del,
            self.btn_save,
            self.btn_load,
            self.btn_suppliers,
            self.btn_pdf,
            self.btn_exit,
        ]:
            act.setToolTip("")
            act.setStatusTip("")
        for act in [
            self.btn_new,
            self.btn_add,
            self.btn_edit,
            self.btn_del,
            self.btn_save,
            self.btn_load,
            self.btn_suppliers,
        ]:
            self.toolbar.addAction(act)
        # Connect suppliers handler
        self.btn_suppliers.triggered.connect(self.manage_suppliers)

        self.toolbar.addSeparator()
        ver_lbl = QtWidgets.QLabel(VERSION)
        ver_lbl.setStyleSheet("margin-left: 8px;")
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        self.toolbar.addWidget(spacer)
        self.toolbar.addWidget(ver_lbl)
        self.po_edit = QtWidgets.QLineEdit()
        self.po_edit.setPlaceholderText("PO#")
        self.toolbar.addWidget(self.po_edit)
        self.table = QtWidgets.QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            [
                "Part #",
                "Description",
                "Qty",
                "Unit Cost",
                "List Price",
                "Source",
                "Line Total",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        # Alternating row colors and a compact look
        self.table.setAlternatingRowColors(True)
        palette = self.table.palette()
        palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(PANEL_BG))
        palette.setColor(
            QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(ALT_PANEL_BG)
        )
        palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(FG))
        self.table.setPalette(palette)

        main_layout.addWidget(self.table)

        # total and notes
        bottom_layout = QtWidgets.QHBoxLayout()
        self.lbl_total = QtWidgets.QLabel("Total: $0.00")
        bottom_layout.addWidget(self.lbl_total)
        bottom_layout.addStretch()
        main_layout.addLayout(bottom_layout)

        self.notes = QtWidgets.QTextEdit()
        self.notes.setPlaceholderText("Notes...")
        self.notes.setFixedHeight(140)
        main_layout.addWidget(self.notes)

        # Connect actions
        self.btn_new.triggered.connect(self.new_quote)
        self.btn_add.triggered.connect(self.add_part)
        self.btn_edit.triggered.connect(self.edit_item)
        self.btn_del.triggered.connect(self.delete_item)
        self.btn_save.triggered.connect(self.save_current)
        self.btn_load.triggered.connect(self.load_quote)
        self.btn_pdf.triggered.connect(self.export_pdf)
        self.btn_exit.triggered.connect(self.close)

        self.toolbar.addAction(self.btn_pdf)
        self.toolbar.addAction(self.btn_exit)

        self.table.doubleClicked.connect(self._on_table_double)

        self.current = {"quote": None}
        self.quotes = load_quotes()

        if self.quotes:
            quotes_sorted = sorted(
                self.quotes, key=lambda x: x.get("created_at") or "", reverse=True
            )
            self.set_current_quote(quotes_sorted[0])

    def set_current_quote(self, q):
        self.current["quote"] = q
        self.update_table()
        self.update_totals()
        self.po_edit.setText(q.get("po_number", ""))
        self.notes.setPlainText(q.get("notes", ""))

    def clear_current(self):
        self.current["quote"] = None
        self.update_table()
        self.update_totals()
        self.po_edit.clear()
        self.notes.clear()

    def new_quote(self):
        q = create_quote()
        self.set_current_quote(q)

    def add_part(self):
        if self.current.get("quote") is None:
            self.new_quote()
        dlg = AddEditPartDialog(self)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            item = dlg.get_data()
            self.current["quote"]["items"].append(item)
            self.update_table()
            self.update_totals()

    def manage_suppliers(self):
        # I'll be frank, this part is totally AI generated. Couldn't figure it out. :)
        q = self.current.get("quote")
        if not q:
            QtWidgets.QMessageBox.information(self, "Suppliers", "No current quote.")
            return
        # Aggregate supplier names from items
        suppliers = sorted(
            {(it.get("source") or "<unknown>").strip() for it in q.get("items", [])}
        )
        existing = q.get("suppliers", {}) or {}
        supp_dialog = SuppliersDialog(self, suppliers=suppliers, existing=existing)
        if supp_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            mapping = supp_dialog.get_mapping()
            q["suppliers"] = {s: {"tax_exempt": bool(v)} for s, v in mapping.items()}
            for it in q.get("items", []):
                src = (it.get("source") or "").strip()
                if not src:
                    src = "<unknown>"
                it["tax_exempt"] = bool(mapping.get(src, False))
            self.update_table()
            # Optionally auto-save silently to persist supplier choices
            try:
                self.save_current(silent=True)
            except Exception:
                pass

    def update_table(self):
        q = self.current.get("quote")
        self.table.setRowCount(0)
        if not q:
            return
        for idx, it in enumerate(q.get("items", [])):
            self.table.insertRow(self.table.rowCount())
            self.table.setItem(
                idx, 0, QtWidgets.QTableWidgetItem(it.get("part_number") or "")
            )
            self.table.setItem(
                idx, 1, QtWidgets.QTableWidgetItem(it.get("description") or "")
            )
            self.table.setItem(
                idx, 2, QtWidgets.QTableWidgetItem(str(it.get("quantity") or ""))
            )
            self.table.setItem(
                idx,
                3,
                QtWidgets.QTableWidgetItem(f"{(it.get('unit_cost') or 0.0):.2f}"),
            )
            self.table.setItem(
                idx,
                4,
                QtWidgets.QTableWidgetItem(f"{(it.get('list_price') or 0.0):.2f}"),
            )
            src_val = it.get("source") or ""
            if it.get("tax_exempt"):
                src_val = f"{src_val} (Tax Exempt)"
            self.table.setItem(idx, 5, QtWidgets.QTableWidgetItem(src_val))
            self.table.setItem(
                idx,
                6,
                QtWidgets.QTableWidgetItem(f"{(it.get('line_total') or 0.0):.2f}"),
            )

    def update_totals(self):
        q = self.current.get("quote")
        if not q:
            self.lbl_total.setText("Total: $0.00")
            return
        total = sum(it.get("line_total", 0.0) for it in q.get("items", []))
        self.lbl_total.setText(f"Total: ${total:.2f}")

    def _selected_index(self):
        sels = self.table.selectionModel().selectedRows()
        if not sels:
            return None
        return sels[0].row()

    def delete_item(self):
        idx = self._selected_index()
        if idx is None:
            QtWidgets.QMessageBox.information(self, "Delete", "No item selected.")
            return
        if QtWidgets.QMessageBox.question(self, "Delete", "Remove selected item?"):
            q = self.current.get("quote")
            if q and 0 <= idx < len(q["items"]):
                q["items"].pop(idx)
                self.update_table()
                self.update_totals()

    def edit_item(self):
        idx = self._selected_index()
        if idx is None:
            QtWidgets.QMessageBox.information(self, "Edit", "No item selected.")
            return
        q = self.current.get("quote")
        if not q or not (0 <= idx < len(q["items"])):
            return
        it = q["items"][idx]
        dlg = AddEditPartDialog(self, item=it)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            q["items"][idx] = data
            self.update_table()
            self.update_totals()

    def _on_table_double(self, index):
        self.edit_item()

    def save_current(self, silent=False):
        q = self.current.get("quote")
        if not q:
            logger.debug("save_current called with no current quote")
            return
        q["notes"] = self.notes.toPlainText().rstrip("\n")
        q["po_number"] = self.po_edit.text().strip()
        quotes = load_quotes()
        existing = [x for x in quotes if x.get("id") == q.get("id")]
        if existing:
            quotes = [x for x in quotes if x.get("id") != q.get("id")]
        quotes.append(q)
        logger.info("Saving current quote id=%s name=%s", q.get("id"), q.get("name"))
        save_quotes(quotes)
        if not silent:
            QtWidgets.QMessageBox.information(self, "Save", "Quote saved.")

    def load_quote(self):
        quotes = load_quotes()
        if not quotes:
            QtWidgets.QMessageBox.information(
                self, "Load Quote", "No saved quotes found."
            )
            return
        dlg = LoadQuoteDialog(self, quotes=quotes)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            q = dlg.selected
            if q:
                self.set_current_quote(q)

    def export_pdf(self):
        q = self.current.get("quote")
        if not q:
            QtWidgets.QMessageBox.information(
                self, "Export", "No current quote to export."
            )
            return
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        c = canvas.Canvas(path, pagesize=letter)
        y = 750
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, y, APP_NAME)
        y -= 25
        c.setFont("Helvetica-Bold", 14)
        c.drawString(72, y, q.get("name"))
        y -= 30
        left = 72
        right = 72
        po = q.get("po_number")
        if po:
            c.setFont("Helvetica", 10)
            c.drawString(left, y, f"PO#: {po}")
            y -= 16

        available_width = letter[0] - left - right
        col_widths = [
            0.6 * inch,
            1.2 * inch,
            3.2 * inch,
            0.6 * inch,
            0.9 * inch,
            0.9 * inch,
        ]
        data = [["No", "Part", "Description", "Qty", "Unit", "Line"]]
        for idx, it in enumerate(q.get("items", []), start=1):
            data.append(
                [
                    str(idx),
                    it.get("part_number") or "",
                    it.get("description") or "",
                    str(it.get("quantity") or ""),
                    f"${(it.get('unit_cost') or 0.0):.2f}",
                    f"${(it.get('line_total') or 0.0):.2f}",
                ]
            )
        total = sum(it.get("line_total", 0.0) for it in q.get("items", []))
        data.append(["", "", "", "", "Total", f"${total:.2f}"])
        table = Table(data, colWidths=col_widths)
        table.repeatRows = 1
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (3, 1), (5, -2), "RIGHT"),
                    ("ALIGN", (4, -1), (5, -1), "RIGHT"),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ]
            )
        )
        w, h = table.wrapOn(c, available_width, y)
        if h > (y - 72):
            c.showPage()
            y = 750
            c.setFont("Helvetica-Bold", 16)
            c.drawString(left, y, APP_NAME)
            y -= 25
            c.setFont("Helvetica-Bold", 14)
            c.drawString(left, y, q.get("name"))
            y -= 30
            po = q.get("po_number")
            if po:
                c.setFont("Helvetica", 10)
                c.drawString(left, y, f"PO#: {po}")
                y -= 16
            w, h = table.wrapOn(c, available_width, y)
        table.drawOn(c, left, y - h)
        y = y - h - 12
        c.save()
        webbrowser.open("file://" + path)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        q = self.current.get("quote")
        if q:
            res = QtWidgets.QMessageBox.question(
                self,
                "Exit",
                "Save current quote before exiting?",
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No
                | QtWidgets.QMessageBox.StandardButton.Cancel,
            )
            if res == QtWidgets.QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            if res == QtWidgets.QMessageBox.StandardButton.Yes:
                self.save_current()
        event.accept()


def main():
    app = QtWidgets.QApplication([])
    stylesheet = get_app_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    pal = app.palette()
    pal.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(UI_BG))
    pal.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(PANEL_BG))
    pal.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(ALT_PANEL_BG))
    pal.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(FG))
    pal.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(ACCENT))
    pal.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor("#ffffff"))
    app.setPalette(pal)

    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_TITLE)

    try:
        import platform as _platform

        if _platform.system() == "Darwin" and APP_ICNS and os.path.exists(APP_ICNS):
            try:
                app.setWindowIcon(QtGui.QIcon(APP_ICNS))
            except Exception:
                logger.debug(
                    "Failed to set application icon on QApplication", exc_info=True
                )
    except Exception:
        logger.debug("Failed to determine platform for app icon", exc_info=True)

    win = ArcsWindow()
    win.show()
    app.exec()


def get_app_stylesheet() -> str:
    qss_path = get_resource_path(os.path.join("data", "style.qss"))
    try:
        with open(qss_path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except Exception:
        logger.debug("Style QSS not found or unreadable: %s", qss_path, exc_info=True)
        return ""

    try:
        fmt = {
            "UI_BG": UI_BG,
            "TOOLBAR_BG": TOOLBAR_BG,
            "PANEL_BG": PANEL_BG,
            "ALT_PANEL_BG": ALT_PANEL_BG,
            "FG": FG,
            "ACCENT": ACCENT,
            "ACCENT2": ACCENT2,
            "ACCENT3": ACCENT3,
        }
        for k, v in fmt.items():
            raw = raw.replace(f"{{{k}}}", v)
        return raw
    except Exception:
        logger.debug("Failed to format stylesheet with theme variables", exc_info=True)
        return ""


if __name__ == "__main__":
    main()
