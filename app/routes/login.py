from flask import Blueprint, render_template, request, url_for, flash, redirect, session
from app.forms import LoginForm
from werkzeug.security import check_password_hash
import logging
from app import db

bp = Blueprint('login', __name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@bp.route('/')
@bp.route('/Login_Page', methods=['GET', 'POST'])
def log():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = db.user_collection.find_one({'email': email})
        if user and check_password_hash(user['password'], password):
            # Fetch and store user details in session
            session['user_id'] = str(user['_id'])
            session['full_name'] = f"{user['fname']} {user['lname']}"
            session['role'] = user.get('role', 'normal')  # Fetch role from database, default to 'normal'
            session['email'] = user['email']  # Store email for convenience
            logger.debug(f"User logged in: {session['email']}, role: {session['role']}, _id: {session['user_id']}")
            flash('Login successful!', 'success')
            return redirect(url_for('home.home'))
        else:
            logger.warning(f"Failed login attempt for email: {email}")
            flash('Invalid email or password.', 'error')
    return render_template('login.html', form=form, role=session.get('role', 'normal'))