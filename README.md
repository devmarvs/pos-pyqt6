# POS App (Python, PyQt6, SQLAlchemy, Alembic)

## Quick start (SQLite)
```
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
python setup_db.py
python app.py
```
## PostgreSQL
```
export DATABASE_URL="postgresql+psycopg://user:pass@host:5432/posdb"
python setup_db.py
python app.py
```
## Migrations
```
alembic revision --autogenerate -m "change"
alembic upgrade head
```


## Login (demo)
Default users (seeded by `setup_db.py`):
- admin / changeme
- manager / changeme
- cashier / changeme

Roles: Admin, Manager, Cashier. Products/Customers require Admin or Manager.

## Printing
The demo uses a simple ESC/POS stub (`pos_app/integrations/printers/escpos.py`). 
Replace with `python-escpos` for real printers and update the device config there.


## Devices & Labels
- **Devices → Printer Settings** to set ESC/POS (receipt) and Zebra (label) printers.
- In **Products**, use **Print Label (Selected)** to send a simple ZPL barcode label.
- **Reports** tab exports CSV/PDF (uses WeasyPrint).


## Profiles, USB Zebra, and Expanded Reports
- **Printer Profiles**: Devices → Printer Settings lets you create per-store/register profiles and set the active one.
- **Zebra USB**: Set VID/PID in the Zebra section (hex like `0x0a5f`). Falls back to console if not found.
- **Reports**: Tabs for Daily Summary, Category, Cashier, and Payment. Export CSV/PDF and save bar charts (matplotlib).
