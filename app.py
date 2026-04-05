import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Item, Place, Client, DayRecord, User, DraftRecord
from datetime import datetime
from sqlalchemy import func, desc, case
from dotenv import load_dotenv



load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "traxxit_secret_key_2026")

os.environ['PGCLIENTENCODING'] = 'utf8'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    if not User.query.first():
        db.session.add_all([
            User(username='bossman', password='password123', role='boss', display_name='boss')
        ])
        db.session.commit()

@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return dict(current_user=user)
    return dict(current_user=None)


@app.before_request
def check_user_exists():
    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        if not user:
            session.clear()
            flash("Session expired or user deleted. Please log in again.", "warning")
            return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username'), password=request.form.get('password')).first()
        if user:
            if hasattr(user, 'is_active') and not user.is_active:
                flash("Account is deactivated.", "danger")
                return redirect(url_for('login'))
            session.update({'user_id': user.id, 'role': user.role, 'username': user.username})
            return redirect(url_for('index'))
        flash("Invalid Credentials", "danger")
    return render_template('login.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        user.display_name = request.form.get('display_name')
        db.session.commit()
        flash("Profile updated!", "success")
        return redirect(url_for('inventory'))
        
    return render_template('profile.html', user=user)

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
    user = db.session.get(User, session['user_id'])
    
    # Check if they selected a different user to view
    if 'view_user_id' in request.args:
        session['view_user_id'] = int(request.args.get('view_user_id'))
        return redirect(url_for('inventory'))
        
    view_id = user.id
    if not getattr(user, 'has_own_inventory', True):
        # If they don't have their own, use their selected view or default to the first boss/user with inventory
        view_id = session.get('view_user_id')
        if not view_id:
            first_user = User.query.filter_by(has_own_inventory=True).first()
            if first_user:
                view_id = first_user.id
                session['view_user_id'] = view_id
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_query = request.args.get('search', '')

    if request.method == 'POST':
        # Block POST if they don't have their own inventory
        if not getattr(user, 'has_own_inventory', True):
            flash("You do not have permission to modify inventory.", "danger")
            return redirect(url_for('inventory'))
            
        # --- BULK SAVE ---
        if 'bulk_save' in request.form:
            item_ids = request.form.getlist('item_ids[]')
            quantities = request.form.getlist('quantities[]')
            for i_id, qty in zip(item_ids, quantities):
                item = Item.query.filter_by(id=i_id, user_id=user.id).first()
                if item and item.is_active:
                    item.quantity = int(qty)
            db.session.commit()

        # --- ADD NEW ITEM ---
        else:
            name = request.form.get('name').strip()
            qty = int(request.form.get('qty'))
            item = Item.query.filter_by(user_id=user.id).filter(Item.name.ilike(name)).first()
            if item: 
                item.quantity += qty
                item.is_active = True 
            else: 
                db.session.add(Item(name=name, quantity=qty, user_id=user.id, is_active=True))
            db.session.commit()

        flash("Inventory updated.", "success")
        return redirect(url_for('inventory', search=search_query, per_page=per_page, page=page))

    # --- FETCH LOGIC ---
    lent_subquery = db.session.query(DayRecord.item_id).filter(DayRecord.quantity_returned < DayRecord.quantity_out, DayRecord.is_sold == False).distinct().subquery()

    items_query = Item.query.filter_by(user_id=view_id).filter(
        db.or_(Item.is_active == True, Item.id.in_(lent_subquery))
    )

    if search_query: 
        items_query = items_query.filter(Item.name.ilike(f"%{search_query}%"))
    
    pagination = items_query.order_by(Item.is_active.desc(), Item.name).paginate(page=page, per_page=per_page)
    
    for item in pagination.items:
        item.lent_out = db.session.query(func.sum(DayRecord.quantity_out)).filter(
            DayRecord.item_id == item.id, DayRecord.quantity_returned < DayRecord.quantity_out, DayRecord.is_sold == False
        ).scalar() or 0

    # Fetch users with inventory for the dropdown
    users_with_inventory = []
    if not getattr(user, 'has_own_inventory', True):
        users_with_inventory = User.query.filter_by(has_own_inventory=True, is_active=True).all()

    return render_template('inventory.html', 
                           pagination=pagination, 
                           items=pagination.items, 
                           search_query=search_query, 
                           per_page=per_page,
                           users_with_inventory=users_with_inventory,
                           view_id=view_id)

@app.route('/record', methods=['GET', 'POST'])
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
        item_ids = request.form.getlist('item_id')
        client_id = int(request.form['client_id'])
        qty = int(request.form['qty'])
        session['last_client_id'] = client_id
        
        for i_id in item_ids:
            item_id = int(i_id)
            item = Item.query.get(item_id)
            
            # Calculate how many are ALREADY in the shared basket across ALL places for this item
            already_in_basket = db.session.query(func.sum(DraftRecord.quantity_out - DraftRecord.quantity_returned)).filter(DraftRecord.item_id==item_id, DraftRecord.quantity_returned < DraftRecord.quantity_out).scalar() or 0
            
            if (already_in_basket + qty) > item.quantity:
                remaining = item.quantity - already_in_basket
                flash(f"Not enough stock for {item.name}! You only have {remaining} left available to add.", "danger")
                continue
            
            draft = DraftRecord.query.filter(DraftRecord.place_id==place_id, DraftRecord.client_id==client_id, DraftRecord.item_id==item_id, DraftRecord.quantity_returned < DraftRecord.quantity_out).first()
            
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
        'qty_returned': d.quantity_returned,
        'is_returned': d.quantity_returned >= d.quantity_out
    } for d in drafts]
    
    display_items = []
    for item in db_items:
        in_basket = sum(e['qty'] - e['qty_returned'] for e in temp_entries if e['item_id'] == item.id)
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


@app.route('/update_draft_qty/<int:draft_id>', methods=['POST'])
def update_draft_qty(draft_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    draft = DraftRecord.query.get_or_404(draft_id)
    
    try:
        new_qty = int(request.form.get('new_qty'))
        if new_qty < draft.quantity_returned:
            flash("Cannot set quantity below what has already been returned.", "danger")
            return redirect(url_for('record'))
            
        item = Item.query.get(draft.item_id)
        
        # Calculate how many are ALREADY in the shared basket excluding THIS draft
        already_in_basket = db.session.query(func.sum(DraftRecord.quantity_out - DraftRecord.quantity_returned)).filter(
            DraftRecord.item_id==draft.item_id, 
            DraftRecord.quantity_returned < DraftRecord.quantity_out,
            DraftRecord.id != draft_id
        ).scalar() or 0
        
        # Check against available stock
        net_change = new_qty - draft.quantity_out
        if net_change > 0:
            if (already_in_basket + (draft.quantity_out - draft.quantity_returned) + net_change) > item.quantity:
                remaining_stock_can_add = item.quantity - already_in_basket - (draft.quantity_out - draft.quantity_returned)
                flash(f"Not enough stock! You only have {remaining_stock_can_add} more available.", "danger")
                return redirect(url_for('record'))
                
        draft.quantity_out = new_qty
        draft.is_returned = draft.quantity_returned >= draft.quantity_out
        db.session.commit()
    except ValueError:
        flash("Invalid quantity.", "danger")
        
    return redirect(url_for('record'))

@app.route('/save_day', methods=['POST'])
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
                quantity_returned=draft.quantity_returned,
                is_returned=draft.quantity_returned >= draft.quantity_out,
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

@app.route('/toggle_sold/<int:record_id>')
def toggle_sold(record_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    record = db.session.get(DayRecord, record_id)
    item = db.session.get(Item, record.item_id)

    if not item.is_active:
        flash("Cannot modify archived items.", "warning")
        return redirect(request.referrer)

    if record.is_sold:
        record.is_sold = False
        flash(f"Unmarked {item.name} as Sold.", "info")
    else:
        record.is_sold = True
        record.is_returned = False 
        flash(f"{item.name} marked as Sold.", "success")
    
    db.session.commit()
    return redirect(request.referrer)

@app.route('/history')
def history():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    f_date = request.args.get('filter_date', '')
    f_place = request.args.get('filter_place', '').strip()

    query = db.session.query(
        func.date(DayRecord.timestamp).label('day'),
        DayRecord.place_id,
        Place.name.label('place_name'),
        func.sum(case((db.and_(DayRecord.quantity_returned < DayRecord.quantity_out, DayRecord.is_sold == False), 1), else_=0)).label('unreturned_count')
    ).join(Place)

    # Shared Visibility: Everyone can see all history records
    # Removed the user.role != 'boss' filter so all staff can see accumulated records
    # for the same racecourse on the same day.

    if f_date:
        query = query.filter(func.date(DayRecord.timestamp) == f_date)
    if f_place:
        query = query.filter(Place.name.ilike(f"%{f_place}%"))

    pagination = query.group_by(func.date(DayRecord.timestamp), DayRecord.place_id, Place.name)\
                      .order_by(desc('day'))\
                      .paginate(page=page, per_page=per_page)

    return render_template('history.html', 
                           pagination=pagination, 
                           f_date=f_date,
                           f_place=f_place,
                           per_page=per_page)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # Use distinct page variables for Places and Clients
    page_p = request.args.get('page_p', 1, type=int)
    page_c = request.args.get('page_c', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    search_p = request.args.get('search_p', '').strip()
    search_c = request.args.get('search_c', '').strip()

    if request.method == 'POST':
        # 1. Create Staff Account
        if 'create_account' in request.form and user.role == 'boss':
            existing_user = User.query.filter_by(username=request.form['new_username']).first()
            if not existing_user:
                new_user = User(
                    username=request.form['new_username'], 
                    password=request.form['new_password'], 
                    role='staff',
                    display_name=request.form.get('new_display_name', ''),
                    has_own_inventory='has_own_inventory' in request.form
                )
                db.session.add(new_user)
                flash(f"Staff {new_user.username} created successfully.", "success")
            else:
                flash("Username already exists!", "danger")

        # 2. Add Place (with duplicate check)
        elif 'add_place' in request.form:
            name = request.form['place_name'].strip()
            # Look for ANY place with this name, active or not
            existing_place = Place.query.filter_by(name=name).first()
            
            if existing_place:
                if not existing_place.is_active:
                    existing_place.is_active = True # Restore it
                    flash(f"'{name}' has been restored.", "success")
                else:
                    flash(f"'{name}' already exists in your list!", "warning")
            else:
                db.session.add(Place(name=name))
                flash(f"Added '{name}' successfully.", "success")

        # 3. Add Client (with duplicate check)
        elif 'add_client' in request.form:
            name = request.form['client_name'].strip()
            existing_client = Client.query.filter_by(name=name).first()
            
            if existing_client:
                if not existing_client.is_active:
                    existing_client.is_active = True # Restore it
                    flash(f"Client '{name}' has been restored.", "success")
                else:
                    flash(f"Client '{name}' already exists!", "warning")
            else:
                db.session.add(Client(name=name))
                flash(f"Added '{name}' successfully.", "success")

        db.session.commit()
        return redirect(url_for('settings'))

    # --- THE FIX: Use page_p and page_c here ---
    # Also added .order_by(name) for A-Z sorting
    p_query = Place.query.filter_by(is_active=True)
    if search_p: p_query = p_query.filter(Place.name.ilike(f"%{search_p}%"))
    p_pag = p_query.order_by(Place.name).paginate(page=page_p, per_page=per_page, count=False)
    
    c_query = Client.query.filter_by(is_active=True)
    if search_c: c_query = c_query.filter(Client.name.ilike(f"%{search_c}%"))
    c_pag = c_query.order_by(Client.name).paginate(page=page_c, per_page=per_page, count=False)
    
    staff = User.query.filter_by(role='staff').all() if user.role == 'boss' else []
    
    return render_template('settings.html', 
                           places_pagination=p_pag, 
                           clients_pagination=c_pag, 
                           search_p=search_p,
                           search_c=search_c,
                           staff_members=staff, 
                           user=user, 
                           per_page=per_page)

@app.route('/reset_session')
def reset_session():
    session.pop('current_place_id', None)
    flash("Session reset. Please select a new location.", "info")
    return redirect(url_for('record'))


@app.route('/bulk_toggle_session', methods=['POST'])
def bulk_toggle_session():
    if 'user_id' not in session: return {"error": "Unauthorized"}, 401
    data = request.json
    toggles = data.get('toggles', [])
    
    for t in toggles:
        draft_id = t.get('id')
        qty = int(t.get('qty', 0))
        action = t.get('action')
        
        draft = DraftRecord.query.get(draft_id)
        if draft:
            if action == 'return':
                if 0 < qty <= (draft.quantity_out - draft.quantity_returned):
                    draft.quantity_returned += qty
            elif action == 'undo':
                if 0 < qty <= draft.quantity_returned:
                    draft.quantity_returned -= qty
            draft.is_returned = draft.quantity_returned >= draft.quantity_out
            
    db.session.commit()
    return {"success": True}

@app.route('/toggle_session_return/<string:entry_id>', methods=['GET', 'POST'])
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
    if 'user_id' not in session: return redirect(url_for('login'))
    draft = DraftRecord.query.get(int(entry_id))
    if draft:
        db.session.delete(draft)
        db.session.commit()
        flash("Item removed from your current list.", "info")
    return redirect(url_for('record'))

@app.route('/history/<ts>/<int:place_id>')
def session_details(ts, place_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    
    place = db.session.get(Place, place_id)
    
    # Base Filter
    filters = [
        func.date(DayRecord.timestamp) == ts,
        DayRecord.place_id == place_id
    ]
    
    # Shared Visibility: Everyone can see all details
    # Removed the user.role != 'boss' filter.
    
    records = DayRecord.query.filter(*filters).all()
    
    if not records:
        flash("No records found or Access Denied.", "warning")
        return redirect(url_for('history'))

    grouped_data = {}
    for r in records:
        # Pass archiving status to the UI
        r.item_is_archived = not r.item.is_active
        client_name = r.client.name
        if client_name not in grouped_data:
            grouped_data[client_name] = []
        grouped_data[client_name].append(r)
        
    return render_template('session_details.html', 
                           grouped_data=grouped_data, 
                           place=place, 
                           ts=ts,
                           records=records)

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

@app.route('/toggle_return/<int:record_id>', methods=['GET', 'POST'])
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
    return redirect(url_for('session_details', ts=ts, place_id=record.place_id))

@app.route('/delete_session/<ts>/<int:place_id>')
def delete_session(ts, place_id):
    if 'user_id' not in session: 
        return redirect(url_for('login'))
        
    user = db.session.get(User, session['user_id'])
    if user.role != 'boss':
        flash("Permission Denied: Only the boss can delete history records.", "danger")
        return redirect(url_for('history'))
    
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
    if 'user_id' not in session: return redirect(url_for('login'))
    
    if type == 'place':
        target = Place.query.get(id)
    else:
        target = Client.query.get(id)

    if target:
        target.is_active = False  # This hides it from dropdowns
        db.session.commit()
        flash(f"{type.capitalize()} archived. History remains intact.", "warning")
    
    return redirect(url_for('settings'))


# --- BOSS STAFF MANAGEMENT ---
@app.route('/staff/<int:staff_id>/update_password', methods=['POST'])
def update_staff_password(staff_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    boss = User.query.get(session['user_id'])
    if boss.role != 'boss': return "Access Denied", 403
    
    staff = User.query.get_or_404(staff_id)
    new_password = request.form.get('new_password')
    if new_password:
        staff.password = new_password
        db.session.commit()
        flash(f"Password updated for {staff.username}.", "success")
    return redirect(url_for('settings'))

@app.route('/staff/<int:staff_id>/toggle_status', methods=['POST'])
def toggle_staff_status(staff_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    boss = User.query.get(session['user_id'])
    if boss.role != 'boss': return "Access Denied", 403
    
    staff = User.query.get_or_404(staff_id)
    # Check if is_active exists (if not, add dynamically)
    if not hasattr(staff, 'is_active') or staff.is_active is None:
        staff.is_active = True
    
    staff.is_active = not staff.is_active
    db.session.commit()
    status_str = "activated" if staff.is_active else "deactivated"
    flash(f"Staff account {staff.username} has been {status_str}.", "warning")
    return redirect(url_for('settings'))

@app.route('/staff/<int:staff_id>/delete', methods=['POST'])
def delete_staff(staff_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    boss = User.query.get(session['user_id'])
    if boss.role != 'boss': return "Access Denied", 403
    
    staff = User.query.get_or_404(staff_id)
    old_name = staff.display_name or staff.username
    
    try:
        # Check if they have any history records
        has_records = DayRecord.query.filter_by(user_id=staff.id).first() or DraftRecord.query.filter_by(user_id=staff.id).first()
        
        if has_records:
            # Soft delete: Hides them from staff list, frees up their username, but keeps their name for history
            staff.username = f"deleted_{staff.id}_{staff.username}"
            staff.role = 'deleted'
            staff.is_active = False
            db.session.commit()
            flash(f"Staff account '{old_name}' deleted. Their past records are preserved in History.", "warning")
        else:
            # Safe to hard delete if they have absolutely no records
            db.session.delete(staff)
            db.session.commit()
            flash(f"Staff account '{old_name}' deleted permanently.", "danger")
            
    except Exception as e:
        db.session.rollback()
        flash(f"Error processing deletion: {str(e)}", "danger")
        
    return redirect(url_for('settings'))