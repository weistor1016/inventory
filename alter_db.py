from app import app
from models import db
from sqlalchemy import text
with app.app_context():
    db.session.execute(text('ALTER TABLE draft_record ADD COLUMN is_sold BOOLEAN DEFAULT FALSE;'))
    db.session.commit()
    print("Done")
