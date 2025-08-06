from flask import render_template, Blueprint, session, request
from app import db
from bson.objectid import ObjectId
from app.routes.login import login_required

bp = Blueprint('view_stats', __name__, url_prefix='/stats')

@bp.route('/view_stats')
@bp.login_required
def view_stats():
    user_id = session.get('user_id')
    user_data = None
    if user_id:
        user_data = db.user_collection.find_one({'_id': ObjectId(user_id)})
    
    entity = request.args.get('entity', '').replace('_', ' ')
    entity_type = request.args.get('type', 'office')
    
    if entity_type == 'office':
        stats = db.inventory_collection.aggregate([
            {"$match": {"department_school": entity}},
            {"$unwind": "$rows"},
            {
                "$group": {
                    "_id": {"username": "$rows.username", "position": "$rows.position", "status": "$rows.status"},
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id.username": 1, "_id.position": 1}}
        ])
    else:  # school
        stats = db.inventory_collection.aggregate([
            {"$match": {"department_school": entity}},
            {"$unwind": "$rows"},
            {
                "$group": {
                    "_id": {"username": "$rows.username", "position": "$rows.position", "status": "$rows.status"},
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id.username": 1, "_id.position": 1}}
        ])
    
    stats_list = list(stats)
    return render_template('view_stats.html', user_data=user_data, stats=stats_list, entity=entity, entity_type=entity_type)