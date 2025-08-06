from flask import Blueprint, render_template, request, url_for, jsonify, flash, redirect, session
from app.forms import RegistrationForm
from werkzeug.security import generate_password_hash
import logging
from app.routes.login import login_required

bp = Blueprint('registration', __name__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@bp.route('/Register_Page', methods=['GET', 'POST'])
@login_required
def reg():
    from app import db, pending_users  
    form = RegistrationForm()
    if form.validate_on_submit():
        if pending_users.find_one({'email': form.email.data}):
            logger.error(f"Email {form.email.data} already pending")
            flash('This email is already pending approval.', 'error')
            return render_template('registration.html', form=form)
        from app import user_collection
        if user_collection.find_one({'email': form.email.data}):
            logger.error(f"Email {form.email.data} already registered")
            flash('This email is already registered.', 'error')
            return render_template('registration.html', form=form)
        
        try:
            user_data = {
                'email': form.email.data,
                'fname': form.fname.data,
                'lname': form.lname.data,
                'role': form.role.data,
                'phone_number': form.phone_number.data,
                'student_number': form.student_number.data if form.role.data == 'normal' else None,
                'password': generate_password_hash(form.password.data),
                'status': 'pending'
            }
            result = pending_users.insert_one(user_data)  # Insert into pending_users
            if result.inserted_id:
                logger.debug(f"User inserted into pending_users with ID: {result.inserted_id}, data: {user_data}")
                flash('Registration successful! You will receive an email to confirm registration, Thank You.', 'success')
                return redirect(url_for('login.log'))
            else:
                logger.error("Insert operation returned no inserted_id")
                flash('Failed to register user: Insert operation failed.', 'error')
        except Exception as e:
            logger.error(f"Error inserting user: {str(e)}")
            flash(f'Failed to register user: {str(e)}', 'error')
    else:
        logger.debug(f"Validation errors: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", 'error')
    return render_template('registration.html', form=form)