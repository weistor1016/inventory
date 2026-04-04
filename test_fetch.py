from app import app
with app.app_context():
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['user_id'] = 1
        res = c.get('/settings')
        text = res.get_data(as_text=True)
        if "RED BANNER" in text:
            print("BANNER FOUND IN FLASK")
        else:
            print("BANNER MISSING IN FLASK")
