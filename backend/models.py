"""SQLAlchemy models mapping to database tables."""
from flask_sqlalchemy import SQLAlchemy

# WHY: Provide ORM mappings for easier DB access; extend with more models later.
db = SQLAlchemy()


class Product(db.Model):
    __tablename__ = 'Products'

    product_id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    product_name = db.Column(db.String(200), nullable=False)

    # HOW: Add additional fields based on schemadb when expanding features.

