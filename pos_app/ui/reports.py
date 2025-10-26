
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox, QTabWidget,
                             QSizePolicy)
from PyQt6.QtCore import QDate
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timedelta
from pos_app.data.models import Sale, SaleLine, Product, Category, Payment, User
from jinja2 import Environment, BaseLoader
from weasyprint import HTML
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import uuid, tempfile
from pathlib import Path

REPORT_TEMPLATE = """
<!doctype html><html><head><meta charset="utf-8"><title>Sales Report</title>
<style>body{font-family:Arial,sans-serif}h1{font-size:18px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:6px;font-size:12px}th{background:#f0f0f0}</style>
</head><body>
<h1>Sales Report: {{ start }} – {{ end }}</h1>
<table><thead><tr><th>Date</th><th>Sales</th><th>Subtotal</th><th>Tax</th><th>Total</th></tr></thead><tbody>
{% for r in rows %}<tr><td>{{ r.date }}</td><td>{{ r.count }}</td><td>{{ '%.2f'|format(r.subtotal) }}</td><td>{{ '%.2f'|format(r.tax) }}</td><td>{{ '%.2f'|format(r.total) }}</td></tr>{% endfor %}
</tbody><tfoot><tr><th>Totals</th><th>{{ totals.count }}</th><th>{{ '%.2f'|format(totals.subtotal) }}</th><th>{{ '%.2f'|format(totals.tax) }}</th><th>{{ '%.2f'|format(totals.total) }}</th></tr></tfoot></table>
</body></html>
"""

def save_bar_chart(labels, values, title):
    fig, ax = plt.subplots()
    ax.bar(labels, values)
    ax.set_title(title)
    ax.set_ylabel("Total")
    fig.tight_layout()
    out_dir = Path(tempfile.gettempdir())
    path = out_dir / f"pos_chart_{uuid.uuid4().hex}.png"
    try:
        fig.savefig(path)
    finally:
        plt.close(fig)
    return str(path)

class ReportsPage(QWidget):
    def __init__(self, session_maker):
        super().__init__()
        self.SessionLocal = session_maker
        self.session: Session = self.SessionLocal()

        layout = QVBoxLayout(self)

        dates = QHBoxLayout()
        self.start = QDateEdit(); self.end = QDateEdit()
        self.start.setCalendarPopup(True); self.end.setCalendarPopup(True)
        today = QDate.currentDate()
        self.end.setDate(today); self.start.setDate(today.addDays(-30))
        dates.addWidget(QLabel("Start")); dates.addWidget(self.start)
        dates.addWidget(QLabel("End")); dates.addWidget(self.end)
        self.btn_run = QPushButton("Run Report")
        dates.addWidget(self.btn_run)
        layout.addLayout(dates)

        self.tabs = QTabWidget()
        # Tab 0: Summary by day
        self.tab_summary = QWidget(); self.summary_table = QTableWidget(0,5); self.summary_table.setHorizontalHeaderLabels(["Date","Sales","Subtotal","Tax","Total"])
        t0 = QVBoxLayout(self.tab_summary); t0.addWidget(self.summary_table)
        # Tab 1: By Category
        self.tab_cat = QWidget(); self.cat_table = QTableWidget(0,2); self.cat_table.setHorizontalHeaderLabels(["Category","Total"])
        t1 = QVBoxLayout(self.tab_cat); t1.addWidget(self.cat_table); self.btn_cat_csv = QPushButton("Export CSV"); t1.addWidget(self.btn_cat_csv)
        # Tab 2: By Cashier
        self.tab_cashier = QWidget(); self.cashier_table = QTableWidget(0,2); self.cashier_table.setHorizontalHeaderLabels(["Cashier","Total"])
        t2 = QVBoxLayout(self.tab_cashier); t2.addWidget(self.cashier_table); self.btn_cashier_csv = QPushButton("Export CSV"); t2.addWidget(self.btn_cashier_csv)
        # Tab 3: By Payment Method
        self.tab_pay = QWidget(); self.pay_table = QTableWidget(0,2); self.pay_table.setHorizontalHeaderLabels(["Method","Total"])
        t3 = QVBoxLayout(self.tab_pay); t3.addWidget(self.pay_table); self.btn_pay_csv = QPushButton("Export CSV"); t3.addWidget(self.btn_pay_csv)

        self.tabs.addTab(self.tab_summary, "Daily Summary")
        self.tabs.addTab(self.tab_cat, "By Category")
        self.tabs.addTab(self.tab_cashier, "By Cashier")
        self.tabs.addTab(self.tab_pay, "By Payment")

        layout.addWidget(self.tabs)

        # Exports
        btns = QHBoxLayout()
        self.btn_csv = QPushButton("Export Summary CSV")
        self.btn_pdf = QPushButton("Export Summary PDF")
        btns.addWidget(self.btn_csv); btns.addWidget(self.btn_pdf)
        layout.addLayout(btns)

        # Chart buttons
        chart_row = QHBoxLayout()
        self.btn_cat_chart = QPushButton("Category Chart")
        self.btn_cashier_chart = QPushButton("Cashier Chart")
        self.btn_pay_chart = QPushButton("Payment Chart")
        chart_row.addWidget(self.btn_cat_chart); chart_row.addWidget(self.btn_cashier_chart); chart_row.addWidget(self.btn_pay_chart)
        layout.addLayout(chart_row)

        # Wire
        self.btn_run.clicked.connect(self.refresh)
        self.btn_csv.clicked.connect(self.export_csv)
        self.btn_pdf.clicked.connect(self.export_pdf)
        self.btn_cat_csv.clicked.connect(lambda: self._export_kv_csv(self._cat_rows(), "categories.csv"))
        self.btn_cashier_csv.clicked.connect(lambda: self._export_kv_csv(self._cashier_rows(), "cashiers.csv"))
        self.btn_pay_csv.clicked.connect(lambda: self._export_kv_csv(self._pay_rows(), "payments.csv"))
        self.btn_cat_chart.clicked.connect(lambda: self._show_chart(self._cat_rows(), "Total by Category"))
        self.btn_cashier_chart.clicked.connect(lambda: self._show_chart(self._cashier_rows(), "Total by Cashier"))
        self.btn_pay_chart.clicked.connect(lambda: self._show_chart(self._pay_rows(), "Total by Payment Method"))

        self.refresh()

    def _date_range(self):
        start = self.start.date().toPyDate()
        end = self.end.date().toPyDate()
        return start, end

    def _summary_rows(self):
        start, end = self._date_range()
        q = (self.session.query(
                func.date(Sale.datetime).label("d"),
                func.count(Sale.id),
                func.coalesce(func.sum(Sale.subtotal),0.0),
                func.coalesce(func.sum(Sale.tax_total),0.0),
                func.coalesce(func.sum(Sale.grand_total),0.0)
            )
            .filter(Sale.datetime >= start, Sale.datetime < (end + timedelta(days=1)))
            .group_by(func.date(Sale.datetime))
            .order_by(func.date(Sale.datetime))
        )
        rows = [{"date": d.strftime("%Y-%m-%d") if isinstance(d, (date, datetime)) else str(d),
                 "count": int(c), "subtotal": float(s), "tax": float(t), "total": float(g)} for d,c,s,t,g in q]
        totals = {"count": sum(r["count"] for r in rows),
                  "subtotal": sum(r["subtotal"] for r in rows),
                  "tax": sum(r["tax"] for r in rows),
                  "total": sum(r["total"] for r in rows)}
        return rows, totals

    def _cat_rows(self):
        start, end = self._date_range()
        q = (self.session.query(Category.name, func.coalesce(func.sum(SaleLine.line_total),0.0))
             .join(Product, Product.id==SaleLine.product_id)
             .join(Category, Category.id==Product.category_id, isouter=True)
             .join(Sale, Sale.id==SaleLine.sale_id)
             .filter(Sale.datetime >= start, Sale.datetime < (end + timedelta(days=1)))
             .group_by(Category.name)
             .order_by(Category.name))
        return [(name or "Uncategorized", float(total)) for name, total in q]

    def _cashier_rows(self):
        start, end = self._date_range()
        q = (self.session.query(User.username, func.coalesce(func.sum(Sale.grand_total),0.0))
             .join(Sale, Sale.cashier_id==User.id, isouter=True)
             .filter(Sale.datetime >= start, Sale.datetime < (end + timedelta(days=1)))
             .group_by(User.username)
             .order_by(User.username))
        return [(name or "Unassigned", float(total)) for name, total in q]

    def _pay_rows(self):
        start, end = self._date_range()
        q = (self.session.query(Payment.method, func.coalesce(func.sum(Payment.amount),0.0))
             .join(Sale, Sale.id==Payment.sale_id)
             .filter(Sale.datetime >= start, Sale.datetime < (end + timedelta(days=1)))
             .group_by(Payment.method)
             .order_by(Payment.method))
        return [(m or "Unknown", float(total)) for m, total in q]

    def refresh(self):
        rows, totals = self._summary_rows()
        self.summary_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.summary_table.setItem(i,0,QTableWidgetItem(r["date"]))
            self.summary_table.setItem(i,1,QTableWidgetItem(str(r["count"])))
            self.summary_table.setItem(i,2,QTableWidgetItem(f"{r['subtotal']:.2f}"))
            self.summary_table.setItem(i,3,QTableWidgetItem(f"{r['tax']:.2f}"))
            self.summary_table.setItem(i,4,QTableWidgetItem(f"{r['total']:.2f}"))
        self.summary_table.resizeColumnsToContents()

        # fill other tabs
        cats = self._cat_rows()
        self.cat_table.setRowCount(len(cats))
        for i, (name, total) in enumerate(cats):
            self.cat_table.setItem(i,0,QTableWidgetItem(name))
            self.cat_table.setItem(i,1,QTableWidgetItem(f"{total:.2f}"))
        cash = self._cashier_rows()
        self.cashier_table.setRowCount(len(cash))
        for i, (name, total) in enumerate(cash):
            self.cashier_table.setItem(i,0,QTableWidgetItem(name))
            self.cashier_table.setItem(i,1,QTableWidgetItem(f"{total:.2f}"))
        pays = self._pay_rows()
        self.pay_table.setRowCount(len(pays))
        for i, (name, total) in enumerate(pays):
            self.pay_table.setItem(i,0,QTableWidgetItem(name))
            self.pay_table.setItem(i,1,QTableWidgetItem(f"{total:.2f}"))

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "sales_summary.csv", "CSV Files (*.csv)")
        if not path: return
        rows, totals = self._summary_rows()
        import csv
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["Date","Sales","Subtotal","Tax","Total"])
                for r in rows:
                    w.writerow([r["date"], r["count"], f"{r['subtotal']:.2f}", f"{r['tax']:.2f}", f"{r['total']:.2f}"])
                w.writerow([]); w.writerow(["TOTALS", totals["count"], f"{totals['subtotal']:.2f}", f"{totals['tax']:.2f}", f"{totals['total']:.2f}"])
        except OSError as exc:
            QMessageBox.critical(self, "Export error", f"Could not write CSV file.\n\nDetails: {exc}")

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "sales_summary.pdf", "PDF Files (*.pdf)")
        if not path: return
        rows, totals = self._summary_rows()
        html = Environment(loader=BaseLoader()).from_string(REPORT_TEMPLATE).render(
            rows=rows, totals=totals, start=self.start.date().toString("yyyy-MM-dd"), end=self.end.date().toString("yyyy-MM-dd")
        )
        try:
            HTML(string=html).write_pdf(path)
        except Exception as exc:
            QMessageBox.critical(self, "Export error", f"Failed to generate PDF.\n\nDetails: {exc}")

    def _export_kv_csv(self, rows, default_name):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", default_name, "CSV Files (*.csv)")
        if not path: return
        import csv
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["Key","Total"])
                for k, v in rows:
                    w.writerow([k, f"{v:.2f}"])
        except OSError as exc:
            QMessageBox.critical(self, "Export error", f"Could not write CSV file.\n\nDetails: {exc}")

    def _show_chart(self, rows, title):
        labels = [k for k,_ in rows]
        values = [v for _,v in rows]
        if not labels: 
            QMessageBox.information(self, "No data", "Nothing to chart for this range."); return
        try:
            path = save_bar_chart(labels, values, title)
        except Exception as exc:
            QMessageBox.critical(self, "Chart error", f"Failed to create chart.\n\nDetails: {exc}")
            return
        QMessageBox.information(self, "Chart saved", f"Chart saved to: {path}")
