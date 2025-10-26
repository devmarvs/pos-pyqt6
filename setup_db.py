from pos_app.data.db import get_engine, get_session_maker, Base
from pos_app.data.models import *
from pos_app.auth import hash_password
from sqlalchemy.orm import Session

def seed_data(db: Session):
    if not db.query(Category).first():
        grocery = Category(name="Grocery")
        drinks = Category(name="Drinks")
        db.add_all([grocery, drinks]); db.flush()
        vat = TaxRate(name="VAT 21%", rate=0.21); db.add(vat); db.flush()
        cola = Product(sku="COLA-330", barcode="1234567890123", name="Cola 330ml", category=grocery, tax_rate=vat, price=1.20, cost=0.40)
        water = Product(sku="WATER-500", barcode="2234567890123", name="Water 500ml", category=drinks, tax_rate=vat, price=0.80, cost=0.10)
        db.add_all([cola, water]); db.flush()
        store = InventoryLocation(name="Main Store"); db.add(store); db.flush()
        db.add_all([Inventory(product=cola, location=store, qty_on_hand=50, reorder_point=10),
                    Inventory(product=water, location=store, qty_on_hand=80, reorder_point=20)])
    if not db.query(Role).first():
        admin = Role(name="Admin"); manager = Role(name="Manager"); cashier = Role(name="Cashier")
        db.add_all([admin, manager, cashier]); db.flush()
        db.flush()
        db.add(User(username="admin", password_hash="changeme", role_id=admin.id, active=True))
    db.commit()

def main():
    engine = get_engine()
    Base.metadata.create_all(engine)
    SessionLocal = get_session_maker(engine)
    with SessionLocal() as s: seed_data(s)
    print("DB ready.")

if __name__ == "__main__":
    main()
