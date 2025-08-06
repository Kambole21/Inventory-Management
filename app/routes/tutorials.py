from flask import Blueprint, render_template, request, session, url_for, redirect
from app import db
from bson.objectid import ObjectId
from app.routes.login import login_required
bp = Blueprint('tutorial', __name__)

@bp.route('/Tutorial')
@login_required
def tut():
	user_id = session.get('user_id')
	user_data = None
	if user_id:
		user_data = db.user_collection.find_one({'id': ObjectId(user_id)})


	return render_template('tutorial.html', user_data = user_data)
