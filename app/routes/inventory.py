from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from app import db
from bson.objectid import ObjectId
from datetime import datetime
app.routes.login import login_required

bp = Blueprint('inventory', __name__)

@bp.route('/Inventory')
@bp.login_required
def inventory():
    user_id = session.get('user_id')
    user_data = None
    if user_id:
        user_data = db.user_collection.find_one({'_id': ObjectId(user_id)})
    return render_template('inventory.html', user_data=user_data)

@bp.route('/upload_inventory', methods=['POST'])
def upload_inventory():
    from flask import session
    csv_data = request.form.get('csvData')
    user_id = session.get('user_id')
    if csv_data:
        import json
        try:
            data = json.loads(csv_data)
            inventory_doc = {
                'inventory_date': datetime.now().strftime('%Y-%m-%d'),
                'submission_date': datetime.now().isoformat(),
                'rows': data,
                'created_by': session.get('full_name', 'Unknown User'),
                'user_id': user_id  # Link to the user
            }
            # Save to my_files_collection first
            my_files_result = db.my_files_collection.insert_one(inventory_doc)
            flash('Inventory saved to My Files. Submit from My Files to finalize.', 'success')
            return redirect(url_for('my_files.files'))
        except Exception as e:
            flash(f'Failed to upload inventory: {str(e)}', 'error')
    return redirect(url_for('recent.recent'))