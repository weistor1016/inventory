import re

with open('/mnt/c/Users/wei/Desktop/inventory/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_func = """def delete_staff(staff_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    boss = User.query.get(session['user_id'])
    if boss.role != 'boss': return "Access Denied", 403
    
    staff = User.query.get_or_404(staff_id)
    # Re-assign or check records? We can just delete if cascade lets us, or we might need to handle foreign keys
    try:
        db.session.delete(staff)
        db.session.commit()
        flash(f"Staff account {staff.username} deleted permanently.", "danger")
    except Exception as e:
        db.session.rollback()
        flash("Cannot delete staff with existing history records. Deactivate them instead.", "danger")
        
    return redirect(url_for('settings'))"""

new_func = """def delete_staff(staff_id):
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
        
    return redirect(url_for('settings'))"""

content = content.replace(old_func, new_func)

with open('/mnt/c/Users/wei/Desktop/inventory/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched delete_staff!")
