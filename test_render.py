import sys
from app import app, db, User
with app.app_context():
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['user_id'] = 1 # bossman
        response = c.get('/settings')
        with open('rendered_settings.html', 'w', encoding='utf-8') as f:
            f.write(response.get_data(as_text=True))
