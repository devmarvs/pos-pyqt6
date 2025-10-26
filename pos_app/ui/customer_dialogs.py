from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QDialogButtonBox,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from sqlalchemy.orm import Session
from pos_app.data.models import Customer


class CustomerFormDialog(QDialog):
    def __init__(self, session: Session, customer: Customer | None = None, parent=None):
        super().__init__(parent)
        self.session = session
        self.customer = customer
        self.mode = "edit" if customer else "add"
        self.setWindowTitle("Edit Customer" if self.mode == "edit" else "Add Customer")
        layout = QVBoxLayout(self)

        self.name = QLineEdit()
        self.email = QLineEdit()
        self.phone = QLineEdit()
        self.loyalty = QSpinBox()
        self.loyalty.setRange(0, 1_000_000)

        form = QVBoxLayout()

        def row(label, widget):
            line = QHBoxLayout()
            line.addWidget(QLabel(label))
            line.addWidget(widget)
            form.addLayout(line)

        self.name.setPlaceholderText("Customer name")
        self.email.setPlaceholderText("Email (optional)")
        self.phone.setPlaceholderText("Phone (optional)")
        row("Name", self.name)
        row("Email", self.email)
        row("Phone", self.phone)
        row("Loyalty Points", self.loyalty)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if self.customer:
            self.name.setText(self.customer.name or "")
            self.email.setText(self.customer.email or "")
            self.phone.setText(self.customer.phone or "")
            self.loyalty.setValue(int(self.customer.loyalty_points or 0))

    def accept(self):
        name = self.name.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing", "Name is required.")
            return
        try:
            if self.customer is None:
                self.customer = Customer()
                self.session.add(self.customer)
            self.customer.name = name
            self.customer.email = self.email.text().strip() or None
            self.customer.phone = self.phone.text().strip() or None
            self.customer.loyalty_points = int(self.loyalty.value())
            super().accept()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))


class CustomerDeleteDialog(QDialog):
    def __init__(self, customer: Customer, parent=None):
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle("Delete Customer")
        layout = QVBoxLayout(self)
        info = QLabel(
            f"Delete customer '{customer.name}'"
            f"{' (' + customer.email + ')' if customer.email else ''}?"
        )
        info.setWordWrap(True)
        warn = QLabel("This action will permanently remove the customer record.")
        warn.setStyleSheet("color: #b00020;")
        warn.setAlignment(Qt.AlignmentFlag.AlignLeft)
        warn.setWordWrap(True)
        layout.addWidget(info)
        layout.addWidget(warn)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        confirm_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        confirm_btn.setText("Delete")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
