import json
import os
import tempfile
import datetime
import webbrowser
import logging
import tkinter as tk
import platform
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkfont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# Local helpers
from arcs_utils import (
    get_resource_path,
    user_data_dir,
    load_json_file,
    save_json_file,
    create_quote,
    normalize_quote_name,
    safe_filename,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

VERSION = "1.0.3-beta"
APP_NAME = "ARCS"
APP_TITLE = "ARCS Quote Manager"

# Default window size (can be customized)
DEFAULT_WIDTH = 1000
DEFAULT_HEIGHT = 700

# UI color scheme for dark mode
UI_BG = "#1f1f1f"  # main window background
TOOLBAR_BG = "#2a2a2a"  # toolbar background
PANEL_BG = "#141414"  # panels / tree background
FG = "#e8e8e8"  # primary foreground (text)
SELECT_BG = "#2b6fb6"  # selection color for rows

# Bundled resources (resolve with `get_resource_path` from `arcs_utils`)
BUNDLED_QUOTES_FILE = get_resource_path(os.path.join("data", "quotes.json"))
APP_ICON = get_resource_path(os.path.join("data", "app.ico"))
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


def save_quotes(quotes):
    try:
        save_json_file(QUOTES_FILE, quotes)
        logger.info("Saved %d quotes to %s", len(quotes), QUOTES_FILE)
    except Exception:
        logger.exception("Failed to save quotes to %s", QUOTES_FILE)


def _new_quote_template(name=None):
    return create_quote(name)


def format_quote_name(q):
    return normalize_quote_name(q)


def _safe_filename(name):
    return safe_filename(name)

# Center the window on the screen
def _center_window(root, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = int((screen_w - width) / 2)
    y = int((screen_h - height) / 2)
    root.geometry(f"{width}x{height}+{x}+{y}")


def build_ui():
    root = tk.Tk()
    root.title(APP_TITLE)
    bg_color = UI_BG
    root.configure(bg=bg_color)
    root.minsize(900, 600)
    _center_window(root, DEFAULT_WIDTH, DEFAULT_HEIGHT)
    # Try to set window icon if provided
    try:
        if APP_ICON and os.path.exists(APP_ICON):
            tried = False
            try:
                root.iconbitmap(APP_ICON)
                tried = True
            except Exception:
                logger.debug("iconbitmap failed for %s", APP_ICON)
                pass
            if not tried or platform.system() != "Windows":
                try:
                    _img = tk.PhotoImage(file=APP_ICON)
                    root.iconphoto(True, _img)
                    root._icon_img = _img
                except Exception:
                    try:
                        from PIL import Image, ImageTk

                        img = Image.open(APP_ICON)
                        imgtk = ImageTk.PhotoImage(img)
                        root.iconphoto(True, imgtk)
                        root._icon_img = imgtk
                    except Exception:
                        # ignore if neither method works; leaving default Tk icon
                        logger.debug("Failed to set iconphoto for %s", APP_ICON, exc_info=True)
                        pass
    except Exception:
        # ignore platforms that don't support icon changes or if setting fails
        logger.debug("Failed to set window icon for %s", APP_ICON, exc_info=True)
        pass

    # Main content area fills the window (no header)
    content = tk.Frame(root, bg=bg_color)
    content.place(relx=0, rely=0, relwidth=1, relheight=1)
    toolbar = tk.Frame(content, bg=TOOLBAR_BG)
    toolbar.place(relx=0.02, rely=0.02, relwidth=0.96, relheight=0.10)
    style = ttk.Style(root)

    if platform.system() == "Windows":
        base_family = "Segoe UI"
    else:
        base_family = "Helvetica"

    body_font = tkfont.Font(family=base_family, size=11)
    heading_font = tkfont.Font(family=base_family, size=11, weight="bold")
    button_font = tkfont.Font(family=base_family, size=10)

    try:
        style.theme_use("clam")
    except Exception:
        pass
    try:
        style.configure(
            "Treeview",
            background=PANEL_BG,
            fieldbackground=PANEL_BG,
            foreground=FG,
            rowheight=26,
            font=body_font,
        )
        style.configure(
            "Treeview.Heading", background=TOOLBAR_BG, foreground=FG, font=heading_font
        )
        style.map(
            "Treeview",
            background=[("selected", SELECT_BG), ("!selected", PANEL_BG)],
            foreground=[("selected", "#ffffff"), ("!selected", FG)],
        )
        style.map(
            "Treeview.Heading",
            background=[("active", TOOLBAR_BG), ("!active", TOOLBAR_BG)],
            foreground=[("active", FG), ("!active", FG)],
        )

        style.configure(
            "TButton",
            background=TOOLBAR_BG,
            foreground=FG,
            font=button_font,
            padding=(6, 4),
        )
        style.map("TButton", background=[("active", "#3a3a3a")])

        style.configure(
            "TEntry", fieldbackground=PANEL_BG, foreground=FG, font=body_font
        )
        style.configure("TLabel", background=UI_BG, foreground=FG, font=body_font)
    except Exception:
        logger.debug("Failed to configure ttk styles", exc_info=True)
        pass

    po_entry_var = tk.StringVar()

    current = {"quote": None}

    def set_current_quote(q):
        current["quote"] = q
        update_tree()
        update_totals()
        po_entry_var.set(q.get("po_number", ""))
        _load_notes_for_quote(q)

    def clear_current():
        current["quote"] = None
        update_tree()
        update_totals()
        po_entry_var.set("")
        notes_text.delete("1.0", "end")

    def new_quote():
        quoteTemplate = _new_quote_template()
        set_current_quote(quoteTemplate)
        po_entry_var.set("")
        # clear notes area
        notes_text.delete("1.0", "end")

    def add_part():
        if current["quote"] is None:
            new_quote()

        def _submit():
            pn = ent_part.get().strip()
            desc = ent_desc.get().strip()
            try:
                qty = int(ent_qty.get())
            except ValueError:
                qty = 1
            try:
                unit = float(ent_unit.get())
            except ValueError:
                unit = 0.0
            try:
                listp = float(ent_list.get())
            except ValueError:
                listp = 0.0
            src = ent_source.get().strip()

            item = {
                "part_number": pn,
                "description": desc,
                "quantity": qty,
                "unit_cost": unit,
                "list_price": listp,
                "source": src,
                "line_total": round(qty * unit, 2),
            }
            current["quote"]["items"].append(item)
            update_tree()
            update_totals()
            add_part_window.destroy()

        add_part_window = tk.Toplevel(root)
        add_part_window.title("Add Part")
        add_part_window.transient(root)
        add_part_window.grab_set()

        lbl_part = ttk.Label(add_part_window, text="Part #")
        lbl_part.grid(row=0, column=0, sticky="e")
        ent_part = ttk.Entry(add_part_window)
        ent_part.grid(row=0, column=1, sticky="we")

        lbl_desc = ttk.Label(add_part_window, text="Description")
        lbl_desc.grid(row=1, column=0, sticky="e")
        ent_desc = ttk.Entry(add_part_window)
        ent_desc.grid(row=1, column=1, sticky="we")

        lbl_qty = ttk.Label(add_part_window, text="Qty")
        lbl_qty.grid(row=2, column=0, sticky="e")
        ent_qty = ttk.Entry(add_part_window)
        ent_qty.insert(0, "1")
        ent_qty.grid(row=2, column=1, sticky="we")

        lbl_unit = ttk.Label(add_part_window, text="Unit Cost")
        lbl_unit.grid(row=3, column=0, sticky="e")
        ent_unit = ttk.Entry(add_part_window)
        ent_unit.insert(0, "0.00")
        ent_unit.grid(row=3, column=1, sticky="we")

        lbl_list = ttk.Label(add_part_window, text="List Price")
        lbl_list.grid(row=4, column=0, sticky="e")
        ent_list = ttk.Entry(add_part_window)
        ent_list.insert(0, "0.00")
        ent_list.grid(row=4, column=1, sticky="we")

        lbl_source = ttk.Label(add_part_window, text="Source")
        lbl_source.grid(row=5, column=0, sticky="e")
        ent_source = ttk.Entry(add_part_window)
        ent_source.grid(row=5, column=1, sticky="we")

        btn = ttk.Button(add_part_window, text="Add", command=_submit)
        btn.grid(row=6, column=0, columnspan=2, pady=(8, 4))

        add_part_window.columnconfigure(1, weight=1)

    def update_tree():
        for r in tree.get_children():
            tree.delete(r)
        q = current.get("quote")
        if not q:
            return
        for idx, it in enumerate(q["items"], start=1):
            tree.insert(
                "",
                "end",
                iid=str(idx - 1),
                values=(
                    it.get("part_number"),
                    it.get("description"),
                    it.get("quantity"),
                    f"{(it.get('unit_cost') or 0.0):.2f}",
                    f"{(it.get('list_price') or 0.0):.2f}",
                    it.get("source"),
                    f"{(it.get('line_total') or 0.0):.2f}",
                ),
            )
        # Refresh tags so selection and odd/even backgrounds are applied
        refresh_tags()

    def update_totals():
        q = current.get("quote")
        if not q:
            lbl_total.configure(text="Total: $0.00")
            return
        total = sum(it.get("line_total", 0.0) for it in q["items"])
        lbl_total.configure(text=f"Total: ${total:.2f}")

    def delete_item():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Delete", "No item selected.")
            return
        idx = int(sel[0])
        if messagebox.askyesno("Delete", "Remove selected item?"):
            q = current.get("quote")
            if q and 0 <= idx < len(q["items"]):
                q["items"].pop(idx)
                update_tree()
                update_totals()

    def edit_item():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Edit", "No item selected.")
            return
        idx = int(sel[0])
        q = current.get("quote")
        if not q or not (0 <= idx < len(q["items"])):
            return
        it = q["items"][idx]

        def _submit_edit():
            it["part_number"] = ent_part.get().strip()
            it["description"] = ent_desc.get().strip()
            try:
                it["quantity"] = int(ent_qty.get())
            except ValueError:
                it["quantity"] = 1
            try:
                it["unit_cost"] = float(ent_unit.get())
            except ValueError:
                it["unit_cost"] = 0.0
            try:
                it["list_price"] = float(ent_list.get())
            except ValueError:
                it["list_price"] = 0.0
            it["source"] = ent_source.get().strip()
            it["line_total"] = round(it["quantity"] * it["unit_cost"], 2)
            update_tree()
            update_totals()
            edit_part_window.destroy()

        edit_part_window = tk.Toplevel(root)
        edit_part_window.title("Edit Part")
        edit_part_window.transient(root)
        edit_part_window.grab_set()

        lbl_part = ttk.Label(edit_part_window, text="Part #")
        lbl_part.grid(row=0, column=0, sticky="e")
        ent_part = ttk.Entry(edit_part_window)
        ent_part.insert(0, it.get("part_number", ""))
        ent_part.grid(row=0, column=1, sticky="we")

        lbl_desc = ttk.Label(edit_part_window, text="Description")
        lbl_desc.grid(row=1, column=0, sticky="e")
        ent_desc = ttk.Entry(edit_part_window)
        ent_desc.insert(0, it.get("description", ""))
        ent_desc.grid(row=1, column=1, sticky="we")

        lbl_qty = ttk.Label(edit_part_window, text="Qty")
        lbl_qty.grid(row=2, column=0, sticky="e")
        ent_qty = ttk.Entry(edit_part_window)
        ent_qty.insert(0, str(it.get("quantity", 1)))
        ent_qty.grid(row=2, column=1, sticky="we")

        lbl_unit = ttk.Label(edit_part_window, text="Unit Cost")
        lbl_unit.grid(row=3, column=0, sticky="e")
        ent_unit = ttk.Entry(edit_part_window)
        ent_unit.insert(0, f"{it.get('unit_cost', 0.0):.2f}")
        ent_unit.grid(row=3, column=1, sticky="we")

        lbl_list = ttk.Label(edit_part_window, text="List Price")
        lbl_list.grid(row=4, column=0, sticky="e")
        ent_list = ttk.Entry(edit_part_window)
        ent_list.insert(0, f"{it.get('list_price', 0.0):.2f}")
        ent_list.grid(row=4, column=1, sticky="we")

        lbl_source = ttk.Label(edit_part_window, text="Source")
        lbl_source.grid(row=5, column=0, sticky="e")
        ent_source = ttk.Entry(edit_part_window)
        ent_source.insert(0, it.get("source", ""))
        ent_source.grid(row=5, column=1, sticky="we")

        btn = ttk.Button(edit_part_window, text="Save", command=_submit_edit)
        btn.grid(row=6, column=0, columnspan=2, pady=(8, 4))

        edit_part_window.columnconfigure(1, weight=1)

    def save_current(silent=False):
        quotes = load_quotes()
        q = current.get("quote")
        if not q:
            logger.debug("save_current called with no current quote")
            return
        # ensure notes are saved from the notes text area
        try:
            q["notes"] = notes_text.get("1.0", "end").rstrip("\n")
        except Exception as e:
            logger.debug("Failed to read notes text: %s", e)
            # normalize quote name to 'ARC YYYY-MM-DD [PO:xxx]' when saving
            try:
                q["name"] = format_quote_name(q)
            except Exception:
                logger.debug("Failed to normalize quote name for id=%s", q.get("id"))
        # replace if exists
        existing = [x for x in quotes if x.get("id") == q.get("id")]
        if existing:
            quotes = [x for x in quotes if x.get("id") != q.get("id")]
        quotes.append(q)
        logger.info("Saving current quote id=%s name=%s", q.get("id"), q.get("name"))
        save_quotes(quotes)
        if not silent:
            messagebox.showinfo("Save", "Quote saved.")

    def _set_po_from_entry(event=None):
        val = po_entry_var.get().strip()
        if not val and current.get("quote") is None:
            return
        if current.get("quote") is None:
            new_quote()
        current["quote"]["po_number"] = val

    def load_quote():
        quotes = load_quotes()
        if not quotes:
            messagebox.showinfo("Load Quote", "No saved quotes found.")
            return

        def _quote_label(q):
            po = q.get("po_number")
            po_str = f" [PO:{po}]" if po else ""
            # Hide internal id from the UI; show standardized name + PO and item count
            return f"{q.get('name')}{po_str} ({len(q.get('items', []))} items)"

        load_quote_window = tk.Toplevel(root)
        load_quote_window.title("Load Quote")
        load_quote_window.transient(root)
        load_quote_window.grab_set()

        lb = tk.Listbox(load_quote_window, width=60)
        for q in quotes:
            lb.insert("end", _quote_label(q))
        lb.pack(fill="both", expand=True)

        def _load():
            sel = lb.curselection()
            if not sel:
                return
            idx = int(sel[0])
            q = quotes[idx]
            set_current_quote(q)
            load_quote_window.destroy()

        def _delete():
            sel = lb.curselection()
            if not sel:
                messagebox.showinfo("Delete Quote", "No quote selected.")
                return
            idx = int(sel[0])
            q = quotes[idx]
            if not messagebox.askyesno(
                "Delete Quote", f"Delete quote '{q.get('name')}'?"
            ):
                return
            # remove and save
            del quotes[idx]
            save_quotes(quotes)
            lb.delete(idx)
            # if the deleted quote was loaded, clear current
            if current.get("quote") and current["quote"].get("id") == q.get("id"):
                clear_current()

        def _export():
            sel = lb.curselection()
            if not sel:
                messagebox.showinfo("Export Quote", "No quote selected.")
                return
            idx = int(sel[0])
            q = quotes[idx]
            # Suggest a safe filename based on standardized quote name
            suggested = _safe_filename(format_quote_name(q))
            fn = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=f"{suggested}.json",
            )
            if not fn:
                return
            with open(fn, "w") as f:
                json.dump(q, f, indent=4, default=str)
            messagebox.showinfo("Export Quote", f"Quote exported to {fn}")

        def _import():
            fn = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if not fn:
                return
            try:
                with open(fn, "r") as f:
                    payload = json.load(f)
            except Exception as e:
                messagebox.showerror("Import Quote", f"Failed to read file: {e}")
                return
            # payload should be a dict representing a quote
            if not isinstance(payload, dict) or "items" not in payload:
                messagebox.showerror(
                    "Import Quote", "File does not appear to be a valid quote JSON."
                )
                return
            # avoid id collision: if same id exists, assign a new id
            existing_ids = {x.get("id") for x in quotes}
            if payload.get("id") in existing_ids:
                payload["id"] = int(
                    datetime.datetime.now(datetime.timezone.utc).timestamp()
                )
            # normalize imported quote name to project format
            try:
                payload["name"] = format_quote_name(payload)
            except Exception:
                logger.debug(
                    "Failed to normalize imported quote name for id=%s",
                    payload.get("id"),
                )
            quotes.append(payload)
            save_quotes(quotes)
            lb.insert("end", _quote_label(payload))
            messagebox.showinfo(
                "Import Quote", f"Imported quote '{payload.get('name')}'"
            )

        btn_frame = tk.Frame(load_quote_window)
        btn_frame.pack(fill="x", pady=6)
        btn_load = ttk.Button(btn_frame, text="Load", command=_load)
        btn_load.pack(side="left", padx=6)
        btn_del = ttk.Button(btn_frame, text="Delete", command=_delete)
        btn_del.pack(side="left", padx=6)
        btn_exp = ttk.Button(btn_frame, text="Export", command=_export)
        btn_exp.pack(side="left", padx=6)
        btn_imp = ttk.Button(btn_frame, text="Import", command=_import)
        btn_imp.pack(side="left", padx=6)
        btn_close = ttk.Button(
            btn_frame, text="Close", command=load_quote_window.destroy
        )
        btn_close.pack(side="right", padx=6)

    def export_pdf():
        q = current.get("quote")
        if not q:
            messagebox.showinfo("Export", "No current quote to export.")
            return
        # Create a temporary PDF file and open it in the default viewer
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
        # Page margins / left-right offset
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
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                    ("TOPPADDING", (0, 0), (-1, 0), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        # Draw the table and handle simple page overflow
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

    try:
        _small_icon = None
        if APP_ICON and os.path.exists(APP_ICON):
            try:
                # Prefer Pillow for reliable resizing and multi-format support
                from PIL import Image, ImageTk

                img = Image.open(APP_ICON)
                img = img.convert("RGBA")
                img = img.resize((18, 18), Image.LANCZOS)
                _small_icon = ImageTk.PhotoImage(img)
            except Exception:
                # Fallback to Tk PhotoImage (may support PNG/GIF)
                try:
                    _small_icon = tk.PhotoImage(file=APP_ICON)
                except Exception:
                    _small_icon = None
        if _small_icon:
            root._small_icon = _small_icon
            brand_lbl = tk.Label(
                toolbar, image=_small_icon, compound="left", bg=TOOLBAR_BG, fg=FG
            )
            brand_lbl.pack(side="left", padx=(6, 8), pady=6)
        else:
            # Pack a label anyway, gotta make it look consistent
            brand_lbl = tk.Label(toolbar, text=APP_TITLE, bg=TOOLBAR_BG, fg=FG)
            brand_lbl.pack(side="left", padx=(6, 8), pady=6)
    except Exception:
        logger.debug("Failed to load toolbar icon:", exc_info=True)
        pass

    btn_new = ttk.Button(toolbar, text="New Quote", command=new_quote)
    btn_new.pack(side="left", padx=6, pady=6)
    btn_add = ttk.Button(toolbar, text="Add Part", command=add_part)
    btn_add.pack(side="left", padx=6, pady=6)
    btn_edit = ttk.Button(toolbar, text="Edit Item", command=edit_item)
    btn_edit.pack(side="left", padx=6, pady=6)
    btn_del = ttk.Button(toolbar, text="Delete Item", command=delete_item)
    btn_del.pack(side="left", padx=6, pady=6)
    btn_save = ttk.Button(toolbar, text="Save Quote", command=save_current)
    btn_save.pack(side="left", padx=6, pady=6)
    btn_load = ttk.Button(toolbar, text="Load Quote", command=load_quote)
    btn_load.pack(side="left", padx=6, pady=6)
    ver_lbl = ttk.Label(toolbar, text=VERSION)
    ver_lbl.pack(side="right", padx=6)

    try:
        platform_name_font_size = 10
        plat_name = "macOS" if platform.system() == "Darwin" else platform.system()
        small_font = tkfont.Font(family="Helvetica", size=platform_name_font_size)
        plat_lbl = tk.Label(
            toolbar, text=plat_name, bg=TOOLBAR_BG, fg=FG, font=small_font
        )
        plat_lbl.pack(side="right", padx=(0, 6))
    except Exception:
        pass

    btn_pdf = ttk.Button(toolbar, text="Export PDF", command=export_pdf)
    btn_pdf.pack(side="right", padx=6, pady=6)

    def _exit_app(event=None):
        q = current.get("quote")
        if q:
            ans = messagebox.askyesnocancel(
                "Exit", "Save current quote before exiting?"
            )
            if ans is None:
                return
            if ans:
                save_current()
            root.destroy()
        else:
            if messagebox.askyesno("Exit", "Are you sure you want to quit?"):
                root.destroy()

    btn_exit = ttk.Button(toolbar, text="Exit", command=_exit_app)
    btn_exit.pack(side="right", padx=6, pady=6)

    # PO# label and entry on the toolbar
    lbl_po = ttk.Label(toolbar, text="PO#")
    lbl_po.pack(side="left", padx=(12, 2))
    po_entry = ttk.Entry(toolbar, textvariable=po_entry_var, width=18)
    po_entry.pack(side="left", padx=(2, 12))
    # Update current quote when PO entry loses focus or on Enter
    po_entry.bind("<Return>", lambda e: _set_po_from_entry())
    po_entry.bind("<FocusOut>", lambda e: _set_po_from_entry())
    cols = ("part", "desc", "qty", "unit", "list", "source", "line")
    tree = ttk.Treeview(content, columns=cols, show="headings")
    tree.place(relx=0.02, rely=0.12, relwidth=0.96, relheight=0.60)
    headings = [
        "Part #",
        "Description",
        "Qty",
        "Unit Cost",
        "List Price",
        "Source",
        "Line Total",
    ]
    for c, h in zip(cols, headings):
        tree.heading(c, text=h)

    # Set sensible default column widths so everything fits without resizing
    # Total available width approx: 0.96 * window_width (~1000) => ~960 px
    col_widths = {
        "part": 110,
        "desc": 330,
        "qty": 60,
        "unit": 80,
        "list": 80,
        "source": 140,
        "line": 120,
    }
    for col, w in col_widths.items():
        tree.column(col, width=w, anchor="w", stretch=(col == "desc"))

    # Configure tags to avoid hover/active white background issues
    tree.tag_configure("row_even", background=PANEL_BG, foreground=FG)
    tree.tag_configure("row_odd", background=PANEL_BG, foreground=FG)
    tree.tag_configure("selected", background=SELECT_BG, foreground="#ffffff")

    def refresh_tags(event=None):
        sel = set(tree.selection())
        for idx, iid in enumerate(tree.get_children()):
            if iid in sel:
                tree.item(iid, tags=("selected",))
            else:
                tag = "row_even" if (idx % 2 == 0) else "row_odd"
                tree.item(iid, tags=(tag,))

    tree.bind("<<TreeviewSelect>>", refresh_tags)
    tree.bind("<Enter>", refresh_tags)
    tree.bind("<Leave>", refresh_tags)

    # Total Label
    lbl_total = tk.Label(content, text="Total: $0.00", bg=bg_color)
    lbl_total.place(relx=0.02, rely=0.75)
    lbl_total.configure(font=button_font, foreground=FG)

    #Notes area
    notes_frame = tk.Frame(content, bg=PANEL_BG, bd=0)
    notes_frame.place(relx=0.02, rely=0.78, relwidth=0.96, relheight=0.20)
    notes_label = ttk.Label(notes_frame, text="Notes:")
    notes_label.pack(anchor="nw", padx=6, pady=(6, 0))
    notes_text = tk.Text(
        notes_frame,
        wrap="word",
        height=5,
        bg=PANEL_BG,
        fg=FG,
        insertbackground=FG,
        relief="flat",
        bd=0,
        font=body_font,
        highlightthickness=1,
        highlightbackground="#2a2a2a",
    )
    notes_text.pack(fill="both", expand=True, padx=6, pady=6)

    # Keep notes synced with current quote
    def _load_notes_for_quote(q):
        notes_text.delete("1.0", "end")
        if q:
            notes_text.insert("1.0", q.get("notes", ""))

    # Save notes back into the quote when focus leaves the notes area
    def _save_notes(event=None):
        q = current.get("quote")
        if not q:
            return
        q["notes"] = notes_text.get("1.0", "end").rstrip("\n")

    notes_text.bind("<FocusOut>", _save_notes)

    # If quotes exist, load the most recent by default
    quotes = load_quotes()
    if quotes:
        # pick the most recently created (by created_at)
        quotes_sorted = sorted(
            quotes, key=lambda x: x.get("created_at") or "", reverse=True
        )
        set_current_quote(quotes_sorted[0])

    return root


def main():
    root = build_ui()
    root.mainloop()


if __name__ == "__main__":
    main()
