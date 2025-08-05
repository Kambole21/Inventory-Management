from flask import Blueprint, render_template, request, url_for, flash, redirect, session
from app import db, user_collection, pending_users, mail
from flask_mail import Message
from bson.objectid import ObjectId
import logging

bp = Blueprint('manage_user', __name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@bp.route('/Management_Page', methods=['GET', 'POST'])
def manage():
    user_id = session.get('user_id')
    user_data = None
    if user_id:
        user_data = user_collection.find_one({'_id': ObjectId(user_id)})
    pending_users_list = pending_users.find({'status': 'pending'})  # Fetch from pending_users
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        action = request.form.get('action')
        
        if not user_id or not action:
            logger.error("Missing user_id or action in form data")
            flash('Invalid request data.', 'error')
            return redirect(url_for('manage_user.manage'))
            
        try:
            user = pending_users.find_one({'_id': ObjectId(user_id)})  # Fetch from pending_users
            if not user:
                logger.error(f"User with _id {user_id} not found in pending_users")
                flash('User not found.', 'error')
                return redirect(url_for('manage_user.manage'))
                
            if action == 'approve':
                # Move user to user_collection
                user_data = user.copy()  # Copy user data
                user_data.pop('_id', None)  # Remove MongoDB _id for new insertion
                user_data['status'] = 'approved'  # Update status
                result = user_collection.insert_one(user_data)  # Insert into user_collection
                
                if result.inserted_id:
                    # Delete from pending_users
                    pending_users.delete_one({'_id': ObjectId(user_id)})
                    logger.debug(f"User {user['email']} approved, moved to user_collection with new _id: {result.inserted_id}")
                    try:
                        send_email(
                            user['email'], 
                            'Account Approved', 
                            'Your account has been approved. You can now log in.'
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
            else:
                logger.error(f"Invalid action: {action}")
                flash('Invalid action.', 'error')
                
        except Exception as e:
            logger.error(f"Error processing user management: {str(e)}")
            flash(f'An error occurred: {str(e)}', 'error')
            
        return redirect(url_for('manage_user.manage'))
    
    return render_template('manage_user.html', pending_users=pending_users_list, user_data=user_data)

def send_email(recipient, subject, body):
    msg = Message(subject, recipients=[recipient], body=body)
    try:
        mail.send(msg)
        logger.debug(f"Email sent to {recipient}")
    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {str(e)}")
        raise 