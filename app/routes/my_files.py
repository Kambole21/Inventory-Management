from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from bson.objectid import ObjectId
from app import db
from datetime import datetime
from app.routes.login import login_required

bp = Blueprint('my_files', __name__)

@bp.route('/MyFiles_Page')
@login_required
def files():
    user_id = session.get('user_id')
    user_data = None
    inventories = []
    if user_id:
        user_data = db.user_collection.find_one({'_id': ObjectId(user_id)})
        inventories = list(db.my_files_collection.find({'user_id': user_id}))
        for inventory in inventories:
            if '_id' in inventory:
                inventory['_id'] = str(inventory['_id'])
            inventory['is_uploaded'] = db.inventory_collection.find_one({'user_id': user_id, 'inventory_date': inventory['inventory_date'], 'rows': inventory['rows']}) is None
    return render_template('my_files.html', user_data=user_data, inventories=inventories)

@bp.route('/submit_my_file/<inventory_id>', methods=['POST'])
def submit_my_file(inventory_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to submit inventory.', 'error')
        return redirect(url_for('my_files.files'))
    inventory = db.my_files_collection.find_one({'_id': ObjectId(inventory_id), 'user_id': user_id})
    if inventory:
        try:
            del inventory['_id']
            inventory['submission_date'] = datetime.utcnow().isoformat()
            inventory_result = db.inventory_collection.insert_one(inventory)
            db.my_files_collection.delete_one({'_id': ObjectId(inventory_id)})
            flash('Inventory submitted to Recent Inventories successfully!', 'success')
        except Exception as e:
            flash(f'Error submitting inventory: {str(e)}', 'error')
        return redirect(url_for('recent.recent'))
    flash('Inventory not found or unauthorized.', 'error')
    return redirect(url_for('my_files.files'))

@bp.route('/view_my_file/<inventory_id>')
def view_my_file(inventory_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view inventory.', 'error')
        return redirect(url_for('my_files.files'))
    inventory = db.my_files_collection.find_one({'_id': ObjectId(inventory_id), 'user_id': user_id})
    if inventory:
        if '_id' in inventory:
            inventory['_id'] = str(inventory['_id'])
        return render_template('view_inventory.html', inventory_data=inventory, user_data=db.user_collection.find_one({'_id': ObjectId(user_id)}))
    flash('Inventory not found or unauthorized.', 'error')
    return redirect(url_for('my_files.files'))

@bp.route('/delete_my_file/<inventory_id>', methods=['POST'])
def delete_my_file(inventory_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to delete inventory.', 'error')
        return redirect(url_for('my_files.files'))
    result = db.my_files_collection.delete_one({'_id': ObjectId(inventory_id), 'user_id': user_id})
    if result.deleted_count > 0:
        flash('Inventory deleted successfully!', 'success')
    else:
        flash('Inventory not found or unauthorized.', 'error')
    return redirect(url_for('my_files.files'))