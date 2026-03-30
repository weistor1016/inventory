import os, uuid
from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, Item, Place, Client, DayRecord, User
from datetime import date
from sqlalchemy import func

app = Flask(__name__)
app.secret_key = "trackit_secret_key_2026"

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'inventory.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    if not User.query.first():
        db.session.add_all([
            User(username='bossman', password='password123', role='boss'),
            User(username='staff_john', password='password123', role='staff')
        ])
        db.session.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username'), password=request.form.get('password')).first()
        if user:
            session.update({'user_id': user.id, 'role': user.role, 'username': user.username})
            return redirect(url_for('index'))
        flash("Invalid Credentials", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if 'user_id' not in session: return redirect(url_for('login'))
    user_id = session['user_id']
    search_query = request.args.get('search', '')

    if request.method == 'POST':
        name = request.form.get('name').strip()
        qty = int(request.form.get('qty'))
        item = Item.query.filter_by(user_id=user_id).filter(Item.name.ilike(name)).first()
        if item: item.quantity += qty
        else: db.session.add(Item(name=name, quantity=qty, user_id=user_id))
        db.session.commit()
        return redirect(url_for('inventory'))

    items = Item.query.filter_by(user_id=user_id)
    if search_query: items = items.filter(Item.name.ilike(f"%{search_query}%"))
    return render_template('inventory.html', items=items.all(), search_query=search_query)

@app.route('/record', methods=['GET', 'POST'])
def record():
    if 'user_id' not in session: return redirect(url_for('login'))
    place_id = session.get('current_place_id')
    
    # 1. Location Selection
    if not place_id:
        if request.method == 'POST':
            session['current_place_id'] = request.form['place_id']
            session['temp_entries'] = []
            return redirect(url_for('record'))
        return render_template('select_place.html', places=Place.query.all())

    # 2. Add/Merge Entry Logic
    if request.method == 'POST' and 'add_entry' in request.form:
        item_id = int(request.form['item_id'])
        client_id = int(request.form['client_id'])
        qty = int(request.form['qty'])
        
        temp_list = session.get('temp_entries', [])
        
        # --- MERGE CHECK START ---
        found = False
        for entry in temp_list:
            # If the Client and Item both match, just add the quantity
            if entry['client_id'] == client_id and entry['item_id'] == item_id:
                entry['qty'] += qty
                found = True
                break
        
        # If no match was found, create a brand new row
        if not found:
            item = Item.query.get(item_id)
            client = Client.query.get(client_id)
            temp_list.append({
                'id': str(uuid.uuid4()), 
                'client_id': client.id, 
                'client_name': client.name, 
                'item_id': item.id, 
                'item_name': item.name, 
                'qty': qty, 
                'is_returned': False
            })
        # --- MERGE CHECK END ---
        
        session['temp_entries'] = temp_list
        session.modified = True
        return redirect(url_for('record'))

    # 3. Live Stock Calculation (Same as before)
    db_items = Item.query.filter_by(user_id=session['user_id']).all()
    temp_entries = session.get('temp_entries', [])
    
    display_items = []
    for item in db_items:
        in_basket = sum(e['qty'] for e in temp_entries if e['item_id'] == item.id and not e['is_returned'])
        live_qty = max(0, item.quantity - in_basket)
        display_items.append({'id': item.id, 'name': item.name, 'live_qty': live_qty})

    grouped_entries = {}
    for entry in temp_entries:
        c_name = entry['client_name']
        if c_name not in grouped_entries:
            grouped_entries[c_name] = []
        grouped_entries[c_name].append(entry)

    return render_template('records.html', 
                           place=Place.query.get(place_id), 
                           items=display_items, 
                           clients=Client.query.all(), 
                           grouped_entries=grouped_entries)

@app.route('/save_day')
def save_day():
    temp_entries = session.get('temp_entries', [])
    place_id = session.get('current_place_id')
    for e in temp_entries:
        rec = DayRecord(item_id=e['item_id'], place_id=place_id, client_id=e['client_id'], 
                        user_id=session['user_id'], quantity_out=e['qty'], is_returned=e['is_returned'])
        if not e['is_returned']:
            item = Item.query.get(e['item_id'])
            item.quantity -= e['qty']
        db.session.add(rec)
    db.session.commit()
    session.pop('temp_entries', None); session.pop('current_place_id', None)
    return redirect(url_for('history'))

@app.route('/history')
def history():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    query = db.session.query(func.date(DayRecord.timestamp).label('day'), DayRecord.place_id, 
                             Place.name.label('place_name'), func.count(DayRecord.id).label('total_items')
                             ).join(Place).group_by('day', DayRecord.place_id).order_by(db.desc('day'))
    pagination = query.paginate(page=page, per_page=per_page)
    return render_template('history_sessions.html', sessions=pagination.items, pagination=pagination, 
                           places=Place.query.all(), per_page=per_page)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    page_p = request.args.get('page_p', 1, type=int)
    page_c = request.args.get('page_c', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)

    if request.method == 'POST':
        if 'create_account' in request.form and user.role == 'boss':
            db.session.add(User(username=request.form['new_username'], password=request.form['new_password'], role='staff'))
        elif 'add_place' in request.form:
            db.session.add(Place(name=request.form['place_name']))
        elif 'add_client' in request.form:
            db.session.add(Client(name=request.form['client_name']))
        db.session.commit()
        return redirect(url_for('settings'))

    p_pag = Place.query.paginate(page=page_p, per_page=per_page)
    c_pag = Client.query.paginate(page=page_c, per_page=per_page)
    staff = User.query.filter_by(role='staff').all() if user.role == 'boss' else []
    return render_template('settings.html', places_pagination=p_pag, clients_pagination=c_pag, staff_members=staff, user=user, per_page=per_page)

@app.route('/reset_session')
def reset_session():
    # Clear the temporary recording data from the browser session
    session.pop('current_place_id', None)
    session.pop('temp_entries', None)
    flash("Session reset. Please select a new location.", "info")
    return redirect(url_for('record'))

# Helper routes for toggles/deletes
@app.route('/toggle_session_return/<string:entry_id>')
def toggle_session_return(entry_id):
    temp = session.get('temp_entries', [])
    for e in temp:
        if e['id'] == entry_id:
            e['is_returned'] = not e['is_returned']
    session['temp_entries'] = temp
    session.modified = True
    return redirect(url_for('record'))

@app.route('/delete_item/<int:id>')
def delete_item(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Securely find the item belonging ONLY to the logged-in user
    item = Item.query.filter_by(id=id, user_id=session['user_id']).first()
    
    if item:
        try:
            db.session.delete(item)
            db.session.commit()
            flash(f"Item '{item.name}' removed from your inventory.", "info")
        except Exception as e:
            db.session.rollback()
            flash("Error: Cannot delete item because it is linked to existing history records.", "danger")
    else:
        flash("Item not found or access denied.", "danger")
        
    return redirect(url_for('inventory'))

@app.route('/remove_entry/<string:entry_id>')
def remove_entry(entry_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # Get the current temporary list from the session
    temp_list = session.get('temp_entries', [])
    
    # Filter the list to keep everything EXCEPT the item we clicked
    # We use a list comprehension for a clean, Pythonic removal
    updated_list = [e for e in temp_list if e['id'] != entry_id]
    
    # Save the updated list back to the session
    session['temp_entries'] = updated_list
    session.modified = True  # Tell Flask the session data changed
    
    flash("Item removed from your current list.", "info")
    return redirect(url_for('record'))

@app.route('/history/<ts>/<int:place_id>')
def session_details(ts, place_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 1. Fetch the Place object to show the name at the top
    place = Place.query.get_or_404(place_id)
    
    # 2. Get all records for that specific day and location
    # We use func.date() to match the date string from the URL
    records = DayRecord.query.filter(
        func.date(DayRecord.timestamp) == ts,
        DayRecord.place_id == place_id
    ).all()
    
    # 3. Group the records by Client Name for the UI
    grouped_data = {}
    for r in records:
        client_name = r.client.name
        if client_name not in grouped_data:
            grouped_data[client_name] = []
        grouped_data[client_name].append(r)
        
    return render_template('session_details.html', 
                           grouped_data=grouped_data, 
                           place=place, 
                           ts=ts)

@app.route('/update_item/<int:id>', methods=['POST'])
def update_item(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    new_qty = request.form.get('new_qty')
    item = Item.query.filter_by(id=id, user_id=session['user_id']).first()
    
    if item and new_qty is not None:
        item.quantity = int(new_qty)
        db.session.commit()
        flash(f"Updated {item.name} quantity to {new_qty}.", "success")
    
    return redirect(url_for('inventory'))

@app.route('/bulk_update_inventory', methods=['POST'])
def bulk_update_inventory():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # Loop through all form data
    for key, value in request.form.items():
        if key.startswith('qty_'):
            # Extract the ID from 'qty_5' -> 5
            item_id = int(key.split('_')[1])
            item = Item.query.filter_by(id=item_id, user_id=session['user_id']).first()
            
            if item:
                item.quantity = int(value)
    
    db.session.commit()
    flash("Inventory updated successfully!", "success")
    return redirect(url_for('inventory'))

@app.route('/toggle_return/<int:record_id>')
def toggle_return(record_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    record = DayRecord.query.get_or_404(record_id)
    item = Item.query.get(record.item_id)
    
    # Logic: If we are CHANGING it to 'Returned', add stock back.
    # If we are CHANGING it back to 'Out', subtract stock again.
    if record.is_returned: # It was returned, now it's going back out
        item.quantity -= record.quantity_out
    else: # It was out, now it's coming back in
        item.quantity += record.quantity_out
        
    record.is_returned = not record.is_returned
    db.session.commit()
    
    ts = record.timestamp.strftime('%Y-%m-%d')
    return redirect(url_for('session_details', ts=ts, place_id=record.place_id))

@app.route('/delete_session/<ts>/<int:place_id>')
def delete_session(ts, place_id):
    if 'user_id' not in session: 
        return redirect(url_for('login'))
    
    # 1. Filter all records that match the date string and the place ID
    records = DayRecord.query.filter(
        func.date(DayRecord.timestamp) == ts,
        DayRecord.place_id == place_id
    ).all()
    
    if records:
        try:
            # 2. Loop through and delete each record found
            for r in records:
                db.session.delete(r)
            
            db.session.commit()
            flash(f"Session for {ts} has been deleted.", "warning")
        except Exception as e:
            db.session.rollback()
            flash("Error: Could not delete the session.", "danger")
    else:
        flash("Session not found.", "danger")
        
    return redirect(url_for('history'))

@app.route('/delete_entry/<string:type>/<int:id>')
def delete_entry(type, id):
    if 'user_id' not in session: 
        return redirect(url_for('login'))
    
    try:
        if type == 'place':
            target = Place.query.get(id)
            msg = f"Location '{target.name}' deleted."
        elif type == 'client':
            target = Client.query.get(id)
            msg = f"Client '{target.name}' deleted."
        else:
            flash("Invalid deletion type.", "danger")
            return redirect(url_for('settings'))

        if target:
            db.session.delete(target)
            db.session.commit()
            flash(msg, "warning")
        else:
            flash("Item not found.", "danger")
            
    except Exception as e:
        db.session.rollback()
        flash("Could not delete. This item might be linked to existing history records.", "danger")

    return redirect(url_for('settings'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)