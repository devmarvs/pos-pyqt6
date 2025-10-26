from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel, QMessageBox, QSpinBox
from sqlalchemy.orm import Session
from pos_app.data.models import Customer

class CustomersPage(QWidget):
    def __init__(self, session_maker):
        super().__init__()
        self.SessionLocal = session_maker
        self.session: Session = self.SessionLocal()
        layout = QVBoxLayout(self)
        search_row = QHBoxLayout(); self.search = QLineEdit(); self.search.setPlaceholderText("Search by name / email / phone"); self.btn_search = QPushButton("Search"); self.btn_clear = QPushButton("Clear"); search_row.addWidget(QLabel("Search:")); search_row.addWidget(self.search); search_row.addWidget(self.btn_search); search_row.addWidget(self.btn_clear); layout.addLayout(search_row)
        self.table = QTableWidget(0, 5); self.table.setHorizontalHeaderLabels(["ID", "Name", "Email", "Phone", "Loyalty"]); self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers); layout.addWidget(self.table)
        form = QHBoxLayout(); self.name = QLineEdit(); self.name.setPlaceholderText("Full name"); self.email = QLineEdit(); self.email.setPlaceholderText("Email"); self.phone = QLineEdit(); self.phone.setPlaceholderText("Phone"); self.loyalty = QSpinBox(); self.loyalty.setRange(0, 10000); form.addWidget(QLabel("Name")); form.addWidget(self.name); form.addWidget(QLabel("Email")); form.addWidget(self.email); form.addWidget(QLabel("Phone")); form.addWidget(self.phone); form.addWidget(QLabel("Loyalty")); form.addWidget(self.loyalty); layout.addLayout(form)
        btns = QHBoxLayout(); self.btn_add = QPushButton("Add"); self.btn_edit = QPushButton("Edit Selected"); self.btn_delete = QPushButton("Delete Selected"); btns.addWidget(self.btn_add); btns.addWidget(self.btn_edit); btns.addWidget(self.btn_delete); layout.addLayout(btns)
        self.btn_add.clicked.connect(self.add_customer); self.btn_edit.clicked.connect(self.edit_selected); self.btn_delete.clicked.connect(self.delete_selected); self.btn_search.clicked.connect(self.refresh); self.btn_clear.clicked.connect(self._clear_search)
        self.refresh()
    def _query(self):
        q = self.session.query(Customer); term = self.search.text().strip()
        if term:
            like = f"%{term}%"; q = q.filter((Customer.name.ilike(like)) | (Customer.email.ilike(like)) | (Customer.phone.ilike(like)))
        return q.order_by(Customer.id.desc())
    def refresh(self):
        rows = self._query().all(); self.table.setRowCount(len(rows))
        for i, c in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(c.id)))
            self.table.setItem(i, 1, QTableWidgetItem(c.name or ""))
            self.table.setItem(i, 2, QTableWidgetItem(c.email or ""))
            self.table.setItem(i, 3, QTableWidgetItem(c.phone or ""))
            self.table.setItem(i, 4, QTableWidgetItem(str(c.loyalty_points or 0)))
        self.table.resizeColumnsToContents()
    def _selected_customer_id(self):
        r = self.table.currentRow();
        if r < 0: return None
        return int(self.table.item(r, 0).text())
    def add_customer(self):
        name = self.name.text().strip()
        if not name: QMessageBox.warning(self, "Missing", "Name is required."); return
        try:
            c = Customer(name=name, email=self.email.text().strip() or None, phone=self.phone.text().strip() or None, loyalty_points=int(self.loyalty.value()))
            self.session.add(c); self.session.commit(); self.name.clear(); self.email.clear(); self.phone.clear(); self.loyalty.setValue(0); self.refresh()
        except Exception as e:
            self.session.rollback(); QMessageBox.critical(self, "Error", str(e))
    def edit_selected(self):
        cid = self._selected_customer_id()
        if not cid: QMessageBox.information(self, "Select", "Select a customer first."); return
        try:
            c = self.session.get(Customer, cid)
            if not c: return
            c.name = self.name.text().strip() or c.name
            c.email = self.email.text().strip() or c.email
            c.phone = self.phone.text().strip() or c.phone
            c.loyalty_points = int(self.loyalty.value())
            self.session.commit(); self.refresh()
        except Exception as e:
            self.session.rollback(); QMessageBox.critical(self, "Error", str(e))
    def delete_selected(self):
        cid = self._selected_customer_id()
        if not cid: QMessageBox.information(self, "Select", "Select a customer first."); return
        try:
            c = self.session.get(Customer, cid)
            if not c: return
            self.session.delete(c); self.session.commit(); self.refresh()
        except Exception as e:
            self.session.rollback(); QMessageBox.critical(self, "Error", str(e))
    def _clear_search(self):
        self.search.clear(); self.refresh()

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "customers.csv", "CSV Files (*.csv)")
        if not path: return
        rows = self._query().all()
        import csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id","name","email","phone","loyalty_points"])
            for c in rows:
                w.writerow([c.id, c.name, c.email or "", c.phone or "", c.loyalty_points or 0])

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if not path: return
        import csv
        with open(path, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                name = (row.get("name") or "").strip()
                if not name: continue
                email = (row.get("email") or None)
                phone = (row.get("phone") or None)
                try:
                    points = int(row.get("loyalty_points") or 0)
                except Exception:
                    points = 0
                # Use (name,email,phone) combo to find existing
                q = self.session.query(Customer).filter(Customer.name==name)
                if email: q = q.filter(Customer.email==email)
                c = q.first()
                if c is None:
                    from pos_app.data.models import Customer
                    c = Customer(name=name)
                    self.session.add(c)
                c.email = email; c.phone = phone; c.loyalty_points = points
            try:
                self.session.commit(); self.refresh()
            except Exception as e:
                self.session.rollback(); QMessageBox.critical(self, "Import error", str(e))
