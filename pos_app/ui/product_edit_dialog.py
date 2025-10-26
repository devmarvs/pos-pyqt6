from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDoubleSpinBox, QComboBox, QPushButton, QMessageBox, QCheckBox
from sqlalchemy.orm import Session
from pos_app.data.models import Product, Category, TaxRate

class ProductEditDialog(QDialog):
    def __init__(self, session: Session, product: Product | None = None, parent=None):
        super().__init__(parent)
        self.session = session
        self.product = product
        self.mode = "edit" if product else "add"
        self.setWindowTitle("Edit Product" if self.mode == "edit" else "Add Product")
        layout = QVBoxLayout(self)
        self.sku = QLineEdit(); self.sku.setPlaceholderText("SKU")
        self.barcode = QLineEdit(); self.barcode.setPlaceholderText("Barcode")
        self.name = QLineEdit(); self.name.setPlaceholderText("Name")
        self.price = QDoubleSpinBox(); self.price.setRange(0, 999999); self.price.setDecimals(2); self.price.setValue(1.00)
        self.category = QComboBox(); self.tax = QComboBox()
        self.active = QCheckBox("Active")
        cats = self.session.query(Category).order_by(Category.name).all()
        taxes = self.session.query(TaxRate).order_by(TaxRate.name).all()
        for c in cats: self.category.addItem(c.name, c.id)
        for t in taxes: self.tax.addItem(f"{t.name} ({t.rate:.2f})", t.id)
        form = QVBoxLayout()
        def row(lbl, w):
            r = QHBoxLayout(); r.addWidget(QLabel(lbl)); r.addWidget(w); form.addLayout(r)
        row("SKU", self.sku); row("Barcode", self.barcode); row("Name", self.name); row("Price", self.price); row("Category", self.category); row("Tax", self.tax)
        active_row = QHBoxLayout(); active_row.addWidget(QLabel("Status")); active_row.addWidget(self.active); form.addLayout(active_row)
        layout.addLayout(form)
        btns = QHBoxLayout(); ok = QPushButton("Save"); cancel = QPushButton("Cancel"); btns.addWidget(ok); btns.addWidget(cancel); layout.addLayout(btns)
        ok.clicked.connect(self.accept); cancel.clicked.connect(self.reject)
        if self.product:
            self.sku.setText(self.product.sku or "")
            self.barcode.setText(self.product.barcode or "")
            self.name.setText(self.product.name or "")
            self.price.setValue(float(self.product.price or 0))
            if self.product.category_id is not None:
                idx = self.category.findData(self.product.category_id)
                if idx >= 0: self.category.setCurrentIndex(idx)
            if self.product.tax_id is not None:
                idx = self.tax.findData(self.product.tax_id)
                if idx >= 0: self.tax.setCurrentIndex(idx)
            self.active.setChecked(bool(self.product.active))
        else:
            self.active.setChecked(True)

    def accept(self):
        if not self.sku.text().strip() or not self.name.text().strip():
            QMessageBox.warning(self, "Missing", "SKU and Name are required."); return
        try:
            if self.product is None:
                self.product = Product(); self.session.add(self.product)
            self.product.sku = self.sku.text().strip()
            self.product.barcode = self.barcode.text().strip() or None
            self.product.name = self.name.text().strip()
            self.product.price = float(self.price.value())
            self.product.category_id = self.category.currentData()
            self.product.tax_id = self.tax.currentData()
            self.product.active = self.active.isChecked()
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
