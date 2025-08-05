from flask import render_template, Blueprint, session, request, url_for, flash, redirect
from app import db
from bson.objectid import ObjectId
from datetime import datetime

bp = Blueprint('recent', __name__)

@bp.route('/Recent_inventories')
def recent():
    user_id = session.get('user_id')
    user_data = None
    if user_id:
        user_data = db.user_collection.find_one({'_id': ObjectId(user_id)})
    user_name = session.get('full_name', 'Not Logged In')
    recent_inventories = db.inventory_collection.find().sort('submission_date', -1).limit(100)  # Last 100 submissions
    return render_template('recent.html', user_name=user_name, recent_inventories=recent_inventories, user_data=user_data)

@bp.route('/delete_inventory/<inventory_id>')
def delete_inventory(inventory_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('You must be logged in to delete an inventory.', 'error')
        return redirect(url_for('recent.recent'))

    user_data = db.user_collection.find_one({'_id': ObjectId(user_id)})
    if not user_data or user_data.get('role') != 'admin':
        flash('You do not have permission to delete this inventory.', 'error')
        return redirect(url_for('recent.recent'))

    # Delete from both collections
    db.inventory_collection.delete_one({'_id': ObjectId(inventory_id)})
    db.my_files_collection.delete_one({'_id': ObjectId(inventory_id)})
    flash('Inventory deleted successfully.', 'success')
    return redirect(url_for('recent.recent'))