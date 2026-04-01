import re

with open('/mnt/c/Users/wei/Desktop/inventory/app.py', 'r') as f:
    content = f.read()

record_new = """@app.route('/record', methods=['GET', 'POST'])
def record():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
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
        
        # Calculate how many are ALREADY in the shared basket across ALL places for this item
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

    # Determine whose items to show
    view_id = user.id
    if not getattr(user, 'has_own_inventory', True):
        view_id = session.get('view_user_id')
        if not view_id:
            first_user = User.query.filter_by(has_own_inventory=True).first()
            if first_user:
                view_id = first_user.id
                session['view_user_id'] = view_id

    # 3. Live Stock Calculation (Ordered A-Z)
    db_items = Item.query.filter_by(user_id=view_id, is_active=True).order_by(Item.name).all()
    
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
                           today_date=today_str)"""

content = re.sub(r"@app\.route\('/record', methods=\['GET', 'POST'\]\)\ndef record\(\):.*?return render_template\('records\.html'.*?\)", record_new, content, flags=re.DOTALL)

with open('/mnt/c/Users/wei/Desktop/inventory/app.py', 'w') as f:
    f.write(content)
