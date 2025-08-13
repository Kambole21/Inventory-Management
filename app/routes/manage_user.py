from flask import Blueprint, render_template, request, url_for, flash, redirect, session
from app import db, user_collection, pending_users, mail
from flask_mail import Message
from bson.objectid import ObjectId
from app.forms import EditUserForm
import logging
from app.routes.login import login_required

bp = Blueprint('manage_user', __name__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@bp.route('/Management_Page', methods=['GET', 'POST'])
@login_required
def manage():
    user_id = session.get('user_id')
    user_data = None
    if user_id:
        user_data = user_collection.find_one({'_id': ObjectId(user_id)})
    
    # Get view_type from query parameter or form (default to 'pending')
    view_type = request.args.get('view_type', 'pending')
    
    # Fetch users based on view_type
    if view_type == 'approved':
        users = list(user_collection.find({'status': 'approved'}))
    else:
        users = list(pending_users.find({'status': 'pending'}))
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        action = request.form.get('action')
        
        if not user_id or not action:
            logger.error("Missing user_id or action in form data")
            flash('Invalid request data.', 'error')
            return redirect(url_for('manage_user.manage', view_type=view_type))
            
        try:
            if view_type == 'pending':
                user = pending_users.find_one({'_id': ObjectId(user_id)})
                if not user:
                    logger.error(f"User with _id {user_id} not found in pending_users")
                    flash('User not found.', 'error')
                    return redirect(url_for('manage_user.manage', view_type=view_type))
                
                if action == 'approve':
                    # Move user to user_collection
                    user_data = user.copy()
                    user_data.pop('_id', None)
                    user_data['status'] = 'approved'
                    result = user_collection.insert_one(user_data)
                    
                    if result.inserted_id:
                        pending_users.delete_one({'_id': ObjectId(user_id)})
                        logger.debug(f"User {user['email']} approved, moved to user_collection with new _id: {result.inserted_id}")
                        try:
                            login_url = url_for('login.log', _external = True)
                            send_email(
                                user['email'], 
                                'Account Approved', 
                                f'Your account has been approved. You can now log in. Click on the link to login {login_url}'
                            )
                            flash(f'User {user["email"]} approved successfully.', 'success')
                        except Exception as e:
                            logger.error(f"Email sending failed but user approved: {str(e)}")
                            flash(f'User approved but failed to send email: {str(e)}', 'warning')
                    else:
                        logger.error(f"Failed to insert user with _id {user_id} into user_collection")
                        flash('Failed to approve user. Please try again.', 'error')
                        
                elif action == 'deny':
                    # Remove the user from pending_users
                    result = pending_users.delete_one({'_id': ObjectId(user_id)})
                    if result.deleted_count > 0:
                        logger.debug(f"User {user['email']} denied and removed from pending_users with _id: {user_id}")
                        try:
                            send_email(
                                user['email'], 
                                'Account Denied', 
                                'Your account registration has been denied.'
                            )
                            flash(f'User {user["email"]} denied and removed.', 'success')
                        except Exception as e:
                            logger.error(f"Email sending failed but user denied: {str(e)}")
                            flash(f'User denied but failed to send email: {str(e)}', 'warning')
                    else:
                        logger.error(f"Failed to delete user with _id: {user_id} from pending_users")
                        flash('Failed to deny user. Please try again.', 'error')
                        
            else:  # view_type == 'approved'
                user = user_collection.find_one({'_id': ObjectId(user_id)})
                if not user:
                    logger.error(f"User with _id {user_id} not found in user_collection")
                    flash('User not found.', 'error')
                    return redirect(url_for('manage_user.manage', view_type=view_type))
                
                if action == 'delete':
                    # Prevent deleting the current user
                    if str(user['_id']) == str(user_id):
                        logger.error(f"Cannot delete the current logged-in user: {user_id}")
                        flash('You cannot delete your own account.', 'error')
                        return redirect(url_for('manage_user.manage', view_type=view_type))
                    
                    result = user_collection.delete_one({'_id': ObjectId(user_id)})
                    if result.deleted_count > 0:
                        logger.debug(f"User {user['email']} deleted from user_collection with _id: {user_id}")
                        flash(f'User {user["email"]} deleted successfully.', 'success')
                    else:
                        logger.error(f"Failed to delete user with _id: {user_id} from user_collection")
                        flash('Failed to delete user. Please try again.', 'error')
                        
                elif action.startswith('role_'):
                    new_role = action.split('_')[1]
                    result = user_collection.update_one(
                        {'_id': ObjectId(user_id)},
                        {'$set': {'role': new_role}}
                    )
                    if result.modified_count > 0:
                        logger.debug(f"User {user['email']} role updated to {new_role}")
                        flash(f'User {user["email"]} role updated to {new_role}.', 'success')
                    else:
                        logger.error(f"Failed to update role for user with _id: {user_id}")
                        flash('Failed to update user role. Please try again.', 'error')
                        
            logger.error(f"Invalid action: {action}")
            flash('Invalid action.', 'error')
                
        except Exception as e:
            logger.error(f"Error processing user management: {str(e)}")
            flash(f'An error occurred: {str(e)}', 'error')
            
        return redirect(url_for('manage_user.manage', view_type=view_type))
    
    return render_template('manage_user.html', pending_users=users, view_type=view_type, user_data=user_data)

@bp.route('/edit_user/<user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # Get current user from session
    current_user_id = session.get('user_id')
    current_user = user_collection.find_one({'_id': ObjectId(current_user_id)})
    
    # Check if current user is admin
    if not current_user or current_user.get('role') != 'admin':
        flash('You do not have permission to edit users.', 'error')
        return redirect(url_for('manage_user.manage'))
    
    # Get the user to be edited
    user_to_edit = user_collection.find_one({'_id': ObjectId(user_id)})
    if not user_to_edit:
        flash('User not found.', 'error')
        return redirect(url_for('manage_user.manage'))
    
    # Fetch user_data for the current user (for template rendering)
    user_data = user_collection.find_one({'_id': ObjectId(current_user_id)})
    form = EditUserForm(original_email=user_to_edit['email'], user_id=user_id, obj=user_to_edit)
    
    if form.validate_on_submit():
        try:
            updates = {
                'fname': form.fname.data,
                'lname': form.lname.data,
                'email': form.email.data,
                'phone_number': form.phone_number.data,
                'student_number': form.student_number.data,
                'role': form.role.data
            }
            
            result = user_collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': updates}
            )
            
            if result.modified_count > 0:
                flash('User updated successfully!', 'success')
                return redirect(url_for('manage_user.manage', view_type='approved'))
            else:
                flash('No changes were made.', 'info')
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            flash('An error occurred while updating the user.', 'error')
    
    # Pass both current_user and user_to_edit to template for clarity
    return render_template('edit_user.html', 
                         user=user_to_edit,
                         current_user=current_user, 
                         user_data=user_data,
                         form=form)

def send_email(recipient, subject, body):
    msg = Message(subject, recipients=[recipient], body=body)
    try:
        mail.send(msg)
        logger.debug(f"Email sent to {recipient}")
    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {str(e)}")
        raise