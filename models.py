from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    
    # Added fields:
    role = db.Column(db.String(20), default='staff') # 'boss' or 'staff'
    display_name = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    has_own_inventory = db.Column(db.Boolean, default=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_active = db.Column(db.Boolean, default=True)

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
    client_role = db.Column(db.String(20), default='master')
    # This must match the table name 'user'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    
    quantity_out = db.Column(db.Integer, nullable=False)
    quantity_returned = db.Column(db.Integer, default=0)
    is_returned = db.Column(db.Boolean, default=False)
    is_sold = db.Column(db.Boolean, default=False)
    # Relationships mapped HERE
    item = db.relationship('Item', backref='records')
    place = db.relationship('Place', backref='records')
    client = db.relationship('Client', backref='records')
    
    # ADD THIS LINE:
    # This allows Jinja to use 'r.author.display_name'
    author = db.relationship('User', backref='user_records')
class DraftRecord(db.Model):
    __tablename__ = 'draft_record'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    client_role = db.Column(db.String(20), default='master')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quantity_out = db.Column(db.Integer, nullable=False)
    quantity_returned = db.Column(db.Integer, default=0)
    is_returned = db.Column(db.Boolean, default=False)
    item = db.relationship('Item')
    place = db.relationship('Place')
    client = db.relationship('Client')
    author = db.relationship('User')
