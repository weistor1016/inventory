import re

with open('/mnt/c/Users/wei/Desktop/inventory/app.py', 'r') as f:
    content = f.read()

# 1. Add import
if 'DraftRecord' not in content:
    content = content.replace('from models import db, Item, Place, Client, DayRecord, User', 'from models import db, Item, Place, Client, DayRecord, User, DraftRecord')

# 2. Extract ranges
def replace_func(content, func_name, new_func_code):
    pattern = r"@app\.route\('(/[^']*)'(?:, methods=\[[^\]]+\])?\)\ndef " + func_name + r"\(.*?\):.*?(?=\n@app\.route|\Z)"
    match = re.search(pattern, content, flags=re.DOTALL)
    if match:
        return content[:match.start()] + new_func_code + content[match.end():]
    return content

# 3. Code chunks
record_code = """@app.route('/record', methods=['GET', 'POST'])
def record():
    if 'user_id' not in session: return redirect(url_for('login'))
    place_id = session.get('current_place_id')
    
    # 1. Location Selection (Ordered A-Z)
    if not place_id:
        if request.method == 'POST':
            session['current_place_id'] = request.form['place_id']
            return redirect(url_for('record'))
        return render_template('select_place.html', 
                               places = Place.query.filter_by(is_active=True).order_by(Place.name).all())

    # 2. Add/Merge Entry Logic
    if request.method == 'POST' and 'add_entry' in request.form:
        item_id = int(request.form['item_id'])
        client_id = int(request.form['client_id'])
        qty = int(request.form['qty'])
        
        item = Item.query.get(item_id)
        
        already_in_basket = db.session.query(func.sum(DraftRecord.quantity_out)).filter_by(item_id=item_id, is_returned=False).scalar() or 0
        
        if (already_in_basket + qty) > item.quantity:
            remaining = item.quantity - already_in_basket
            flash(f"Not enough stock! You only have {remaining} left available to add.", "danger")
            return redirect(url_for('record'))
        
        session['last_client_id'] = client_id
        
        draft = DraftRecord.query.filter_by(place_id=place_id, client_id=client_id, item_id=item_id, is_returned=False).first()
        
        if draft:
            draft.quantity_out += qty
        else:
            draft = DraftRecord(
                item_id=item.id,
                place_id=place_id,
                client_id=client_id,
                user_id=session['user_id'],
                quantity_out=qty,
                is_returned=False
            )
            db.session.add(draft)
            
        db.session.commit()
        return redirect(url_for('record'))

    # 3. Live Stock Calculation (Ordered A-Z)
    db_items = Item.query.filter_by(user_id=session['user_id']).order_by(Item.name).all()
    
    drafts = DraftRecord.query.filter_by(place_id=place_id).all()
    temp_entries = [{
        'id': str(d.id), 
        'client_id': d.client_id, 
        'client_name': d.client.name, 
        'item_id': d.item_id, 
        'item_name': d.item.name, 
        'qty': d.quantity_out, 
        'is_returned': d.is_returned
    } for d in drafts]
    
    display_items = []
    for item in db_items:
        in_basket = sum(e['qty'] for e in temp_entries if e['item_id'] == item.id and not e['is_returned'])
        live_qty = max(0, item.quantity - in_basket)
        display_items.append({'id': item.id, 'name': item.name, 'live_qty': live_qty})

    # 4. Grouping & Sorting Clients A-Z
    clients = Client.query.filter_by(is_active=True).order_by(Client.name).all()
    
    grouped_entries = {}
    for entry in temp_entries:
        c_name = entry['client_name']
        if c_name not in grouped_entries:
            grouped_entries[c_name] = []
        grouped_entries[c_name].append(entry)

    today_str = datetime.now().strftime('%Y-%m-%d')

    return render_template('records.html', 
                           place=Place.query.get(place_id), 
                           items=display_items, 
                           clients=clients, 
                           grouped_entries=grouped_entries,
                           last_client_id=session.get('last_client_id'),
                           today_date=today_str)
"""

save_day_code = """@app.route('/save_day', methods=['POST'])
def save_day():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    place_id = session.get('current_place_id')
    drafts = DraftRecord.query.filter_by(place_id=place_id).all()
    
    if not drafts or not place_id:
        flash("No records to save!", "warning")
        return redirect(url_for('record'))

    date_str = request.form.get('manual_date')
    try:
        chosen_date = datetime.strptime(date_str, '%Y-%m-%d')
        now = datetime.now()
        final_timestamp = chosen_date.replace(hour=now.hour, minute=now.minute, second=now.second)
    except Exception:
        final_timestamp = datetime.now()

    try:
        for draft in drafts:
            new_record = DayRecord(
                item_id=draft.item_id,
                place_id=place_id,
                client_id=draft.client_id,
                user_id=session['user_id'],
                quantity_out=draft.quantity_out,
                is_returned=draft.is_returned,
                timestamp=final_timestamp
            )
            db.session.add(new_record)
            db.session.delete(draft)
                
        db.session.commit()
        session.pop('current_place_id', None)
        
        flash(f"Session saved for {final_timestamp.strftime('%d %b %Y')}!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error saving records: {str(e)}", "danger")

    return redirect(url_for('history'))
"""

reset_session_code = """@app.route('/reset_session')
def reset_session():
    session.pop('current_place_id', None)
    flash("Session reset. Please select a new location.", "info")
    return redirect(url_for('record'))
"""

toggle_session_return_code = """@app.route('/toggle_session_return/<string:entry_id>')
def toggle_session_return(entry_id):
    draft = DraftRecord.query.get(int(entry_id))
    if draft:
        draft.is_returned = not draft.is_returned
        db.session.commit()
    return redirect(url_for('record'))
"""

remove_entry_code = """@app.route('/remove_entry/<string:entry_id>')
def remove_entry(entry_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    draft = DraftRecord.query.get(int(entry_id))
    if draft:
        db.session.delete(draft)
        db.session.commit()
        flash("Item removed from your current list.", "info")
    return redirect(url_for('record'))
"""

content = replace_func(content, 'record', record_code)
content = replace_func(content, 'save_day', save_day_code)
content = replace_func(content, 'reset_session', reset_session_code)
content = replace_func(content, 'toggle_session_return', toggle_session_return_code)
content = replace_func(content, 'remove_entry', remove_entry_code)

with open('/mnt/c/Users/wei/Desktop/inventory/app.py', 'w') as f:
    f.write(content)
