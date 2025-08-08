from flask import Blueprint, render_template, request, session, flash, redirect, url_for, jsonify
from app import db
from bson.objectid import ObjectId
from datetime import datetime
from app.routes.login import login_required
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

bp = Blueprint('inventory', __name__)

@bp.route('/Inventory')
@login_required
def inventory():
    user_id = session.get('user_id')
    user_data = None
    if user_id:
        try:
            user_data = db.user_collection.find_one({'_id': ObjectId(user_id)})
            logger.debug(f"User data retrieved for user_id: {user_id}")
        except Exception as e:
            logger.error(f"Error retrieving user data: {str(e)}")
            flash('Error retrieving user data.', 'error')
    return render_template('inventory.html', user_data=user_data)

@bp.route('/upload_inventory', methods=['POST'])
def upload_inventory():
    logger.debug("Received upload_inventory POST request")
    user_id = session.get('user_id')
    full_name = session.get('full_name', 'Unknown User')

    if not user_id:
        logger.warning("User not logged in")
        flash('Please log in to upload inventory.', 'error')
        return jsonify({'status': 'error', 'error': 'User not logged in'}), 401

    csv_data = request.form.get('csvData')
    if not csv_data:
        logger.warning("No csvData provided in request")
        flash('No data provided.', 'error')
        return jsonify({'status': 'error', 'error': 'No data provided'}), 400

    try:
        logger.debug(f"Parsing csvData (first 100 chars): {csv_data[:100]}...")
        data = json.loads(csv_data)
        if not isinstance(data, list) or not data:
            logger.error("Invalid data format: not a non-empty list")
            raise ValueError('Data must be a non-empty list of rows')

        required_fields = ['username', 'ict_equipment', 'serial_number', 'status']
        for row in data:
            if not isinstance(row, dict):
                logger.error(f"Invalid row format: {row}")
                raise ValueError('Each row must be a dictionary')
            for field in required_fields:
                if field not in row or not str(row[field]).strip():
                    logger.error(f"Missing or empty field {field} in row: {row}")
                    raise ValueError(f'Missing or empty required field: {field}')

        # Check for duplicate serial numbers
        serial_numbers = [row['serial_number'] for row in data if row['serial_number']]
        existing_serials = db.inventory_collection.distinct('rows.serial_number')
        duplicates = [sn for sn in serial_numbers if sn in existing_serials]
        if duplicates:
            logger.error(f"Duplicate serial numbers found: {duplicates}")
            flash(f'Duplicate serial numbers found: {", ".join(duplicates)}', 'error')
            return jsonify({'status': 'error', 'error': f'Duplicate serial numbers: {", ".join(duplicates)}'}), 400

        inventory_doc = {
            'inventory_date': datetime.now().strftime('%Y-%m-%d'),
            'submission_date': datetime.now().isoformat(),
            'department_school': data[0].get('department_school', 'N/A'),
            'rows': data,
            'created_by': full_name,
            'user_id': user_id
        }
        logger.debug(f"Attempting to insert inventory_doc: {inventory_doc}")
        result = db.my_files_collection.insert_one(inventory_doc)
        logger.info(f"Inventory saved to my_files_collection with ID: {result.inserted_id}")
        flash('Inventory saved to My Files. Submit from My Files to finalize.', 'success')
        return jsonify({'status': 'success', 'redirect': url_for('my_files.files')})
    except json.decoder.JSONDecodeError as je:
        logger.error(f"JSON parsing error: {str(je)}")
        flash(f'Invalid data format: {str(je)}', 'error')
        return jsonify({'status': 'error', 'error': str(je)}), 400
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        flash(f'Invalid data: {str(ve)}', 'error')
        return jsonify({'status': 'error', 'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}", exc_info=True)
        flash(f'Failed to upload inventory: {str(e)}', 'error')
        return jsonify({'status': 'error', 'error': str(e)}), 500