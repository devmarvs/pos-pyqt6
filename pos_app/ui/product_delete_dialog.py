from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
from PyQt6.QtCore import Qt
from pos_app.data.models import Product


class ProductDeleteDialog(QDialog):
    def __init__(self, product: Product, parent=None):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle("Delete Product")
        layout = QVBoxLayout(self)
        info = (
            f"Delete product '{product.name}' (SKU: {product.sku}"
            f"{', Barcode: ' + product.barcode if product.barcode else ''})?"
        )
        confirm_lbl = QLabel(info)
        confirm_lbl.setWordWrap(True)
        warn_lbl = QLabel("This action cannot be undone.")
        warn_lbl.setWordWrap(True)
        warn_lbl.setStyleSheet("color: #b00020;")
        warn_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(confirm_lbl)
        layout.addWidget(warn_lbl)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        delete_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        delete_btn.setText("Delete")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
