from flask import render_template, Blueprint, session, request, url_for
from bson.objectid import ObjectId
from app import db  
from app.routes.login import login_required

bp = Blueprint('stats', __name__)

@bp.route('/Stats_Page')
@login_required
def stats():
    user_id = session.get('user_id')
    user_data = None
    stats_data = {}
    if user_id:
        user_data = db.user_collection.find_one({'_id': ObjectId(user_id)})
        # Total equipment by office
        office_stats = db.inventory_collection.aggregate([
            {
                "$match": {
                    "department_school": {
                        "$nin": [
                            "School of Business Studies", "School of Agriculture and Natural Resources",
                            "School of Education", "School of Social Sciences",
                            "School of Natural and Applied Sciences", "School of Engineering and Technology",
                            "School of Nursing and Midwifery (Town campus)", "School of Medicine and Health Sciences (Livingstone Campus)"
                        ]
                    }
                }
            },
            {"$unwind": "$rows"},
            {
                "$group": {
                    "_id": "$department_school",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}}
        ])
        stats_data['offices'] = list(office_stats)

        # Total equipment by school
        school_stats = db.inventory_collection.aggregate([
            {
                "$match": {
                    "department_school": {
                        "$in": [
                            "School of Business Studies", "School of Agriculture and Natural Resources",
                            "School of Education", "School of Social Sciences",
                            "School of Natural and Applied Sciences", "School of Engineering and Technology",
                            "School of Nursing and Midwifery (Town campus)", "School of Medicine and Health Sciences (Livingstone Campus)"
                        ]
                    }
                }
            },
            {"$unwind": "$rows"},
            {
                "$group": {
                    "_id": "$department_school",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}}
        ])
        stats_data['schools'] = list(school_stats)

    return render_template('stats.html', user_data=user_data, stats_data=stats_data)