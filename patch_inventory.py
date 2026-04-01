import re

with open('/mnt/c/Users/wei/Desktop/inventory/app.py', 'r') as f:
    content = f.read()

# Replace inventory function
inventory_new = """@app.route('/inventory', methods=['GET', 'POST'])
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
    lent_subquery = db.session.query(DayRecord.item_id).filter(DayRecord.is_returned == False, DayRecord.is_sold == False).distinct().subquery()

    items_query = Item.query.filter_by(user_id=view_id).filter(
        db.or_(Item.is_active == True, Item.id.in_(lent_subquery))
    )

    if search_query: 
        items_query = items_query.filter(Item.name.ilike(f"%{search_query}%"))
    
    pagination = items_query.order_by(Item.is_active.desc(), Item.name).paginate(page=page, per_page=per_page)
    
    for item in pagination.items:
        item.lent_out = db.session.query(func.sum(DayRecord.quantity_out)).filter(
            DayRecord.item_id == item.id, DayRecord.is_returned == False, DayRecord.is_sold == False
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
                           view_id=view_id)"""

content = re.sub(r"@app\.route\('/inventory', methods=\['GET', 'POST'\]\)\ndef inventory\(\):.*?return render_template\('inventory\.html'.*?\)", inventory_new, content, flags=re.DOTALL)

with open('/mnt/c/Users/wei/Desktop/inventory/app.py', 'w') as f:
    f.write(content)
