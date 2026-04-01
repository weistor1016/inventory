with open('/mnt/c/Users/wei/Desktop/inventory/models.py', 'r') as f:
    content = f.read()

content = content.replace("quantity_out = db.Column(db.Integer, nullable=False)\n    is_returned = db.Column(db.Boolean, default=False)", "quantity_out = db.Column(db.Integer, nullable=False)\n    quantity_returned = db.Column(db.Integer, default=0)\n    is_returned = db.Column(db.Boolean, default=False)")

with open('/mnt/c/Users/wei/Desktop/inventory/models.py', 'w') as f:
    f.write(content)
