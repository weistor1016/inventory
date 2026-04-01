import re

with open('/mnt/c/Users/wei/Desktop/inventory/app.py', 'r') as f:
    content = f.read()

toggle_return_new = """@app.route('/toggle_return/<int:record_id>', methods=['GET', 'POST'])
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
            DayRecord.is_returned == False,
            DayRecord.is_sold == False
        ).scalar() or 0
        
        if still_out == 0:
            db.session.delete(item)
            db.session.commit()
    
    ts = record.timestamp.strftime('%Y-%m-%d')
    return redirect(url_for('session_details', ts=ts, place_id=record.place_id))"""

content = re.sub(r"@app\.route\('/toggle_return/<int:record_id>'\)\ndef toggle_return\(record_id\):.*?return redirect\(url_for\('session_details', ts=ts, place_id=record\.place_id\)\)", toggle_return_new, content, flags=re.DOTALL)

with open('/mnt/c/Users/wei/Desktop/inventory/app.py', 'w') as f:
    f.write(content)
