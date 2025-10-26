from sqlalchemy.orm import Session
from pos_app.data.models import Product, Sale, SaleLine, Payment, Inventory

class CompleteSaleService:
    def __init__(self, db: Session):
        self.db = db

    def add_item(self, sale: Sale, barcode: str, qty: float = 1):
        product = self.db.query(Product).filter(Product.barcode == barcode, Product.active == True).first()
        if not product:
            raise ValueError("Item not found")
        line_total = float(qty) * float(product.price)
        line = SaleLine(sale=sale, product_id=product.id, qty=qty,
                        unit_price=float(product.price), line_total=line_total, tax_rate=product.tax_rate)
        sale.lines.append(line)

    def finalize(self, sale: Sale, payment_amount: float, payment_method: str = "cash"):
        subtotal = sum(l.qty * l.unit_price for l in sale.lines)
        tax_total = 0.0
        for l in sale.lines:
            if l.tax_rate:
                tax_total += (l.qty * l.unit_price - l.discount) * float(l.tax_rate.rate)
        grand_total = subtotal + tax_total - sale.discount_total
        sale.subtotal = subtotal; sale.tax_total = tax_total; sale.grand_total = grand_total
        sale.status = "completed"
        sale.payment_status = "paid" if abs(payment_amount - grand_total) < 0.01 else "partial"
        self.db.add(Payment(sale=sale, method=payment_method, amount=payment_amount, status="captured"))
        for l in sale.lines:
            inv = self.db.query(Inventory).filter(Inventory.product_id == l.product_id).first()
            if inv:
                inv.qty_on_hand = float(inv.qty_on_hand) - float(l.qty)
        self.db.commit()
        return sale
