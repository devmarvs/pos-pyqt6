from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtGui import QAction
from pos_app.data.db import get_engine, get_session_maker
from pos_app.data.models import Sale
from pos_app.services.sales import CompleteSaleService
from .products import ProductsPage
from .customers import CustomersPage
from .reports import ReportsPage
from .printer_settings import PrinterSettingsDialog
from .login import LoginDialog
from .change_password import ChangePasswordDialog
from pos_app.integrations.printers.escpos import EscPosPrinter

class SalesPage(QWidget):
    def __init__(self, session_maker, cashier_id: int | None = None):
        super().__init__()
        self.session_maker = session_maker
        self.session = session_maker()
        self.cashier_id = cashier_id
        self.sale = None
        self.service = CompleteSaleService(self.session)
        self.printer = EscPosPrinter()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Active Sale (scan barcodes):"))
        self.items = QListWidget(); layout.addWidget(self.items)
        self.barcode_in = QLineEdit(); self.barcode_in.setPlaceholderText("Scan / type barcode and press Enter"); layout.addWidget(self.barcode_in)
        self.total_lbl = QLabel("Total: 0.00"); layout.addWidget(self.total_lbl)
        self.btn_finalize = QPushButton("Finalize (Cash)"); layout.addWidget(self.btn_finalize)
        self.barcode_in.returnPressed.connect(self.add_barcode)
        self.btn_finalize.clicked.connect(self.finalize_sale)

        self._start_new_sale()

    def closeEvent(self, event):
        try:
            self.session.close()
        finally:
            super().closeEvent(event)

    def set_cashier(self, cashier_id: int | None):
        self.cashier_id = cashier_id
        self._start_new_sale()

    def _start_new_sale(self):
        self.items.clear()
        self.total_lbl.setText("Total: 0.00")
        self.sale = Sale(
            discount_total=0.0,
            cashier_id=self.cashier_id,
            status="open",
            payment_status="unpaid",
        )
        self.session.add(self.sale)
        self.session.commit()
        self.session.refresh(self.sale)

    def recompute_total(self):
        self.session.flush()
        subtotal = sum(l.qty * l.unit_price for l in self.sale.lines)
        tax_total = sum(((l.qty * l.unit_price) - l.discount) * float(l.tax_rate.rate) for l in self.sale.lines if l.tax_rate)
        grand_total = subtotal + tax_total - self.sale.discount_total
        self.total_lbl.setText(f"Total: {grand_total:.2f}")
        return grand_total
    def add_barcode(self):
        code = self.barcode_in.text().strip()
        if not code: return
        try:
            line = self.service.add_item(self.sale, code, qty=1)
            name = line.product.name if getattr(line, "product", None) else code
            self.items.addItem(f"{line.qty:.0f} x {name} @ {line.unit_price:.2f}")
            self.recompute_total()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
        finally:
            self.barcode_in.clear()
    def finalize_sale(self):
        try:
            grand_total = self.recompute_total()
            self.service.finalize(self.sale, payment_amount=grand_total, payment_method="cash")
            try:
                self.printer.print_receipt(self.sale, self.session)
            except Exception as pe:
                QMessageBox.warning(self, "Printer", f"Printed with stub or failed printer: {pe}")
            QMessageBox.information(self, "Sale completed", "Receipt captured (demo).")
            self._start_new_sale()
        except Exception as e:
            self.session.rollback()
            QMessageBox.warning(self, "Error", str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._startup_ok = False
        self.setWindowTitle("POS App - PyQt6")
        engine = get_engine(); self.SessionLocal = get_session_maker(engine)
        self.user = None
        self._role_name = "Cashier"
        # login
        with self.SessionLocal() as s:
            dlg = LoginDialog(s, self)
            if not dlg.exec():
                return
            logged_in_user = dlg.user
            role_obj = getattr(logged_in_user, "role", None)
            logged_in_role = role_obj.name if role_obj else "Cashier"
        self.stack = QStackedWidget()
        self.sales_page = SalesPage(self.SessionLocal, cashier_id=getattr(logged_in_user, "id", None))
        self.products_page = ProductsPage(self.SessionLocal)
        self.customers_page = CustomersPage(self.SessionLocal)
        self.reports_page = ReportsPage(self.SessionLocal)
        self.stack.addWidget(self.sales_page); self.stack.addWidget(self.products_page); self.stack.addWidget(self.customers_page); self.stack.addWidget(self.reports_page)
        self.setCentralWidget(self.stack)
        toolbar = QToolBar("Main"); self.addToolBar(toolbar)
        self.act_sales = QAction("Sales", self)
        self.act_products = QAction("Products", self)
        self.act_customers = QAction("Customers", self)
        self.act_reports = QAction("Reports", self)
        toolbar.addAction(self.act_sales); toolbar.addAction(self.act_products); toolbar.addAction(self.act_customers); toolbar.addAction(self.act_reports)
        menu = self.menuBar().addMenu("&Navigate"); menu.addAction(self.act_sales); menu.addAction(self.act_products); menu.addAction(self.act_customers); menu.addAction(self.act_reports)
        # Account menu
        account = self.menuBar().addMenu("&Account")
        act_change_pwd = QAction("Change Password", self)
        account.addAction(act_change_pwd)
        act_change_pwd.triggered.connect(self._change_password)
        act_logout = QAction("Log Out", self)
        account.addAction(act_logout)
        act_logout.triggered.connect(self._logout)
        # Devices menu
        devices = self.menuBar().addMenu("&Devices")
        act_test_printer = QAction("Test Printer", self)
        devices.addAction(act_test_printer)
        act_test_printer.triggered.connect(self._test_printer)
        act_prn_settings = QAction("Printer Settings", self)
        devices.addAction(act_prn_settings)
        act_prn_settings.triggered.connect(self._open_printer_settings)

        # RBAC: only Admin/Manager can access management pages
        self._set_logged_in_user(logged_in_user, logged_in_role)
        self.act_sales.triggered.connect(lambda: self.stack.setCurrentIndex(0))
        self.act_products.triggered.connect(lambda: (self.products_page.refresh(), self.stack.setCurrentIndex(1)))
        self.act_customers.triggered.connect(lambda: (self.customers_page.refresh(), self.stack.setCurrentIndex(2)))
        self.act_reports.triggered.connect(lambda: (self.reports_page.refresh(), self.stack.setCurrentIndex(3)))

        self._startup_ok = True

    def closeEvent(self, event):
        for page in (getattr(self, "sales_page", None), getattr(self, "products_page", None), getattr(self, "customers_page", None), getattr(self, "reports_page", None)):
            sess = getattr(page, "session", None)
            if sess is None:
                continue
            try:
                sess.close()
            except Exception:
                pass
        super().closeEvent(event)

    def _change_password(self):
        with self.SessionLocal() as s:
            d = ChangePasswordDialog(s, self.user, self)
            d.exec()

    def _open_printer_settings(self):
        dlg = PrinterSettingsDialog(self)
        dlg.exec()

    def _test_printer(self):
        try:
            self.sales_page.printer.test_page()
        except Exception as e:
            QMessageBox.warning(self, "Printer", f"Test failed: {e}")

    def _logout(self):
        confirm = QMessageBox.question(
            self,
            "Log Out",
            "End the current session and return to the sign-in screen?"
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.hide()
        with self.SessionLocal() as s:
            dlg = LoginDialog(s, self)
            if not dlg.exec():
                self.close()
                return
            new_user = dlg.user
            role_obj = getattr(new_user, "role", None)
            role_name = role_obj.name if role_obj else "Cashier"
            self._set_logged_in_user(new_user, role_name)
            self.sales_page.set_cashier(getattr(new_user, "id", None))
            self.stack.setCurrentIndex(0)
            self.show()

    def _set_logged_in_user(self, user, role_name=None):
        self.user = user
        if role_name is None:
            role_obj = getattr(user, "role", None)
            role_name = role_obj.name if role_obj else "Cashier"
        self._role_name = role_name
        self._apply_role_permissions()

    def _apply_role_permissions(self):
        is_manager = self._role_name in {"Admin", "Manager"}
        self.act_products.setEnabled(is_manager)
        self.act_customers.setEnabled(is_manager)
        self.act_reports.setEnabled(is_manager)

def run_app():
    import sys
    app = QApplication(sys.argv)
    win = MainWindow()
    if not getattr(win, "_startup_ok", False):
        sys.exit(0)
    win.resize(900, 650)
    win.show()
    sys.exit(app.exec())
