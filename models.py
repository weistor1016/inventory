from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='staff') # 'boss' or 'staff'

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # ❌ I DELETED the 'records = db.relationship...' line from here

class Place(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) 
    is_active = db.Column(db.Boolean, default=True)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class DayRecord(db.Model):
    __tablename__ = 'day_record'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # IDs
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    quantity_out = db.Column(db.Integer, nullable=False)
    is_returned = db.Column(db.Boolean, default=False)

    # Relationships mapped HERE instead. 
    # I changed the backref to 'records' so if you ever type Item.records in your code, it still works perfectly!
    item = db.relationship('Item', backref='records')
    place = db.relationship('Place', backref='records')
    client = db.relationship('Client', backref='records')