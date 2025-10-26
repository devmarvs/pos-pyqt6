from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from sqlalchemy.orm import Session
from pos_app.data.models import User
from pos_app.auth import hash_password, verify_password

class ChangePasswordDialog(QDialog):
    def __init__(self, session: Session, user: User, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change Password")
        self.session = session
        self.user = user
        layout = QVBoxLayout(self)
        self.current = QLineEdit(); self.current.setEchoMode(QLineEdit.EchoMode.Password)
        self.new1 = QLineEdit(); self.new1.setEchoMode(QLineEdit.EchoMode.Password)
        self.new2 = QLineEdit(); self.new2.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("Current password")); layout.addWidget(self.current)
        layout.addWidget(QLabel("New password")); layout.addWidget(self.new1)
        layout.addWidget(QLabel("Confirm new password")); layout.addWidget(self.new2)
        row = QHBoxLayout(); ok = QPushButton("Update"); cancel = QPushButton("Cancel"); row.addWidget(ok); row.addWidget(cancel); layout.addLayout(row)
        ok.clicked.connect(self.apply); cancel.clicked.connect(self.reject)
    def apply(self):
        if not verify_password(self.current.text(), self.user.password_hash):
            QMessageBox.warning(self, "Invalid", "Current password is incorrect."); return
        if not self.new1.text() or self.new1.text() != self.new2.text():
            QMessageBox.warning(self, "Mismatch", "New passwords do not match."); return
        self.user.password_hash = hash_password(self.new1.text())
        self.session.add(self.user); self.session.commit(); self.accept()
