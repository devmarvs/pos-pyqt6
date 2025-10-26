from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from sqlalchemy.orm import Session
from pos_app.data.models import User
from pos_app.auth import verify_password

class LoginDialog(QDialog):
    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sign in")
        self.session = session
        layout = QVBoxLayout(self)
        self.username = QLineEdit(); self.username.setPlaceholderText("Username")
        self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.EchoMode.Password); self.password.setPlaceholderText("Password")
        layout.addWidget(QLabel("Username")); layout.addWidget(self.username)
        layout.addWidget(QLabel("Password")); layout.addWidget(self.password)
        row = QHBoxLayout(); ok = QPushButton("Sign in"); cancel = QPushButton("Cancel"); row.addWidget(ok); row.addWidget(cancel); layout.addLayout(row)
        ok.clicked.connect(self.try_login); cancel.clicked.connect(self.reject)
        self.user = None
    def try_login(self):
        u = self.session.query(User).filter(User.username == self.username.text().strip(), User.active == True).first()
        if not u or not verify_password(self.password.text(), u.password_hash):
            QMessageBox.warning(self, "Invalid", "Invalid username or password."); return
        self.user = u; self.accept()
