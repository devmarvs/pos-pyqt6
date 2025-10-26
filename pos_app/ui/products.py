from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel, QMessageBox, QFileDialog
from sqlalchemy.orm import Session
from pos_app.data.models import Product
from .product_edit_dialog import ProductEditDialog
from .product_delete_dialog import ProductDeleteDialog

class ProductsPage(QWidget):
    def __init__(self, session_maker):
        super().__init__()
        self.SessionLocal = session_maker
        self.session: Session = self.SessionLocal()
        layout = QVBoxLayout(self)
        search_row = QHBoxLayout(); self.search = QLineEdit(); self.search.setPlaceholderText("Search by SKU / Barcode / Name"); self.btn_search = QPushButton("Search"); self.btn_clear = QPushButton("Clear"); search_row.addWidget(QLabel("Search:")); search_row.addWidget(self.search); search_row.addWidget(self.btn_search); search_row.addWidget(self.btn_clear); layout.addLayout(search_row)
        self.table = QTableWidget(0, 6); self.table.setHorizontalHeaderLabels(["ID", "SKU", "Barcode", "Name", "Price", "Active"]); self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers); layout.addWidget(self.table)
        btns = QHBoxLayout(); self.btn_add = QPushButton("Add"); self.btn_edit = QPushButton("Edit Selected"); self.btn_delete = QPushButton("Delete Selected")
        self.btn_label = QPushButton("Print Label (Selected)"); btns.addWidget(self.btn_add); btns.addWidget(self.btn_edit); btns.addWidget(self.btn_delete); btns.addWidget(self.btn_label); layout.addLayout(btns)
        self.btn_add.clicked.connect(self.add_product); self.btn_edit.clicked.connect(self.edit_selected); self.btn_delete.clicked.connect(self.delete_selected)
        self.btn_label.clicked.connect(self.print_label); self.btn_search.clicked.connect(self.refresh); self.btn_clear.clicked.connect(self._clear_search)
        self.refresh()
    def _query(self):
        q = self.session.query(Product); term = self.search.text().strip()
        if term:
            like = f"%{term}%"; q = q.filter((Product.sku.ilike(like)) | (Product.name.ilike(like)) | (Product.barcode.ilike(like)))
        return q.order_by(Product.id.desc())
    def refresh(self):
        rows = self._query().all(); self.table.setRowCount(len(rows))
        for i, p in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(p.id)))
            self.table.setItem(i, 1, QTableWidgetItem(p.sku or ""))
            self.table.setItem(i, 2, QTableWidgetItem(p.barcode or ""))
            self.table.setItem(i, 3, QTableWidgetItem(p.name or ""))
            self.table.setItem(i, 4, QTableWidgetItem(f"{(p.price or 0):.2f}"))
            self.table.setItem(i, 5, QTableWidgetItem("Yes" if p.active else "No"))
        self.table.resizeColumnsToContents()
    def _selected_product_id(self):
        r = self.table.currentRow();
        if r < 0: return None
        return int(self.table.item(r, 0).text())
    def add_product(self):
        dlg = ProductEditDialog(self.session, None, self)
        if dlg.exec():
            try: self.session.commit(); self.refresh()
            except Exception as e: self.session.rollback(); QMessageBox.critical(self, "Error", str(e))
    def edit_selected(self):
        pid = self._selected_product_id()
        if not pid: QMessageBox.information(self, "Select", "Select a product first."); return
        prod = self.session.get(Product, pid)
        if not prod: return
        dlg = ProductEditDialog(self.session, prod, self)
        if dlg.exec():
            try: self.session.commit(); self.refresh()
            except Exception as e: self.session.rollback(); QMessageBox.critical(self, "Error", str(e))
    def delete_selected(self):
        pid = self._selected_product_id()
        if not pid: QMessageBox.information(self, "Select", "Select a product first."); return
        try:
            prod = self.session.get(Product, pid)
            if not prod: return
            dlg = ProductDeleteDialog(prod, self)
            if not dlg.exec():
                return
            self.session.delete(prod); self.session.commit(); self.refresh()
        except Exception as e:
            self.session.rollback(); QMessageBox.critical(self, "Error", str(e))
    def _clear_search(self):
        self.search.clear(); self.refresh()

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "products.csv", "CSV Files (*.csv)")
        if not path: return
        rows = self._query().all()
        import csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id","sku","barcode","name","price","active","category_id","tax_id"])
            for p in rows:
                w.writerow([p.id, p.sku, p.barcode or "", p.name, p.price or 0, 1 if p.active else 0, p.category_id or "", p.tax_id or ""])

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if not path: return
        import csv
        with open(path, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                sku = (row.get("sku") or "").strip()
                name = (row.get("name") or "").strip()
                if not sku or not name: continue
                p = self.session.query(Product).filter(Product.sku==sku).first()
                if p is None:
                    p = Product(sku=sku)
                    self.session.add(p)
                p.barcode = (row.get("barcode") or None)
                p.name = name
                try:
                    p.price = float(row.get("price") or 0)
                except Exception:
                    p.price = 0
                cat_raw = row.get("category_id")
                tax_raw = row.get("tax_id")
                try:
                    p.category_id = int(cat_raw) if cat_raw else None
                except (TypeError, ValueError):
                    p.category_id = None
                try:
                    p.tax_id = int(tax_raw) if tax_raw else None
                except (TypeError, ValueError):
                    p.tax_id = None
                p.active = (str(row.get("active") or "1").strip() in {"1","true","True","yes"})
            try:
                self.session.commit(); self.refresh()
            except Exception as e:
                self.session.rollback(); QMessageBox.critical(self, "Import error", str(e))

    def print_label(self):
        pid = self._selected_product_id()
        if not pid:
            QMessageBox.information(self, "Select", "Select a product first."); return
        p = self.session.get(Product, pid)
        if not p or not p.barcode:
            QMessageBox.warning(self, "Missing", "Selected product has no barcode."); return
        try:
            from pos_app.integrations.printers.zpl import ZebraPrinter
            ZebraPrinter().print_barcode_label(barcode=p.barcode, title=p.name[:30], copies=1)
            QMessageBox.information(self, "Label", "Label sent.")
        except Exception as e:
            QMessageBox.warning(self, "Label", str(e))
