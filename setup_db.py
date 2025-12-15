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
    # Demo RBAC users
    roles_by_name = {r.name: r for r in db.query(Role).all()}
    for role_name in ("Admin", "Manager", "Cashier"):
        if role_name not in roles_by_name:
            role = Role(name=role_name)
            db.add(role)
            db.flush()
            roles_by_name[role_name] = role

    default_users = [
        ("admin", "Admin"),
        ("manager", "Manager"),
        ("cashier", "Cashier"),
    ]
    for username, role_name in default_users:
        existing = db.query(User).filter(User.username == username).first()
        if existing is not None:
            continue
        role = roles_by_name[role_name]
        db.add(
            User(
                username=username,
                password_hash=hash_password("changeme"),
                role_id=role.id,
                active=True,
            )
        )
    db.commit()

def main():
    engine = get_engine()
    Base.metadata.create_all(engine)
    SessionLocal = get_session_maker(engine)
    with SessionLocal() as s: seed_data(s)
    print("DB ready.")

if __name__ == "__main__":
    main()
