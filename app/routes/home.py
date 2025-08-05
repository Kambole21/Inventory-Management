from flask import render_template, Blueprint, session, request, url_for, redirect, flash
from bson.objectid import ObjectId
from app import db  
from app.routes.login import login_required

bp = Blueprint('home', __name__)

@bp.route('/Home_Page')
@login_required
def home():
    user_id = session.get('user_id')
    user_data = None
    stats = {}
    inventories_count = 0
    equipment_list = []

    if user_id:
        try:
            user_data = db.user_collection.find_one({'_id': ObjectId(user_id)})
            if not user_data:
                flash('User not found. Please log in again.', 'error')
                session.clear()
                return redirect(url_for('login.log'))

            # Total equipment
            total_equipments = db.inventory_collection.aggregate([
                {"$unwind": "$rows"},
                {"$group": {"_id": None, "count": {"$sum": 1}}}
            ]).next().get('count', 0) if db.inventory_collection.count_documents({}) > 0 else 0
            
            # Working, Faulty, Absolute equipment
            status_counts = db.inventory_collection.aggregate([
                {"$unwind": "$rows"},
                {"$group": {
                    "_id": "$rows.status",
                    "count": {"$sum": 1}
                }}
            ])
            stats = {doc['_id']: doc['count'] for doc in status_counts if doc['_id']}
            stats['total'] = total_equipments
            
            # Number of inventories submitted
            inventories_count = db.inventory_collection.count_documents({})
            
            # ICT equipment totals
            equipment_totals = db.inventory_collection.aggregate([
                {"$unwind": "$rows"},
                {"$group": {
                    "_id": "$rows.ict_equipment",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}}
            ])
            equipment_list = list(equipment_totals)

        except Exception as e:
            flash(f'Error retrieving data: {str(e)}', 'error')
            logger.error(f"Error in home route for user_id {user_id}: {str(e)}")
    
    return render_template('home.html', user_data=user_data, stats=stats, inventories_count=inventories_count, equipment_list=equipment_list)