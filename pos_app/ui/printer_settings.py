
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QComboBox, QMessageBox, QSpinBox, QListWidget)
from pos_app.settings_store import load_settings, save_settings, set_active_profile

class PrinterSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Printer Profiles")
        self.data = load_settings()
        layout = QVBoxLayout(self)

        # Profiles list and controls
        top = QHBoxLayout()
        self.list = QListWidget()
        self.list.addItems(sorted(self.data.get("profiles", {}).keys()))
        top.addWidget(self.list)
        actions = QVBoxLayout()
        self.btn_new = QPushButton("New Profile")
        self.btn_delete = QPushButton("Delete Profile")
        self.btn_make_active = QPushButton("Make Active")
        actions.addWidget(self.btn_new); actions.addWidget(self.btn_delete); actions.addWidget(self.btn_make_active)
        actions.addStretch(1)
        top.addLayout(actions)
        layout.addLayout(top)

        # Form for selected profile
        self.store = QLineEdit(); self.register = QLineEdit()
        self.esc_mode = QComboBox(); self.esc_mode.addItems(["network","usb"])
        self.esc_host = QLineEdit(); self.esc_port = QSpinBox(); self.esc_port.setRange(1,65535); self.esc_port.setValue(9100)
        self.esc_vid = QLineEdit(); self.esc_pid = QLineEdit()

        self.z_mode = QComboBox(); self.z_mode.addItems(["network","usb"])
        self.z_host = QLineEdit(); self.z_port = QSpinBox(); self.z_port.setRange(1,65535); self.z_port.setValue(9100)
        self.z_vid = QLineEdit(); self.z_pid = QLineEdit()

        def row(lbl, w):
            r = QHBoxLayout(); r.addWidget(QLabel(lbl)); r.addWidget(w); return r

        layout.addLayout(row("Store", self.store))
        layout.addLayout(row("Register", self.register))
        layout.addLayout(row("ESC/POS Mode", self.esc_mode))
        layout.addLayout(row("ESC/POS Host", self.esc_host))
        layout.addLayout(row("ESC/POS Port", self.esc_port))
        layout.addLayout(row("ESC/POS USB VID (hex)", self.esc_vid))
        layout.addLayout(row("ESC/POS USB PID (hex)", self.esc_pid))

        layout.addLayout(row("Zebra Mode", self.z_mode))
        layout.addLayout(row("Zebra Host", self.z_host))
        layout.addLayout(row("Zebra Port", self.z_port))
        layout.addLayout(row("Zebra USB VID (hex)", self.z_vid))
        layout.addLayout(row("Zebra USB PID (hex)", self.z_pid))

        save_row = QHBoxLayout()
        self.btn_save = QPushButton("Save Changes"); self.btn_close = QPushButton("Close")
        save_row.addWidget(self.btn_save); save_row.addWidget(self.btn_close)
        layout.addLayout(save_row)

        # Wire events
        self.list.currentTextChanged.connect(self._load_profile)
        self.btn_new.clicked.connect(self._new_profile)
        self.btn_delete.clicked.connect(self._delete_profile)
        self.btn_make_active.clicked.connect(self._make_active)
        self.btn_save.clicked.connect(self._save_changes)
        self.btn_close.clicked.connect(self.accept)

        # Load initial
        if self.list.count() > 0:
            self.list.setCurrentRow(0)

    def _current_name(self):
        return self.list.currentItem().text() if self.list.currentItem() else None

    def _load_profile(self, name: str):
        prof = self.data.get("profiles", {}).get(name, {})
        self.store.setText(prof.get("store",""))
        self.register.setText(prof.get("register",""))
        esc = prof.get("escpos", {})
        self.esc_mode.setCurrentText(esc.get("mode","network"))
        self.esc_host.setText(esc.get("host",""))
        self.esc_port.setValue(int(esc.get("port",9100)))
        self.esc_vid.setText(hex(int(esc.get("usb_vid",0))) if esc.get("usb_vid") else "")
        self.esc_pid.setText(hex(int(esc.get("usb_pid",0))) if esc.get("usb_pid") else "")
        z = prof.get("zebra", {})
        self.z_mode.setCurrentText(z.get("mode","network"))
        self.z_host.setText(z.get("host",""))
        self.z_port.setValue(int(z.get("port",9100)))
        self.z_vid.setText(hex(int(z.get("usb_vid",0))) if z.get("usb_vid") else "")
        self.z_pid.setText(hex(int(z.get("usb_pid",0))) if z.get("usb_pid") else "")

    def _new_profile(self):
        base = "Profile"; i = 1
        names = set(self.data.get("profiles", {}).keys())
        while f"{base}-{i}" in names: i += 1
        name = f"{base}-{i}"
        self.data.setdefault("profiles", {})[name] = {
            "store":"", "register":"",
            "escpos":{"mode":"network","host":"","port":9100,"usb_vid":0,"usb_pid":0},
            "zebra":{"mode":"network","host":"","port":9100,"usb_vid":0,"usb_pid":0}
        }
        save_settings(self.data)
        self.list.addItem(name)
        self.list.setCurrentRow(self.list.count()-1)

    def _delete_profile(self):
        name = self._current_name()
        if not name: return
        if name == self.data.get("active_profile"):
            QMessageBox.warning(self, "Active profile", "Cannot delete the active profile."); return
        self.data.get("profiles", {}).pop(name, None)
        save_settings(self.data)
        row = self.list.currentRow()
        self.list.takeItem(row)

    def _make_active(self):
        name = self._current_name()
        if not name: return
        self.data["active_profile"] = name
        save_settings(self.data)
        QMessageBox.information(self, "Active profile", f"Active profile set to: {name}")

    def _save_changes(self):
        name = self._current_name()
        if not name: return
        esc_vid = int(self.esc_vid.text(), 16) if self.esc_vid.text() else 0
        esc_pid = int(self.esc_pid.text(), 16) if self.esc_pid.text() else 0
        z_vid = int(self.z_vid.text(), 16) if self.z_vid.text() else 0
        z_pid = int(self.z_pid.text(), 16) if self.z_pid.text() else 0
        self.data["profiles"][name] = {
            "store": self.store.text().strip(),
            "register": self.register.text().strip(),
            "escpos": {
                "mode": self.esc_mode.currentText(),
                "host": self.esc_host.text().strip(),
                "port": int(self.esc_port.value()),
                "usb_vid": esc_vid,
                "usb_pid": esc_pid
            },
            "zebra": {
                "mode": self.z_mode.currentText(),
                "host": self.z_host.text().strip(),
                "port": int(self.z_port.value()),
                "usb_vid": z_vid,
                "usb_pid": z_pid
            }
        }
        save_settings(self.data)
        QMessageBox.information(self, "Saved", "Profile saved.")
