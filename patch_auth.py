import re

with open('/mnt/c/Users/wei/Desktop/inventory/app.py', 'r') as f:
    content = f.read()

if 'check_user_exists' not in content:
    hook = """
@app.before_request
def check_user_exists():
    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        if not user:
            session.clear()
            flash("Session expired or user deleted. Please log in again.", "warning")
            return redirect(url_for('login'))
"""
    # Insert after db.init_app(app) or before first route
    idx = content.find('@app.route')
    if idx != -1:
        content = content[:idx] + hook + '\n' + content[idx:]
        
with open('/mnt/c/Users/wei/Desktop/inventory/app.py', 'w') as f:
    f.write(content)
