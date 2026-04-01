import re

with open('/mnt/c/Users/wei/Desktop/inventory/app.py', 'r') as f:
    content = f.read()

old_func = r"@app\.route\('/toggle_session_return/<string:entry_id>'\)\ndef toggle_session_return\(entry_id\):\n    draft = DraftRecord\.query\.get\(int\(entry_id\)\)\n    if draft:\n        draft\.is_returned = not draft\.is_returned\n        db\.session\.commit\(\)\n    return redirect\(url_for\('record'\)\)"

new_func = """@app.route('/toggle_session_return/<string:entry_id>', methods=['GET', 'POST'])
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

content = re.sub(old_func, new_func, content, flags=re.DOTALL)

with open('/mnt/c/Users/wei/Desktop/inventory/app.py', 'w') as f:
    f.write(content)
