import re

with open('/mnt/c/Users/wei/Desktop/inventory/app.py', 'r') as f:
    content = f.read()

# 1. Update /inventory queries
content = content.replace("DayRecord.is_returned == False", "DayRecord.quantity_returned < DayRecord.quantity_out")
content = content.replace("DraftRecord.quantity_out)).filter_by(item_id=item_id, is_returned=False)", "DraftRecord.quantity_out - DraftRecord.quantity_returned)).filter(DraftRecord.item_id==item_id, DraftRecord.quantity_returned < DraftRecord.quantity_out)")
content = content.replace("DraftRecord.query.filter_by(place_id=place_id, client_id=client_id, item_id=item_id, is_returned=False)", "DraftRecord.query.filter(DraftRecord.place_id==place_id, DraftRecord.client_id==client_id, DraftRecord.item_id==item_id, DraftRecord.quantity_returned < DraftRecord.quantity_out)")
content = content.replace("db.and_(DayRecord.is_returned == False, DayRecord.is_sold == False), 1", "db.and_(DayRecord.quantity_returned < DayRecord.quantity_out, DayRecord.is_sold == False), 1")

# Update temp_entries in /record
rec_old = """temp_entries = [{
        'id': str(d.id), 
        'client_id': d.client_id, 
        'client_name': d.client.name, 
        'item_id': d.item_id, 
        'item_name': d.item.name, 
        'qty': d.quantity_out, 
        'is_returned': d.is_returned
    } for d in drafts]"""
rec_new = """temp_entries = [{
        'id': str(d.id), 
        'client_id': d.client_id, 
        'client_name': d.client.name, 
        'item_id': d.item_id, 
        'item_name': d.item.name, 
        'qty': d.quantity_out, 
        'qty_returned': d.quantity_returned,
        'is_returned': d.quantity_returned >= d.quantity_out
    } for d in drafts]"""
content = content.replace(rec_old, rec_new)

# Update in_basket
content = content.replace("in_basket = sum(e['qty'] for e in temp_entries if e['item_id'] == item.id and not e['is_returned'])", "in_basket = sum(e['qty'] - e['qty_returned'] for e in temp_entries if e['item_id'] == item.id)")

# Update save_day
save_old = """new_record = DayRecord(
                item_id=draft.item_id,
                place_id=place_id,
                client_id=draft.client_id,
                user_id=session['user_id'],
                quantity_out=draft.quantity_out,
                is_returned=draft.is_returned,
                timestamp=final_timestamp
            )"""
save_new = """new_record = DayRecord(
                item_id=draft.item_id,
                place_id=place_id,
                client_id=draft.client_id,
                user_id=session['user_id'],
                quantity_out=draft.quantity_out,
                quantity_returned=draft.quantity_returned,
                is_returned=draft.quantity_returned >= draft.quantity_out,
                timestamp=final_timestamp
            )"""
content = content.replace(save_old, save_new)

# toggle_session_return
tog_old = """@app.route('/toggle_session_return/<string:entry_id>', methods=['GET', 'POST'])
def toggle_session_return(entry_id):
    draft = DraftRecord.query.get(int(entry_id))
    if draft:
        try:
            qty = int(request.form.get('qty', draft.quantity_out)) if request.method == 'POST' else draft.quantity_out
        except ValueError:
            qty = draft.quantity_out
            
        if qty <= 0 or qty > draft.quantity_out:
            flash("Invalid quantity.", "danger")
            return redirect(url_for('record'))
            
        if qty == draft.quantity_out:
            draft.is_returned = not draft.is_returned
        else:
            draft.quantity_out -= qty
            new_draft = DraftRecord(
                item_id=draft.item_id,
                place_id=draft.place_id,
                client_id=draft.client_id,
                user_id=draft.user_id,
                timestamp=draft.timestamp,
                quantity_out=qty,
                is_returned=not draft.is_returned
            )
            db.session.add(new_draft)
        db.session.commit()
    return redirect(url_for('record'))"""

tog_new = """@app.route('/toggle_session_return/<string:entry_id>', methods=['GET', 'POST'])
def toggle_session_return(entry_id):
    draft = DraftRecord.query.get(int(entry_id))
    if draft:
        try:
            qty = int(request.form.get('qty', draft.quantity_out - draft.quantity_returned)) if request.method == 'POST' else (draft.quantity_out - draft.quantity_returned)
        except ValueError:
            qty = draft.quantity_out - draft.quantity_returned
            
        action = request.form.get('action', 'return')
        
        if action == 'return':
            if qty <= 0 or (draft.quantity_returned + qty) > draft.quantity_out:
                flash("Invalid quantity.", "danger")
                return redirect(url_for('record'))
            draft.quantity_returned += qty
        elif action == 'undo':
            if qty <= 0 or (draft.quantity_returned - qty) < 0:
                flash("Invalid undo quantity.", "danger")
                return redirect(url_for('record'))
            draft.quantity_returned -= qty
            
        draft.is_returned = draft.quantity_returned >= draft.quantity_out
        db.session.commit()
    return redirect(url_for('record'))"""
content = content.replace(tog_old, tog_new)

# toggle_return
tr_old = """@app.route('/toggle_return/<int:record_id>', methods=['GET', 'POST'])
def toggle_return(record_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    record = DayRecord.query.get_or_404(record_id)
    item = Item.query.get(record.item_id)
    
    try:
        qty = int(request.form.get('qty', record.quantity_out)) if request.method == 'POST' else record.quantity_out
    except ValueError:
        qty = record.quantity_out
        
    if qty <= 0 or qty > record.quantity_out:
        flash("Invalid quantity specified.", "danger")
        return redirect(request.referrer)
        
    if qty == record.quantity_out:
        if record.is_returned:
            item.quantity -= record.quantity_out
        else:
            item.quantity += record.quantity_out
        record.is_returned = not record.is_returned
    else:
        record.quantity_out -= qty
        
        if record.is_returned:
            item.quantity -= qty
        else:
            item.quantity += qty
            
        new_record = DayRecord(
            item_id=record.item_id,
            place_id=record.place_id,
            client_id=record.client_id,
            user_id=record.user_id,
            timestamp=record.timestamp,
            quantity_out=qty,
            is_returned=not record.is_returned,
            is_sold=record.is_sold
        )
        db.session.add(new_record)
        
    db.session.commit()

    if item.quantity == 0:
        still_out = db.session.query(func.sum(DayRecord.quantity_out)).filter(
            DayRecord.item_id == item.id,
            DayRecord.quantity_returned < DayRecord.quantity_out,
            DayRecord.is_sold == False
        ).scalar() or 0
        
        if still_out == 0:
            db.session.delete(item)
            db.session.commit()
    
    ts = record.timestamp.strftime('%Y-%m-%d')
    return redirect(url_for('session_details', ts=ts, place_id=record.place_id))"""

tr_new = """@app.route('/toggle_return/<int:record_id>', methods=['GET', 'POST'])
def toggle_return(record_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    record = DayRecord.query.get_or_404(record_id)
    item = Item.query.get(record.item_id)
    
    try:
        qty = int(request.form.get('qty', record.quantity_out - record.quantity_returned)) if request.method == 'POST' else (record.quantity_out - record.quantity_returned)
    except ValueError:
        qty = record.quantity_out - record.quantity_returned
        
    action = request.form.get('action', 'return')
    
    if action == 'return':
        if qty <= 0 or (record.quantity_returned + qty) > record.quantity_out:
            flash("Invalid quantity specified.", "danger")
            return redirect(request.referrer)
        record.quantity_returned += qty
        item.quantity += qty
    elif action == 'undo':
        if qty <= 0 or (record.quantity_returned - qty) < 0:
            flash("Invalid undo quantity.", "danger")
            return redirect(request.referrer)
        record.quantity_returned -= qty
        item.quantity -= qty
        
    record.is_returned = record.quantity_returned >= record.quantity_out
    db.session.commit()

    if item.quantity == 0:
        still_out = db.session.query(func.sum(DayRecord.quantity_out - DayRecord.quantity_returned)).filter(
            DayRecord.item_id == item.id,
            DayRecord.quantity_returned < DayRecord.quantity_out,
            DayRecord.is_sold == False
        ).scalar() or 0
        
        if still_out == 0:
            db.session.delete(item)
            db.session.commit()
    
    ts = record.timestamp.strftime('%Y-%m-%d')
    return redirect(url_for('session_details', ts=ts, place_id=record.place_id))"""
content = content.replace(tr_old, tr_new)

with open('/mnt/c/Users/wei/Desktop/inventory/app.py', 'w') as f:
    f.write(content)
