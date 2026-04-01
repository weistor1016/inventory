import os
from app import app
from models import db, DraftRecord

with app.app_context():
    db.create_all()
print("DraftRecord table created successfully!")
