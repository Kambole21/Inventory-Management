from flask import Flask, Blueprint, session, request, flash 
bp = Blueprint('client', __name__)
@bp.route('/Client Report')
def client ():
	return render_template('client.html')