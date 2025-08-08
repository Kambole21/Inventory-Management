from flask import Blueprint, render_template, request, url_for, jsonify, flash, redirect, session
from datetime import datetime
from bson.objectid import ObjectId
import csv
from io import StringIO
from app import db
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

bp = Blueprint('default_inventory', __name__)

@bp.route('/check_serial_number', methods=['POST'])
def check_serial_number():
    serial_number = request.form.get('serial_number', '').strip()
    edit_id = request.form.get('edit_id', '').strip()
    
    if not serial_number:
        return jsonify({'exists': False, 'message': 'Serial number is required'})

    query = {'rows.serial_number': serial_number}
    if edit_id:
        query['_id'] = {'$ne': ObjectId(edit_id)}
    
    existing = db.inventory_collection.find_one(query) or db.my_files_collection.find_one(query)
    return jsonify({
        'exists': bool(existing), 
        'message': 'Serial number already exists' if existing else 'Serial number is available'
    })

@bp.route('/Default_Inventory_Page', methods=['GET', 'POST'])
def default():
    user_id = session.get('user_id')
    user_data = None
    if user_id:
        user_data = db.user_collection.find_one({'_id': ObjectId(user_id)})
        logger.debug(f"User data retrieved for user_id: {user_id}")

    edit_id = request.args.get('edit')
    edit_data = None
    
    if request.method == 'GET' and edit_id:
        try:
            edit_data = db.inventory_collection.find_one({'_id': ObjectId(edit_id)}) or db.my_files_collection.find_one({'_id': ObjectId(edit_id)})
            if edit_data:
                edit_data['_id'] = str(edit_data['_id'])
                logger.debug(f"Edit data retrieved for inventory_id: {edit_id}")
                return render_template('default_template.html', 
                                     user_data=user_data, 
                                     edit_data=edit_data,
                                     edit_id=edit_id)
            else:
                logger.warning(f"No inventory found for edit_id: {edit_id}")
                flash('Inventory not found.', 'error')
                return redirect(url_for('my_files.files'))
        except Exception as e:
            logger.error(f"Error retrieving edit data: {str(e)}")
            flash(f'Error retrieving inventory: {str(e)}', 'error')
            return redirect(url_for('my_files.files'))

    if request.method == 'POST':
        inventory_data = request.form.get('inventoryData')
        import_file = request.files.get('importCsv') if 'importCsv' in request.files else None
        department_school = request.form.get('departmentSchool') or request.form.get('customDepartmentSchool')
        edit_id = request.form.get('edit_id')
        
        if edit_id:  # Handle edit case
            try:
                import json
                data = json.loads(inventory_data)
                rows = data.get('rows', [])
                
                # Check for duplicate serial numbers excluding the current document
                serial_numbers = [row.get('serial_number') for row in rows if row.get('serial_number')]
                existing_serials = db.inventory_collection.distinct(
                    'rows.serial_number',
                    {'_id': {'$ne': ObjectId(edit_id)}}
                ) + db.my_files_collection.distinct(
                    'rows.serial_number',
                    {'_id': {'$ne': ObjectId(edit_id)}}
                )
                duplicates = [sn for sn in serial_numbers if sn in existing_serials]
                
                if duplicates:
                    logger.error(f"Duplicate serial numbers found during edit: {duplicates}")
                    flash(f'Duplicate serial numbers found: {", ".join(duplicates)}', 'error')
                    return render_template('default_template.html', 
                                         user_data=user_data, 
                                         edit_data=data,
                                         edit_id=edit_id)

                inventory_doc = {
                    'inventory_date': data.get('inventory_date'),
                    'department_school': department_school,
                    'submission_date': datetime.utcnow().isoformat(),
                    'rows': rows,
                    'created_by': session.get('full_name', 'Unknown User'),
                    'user_id': user_id,
                    'last_modified': datetime.utcnow().isoformat()
                }

                # Update the existing document in both collections
                db.inventory_collection.update_one(
                    {'_id': ObjectId(edit_id)},
                    {'$set': inventory_doc},
                    upsert=True
                )
                
                db.my_files_collection.update_one(
                    {'_id': ObjectId(edit_id)},
                    {'$set': inventory_doc},
                    upsert=True
                )
                
                logger.info(f"Inventory updated successfully for ID: {edit_id}")
                flash('Inventory updated successfully!', 'success')
                return redirect(url_for('default_inventory.view_inventory', inventory_id=edit_id))
                
            except Exception as e:
                logger.error(f"Failed to update inventory: {str(e)}", exc_info=True)
                flash(f'Failed to update inventory: {str(e)}', 'error')
                return render_template('default_template.html',
                                     user_data=user_data,
                                     edit_data=json.loads(inventory_data) if inventory_data else None,
                                     edit_id=edit_id)
                
        elif import_file and import_file.filename.endswith('.csv'):
            try:
                csv_data = import_file.read().decode('utf-8')
                csv_file = StringIO(csv_data)
                csv_reader = csv.DictReader(csv_file)
                expected_headers = {
                    'no': ['no', 'NO'],
                    'username': ['username', 'Username', 'USERNAME'],
                    'position': ['position', 'Position', 'POSITION'],
                    'ict_equipment': ['ict_equipment', 'ICT Equipment', 'ICT_EQUIPMENT', 'IctEquipment', 'ICT EQUIPMENT'],
                    'model_details': ['model_details', 'Model Details', 'MODEL_DETAILS', 'ModelDetails', 'MODEL DETAILS'],
                    'serial_number': ['serial_number', 'Serial Number', 'SERIAL_NUMBER', 'SerialNumber', 'SERIAL NUMBER'],
                    'status': ['status', 'Status', 'STATUS'],
                    'comment': ['comment', 'Comment', 'COMMENT']
                }
                actual_headers = csv_reader.fieldnames

                header_map = {}
                for expected, variations in expected_headers.items():
                    for var in variations:
                        if var in actual_headers:
                            header_map[var] = expected
                            break

                imported_data = []
                for row in csv_reader:
                    normalized_row = {}
                    for csv_header, expected_field in header_map.items():
                        normalized_row[expected_field] = row.get(csv_header, '')
                    imported_data.append(normalized_row)

                # Check for duplicate serial numbers
                serial_numbers = [row['serial_number'] for row in imported_data if row['serial_number']]
                existing_serials = db.inventory_collection.distinct('rows.serial_number') + db.my_files_collection.distinct('rows.serial_number')
                duplicates = [sn for sn in serial_numbers if sn in existing_serials]
                if duplicates:
                    logger.error(f"Duplicate serial numbers found during import: {duplicates}")
                    flash(f'Duplicate serial numbers found: {", ".join(duplicates)}', 'error')
                    return render_template('default_template.html', user_data=user_data)

                inventory_doc = {
                    'inventory_date': request.form.get('inventoryDate') or datetime.now().strftime('%Y-%m-%d'),
                    'department_school': department_school,
                    'submission_date': datetime.utcnow().isoformat(),
                    'rows': imported_data,
                    'created_by': session.get('full_name', 'Unknown User'),
                    'user_id': user_id,
                    'last_modified': datetime.utcnow().isoformat()
                }
                
                # Save to collections
                inventory_result = db.inventory_collection.insert_one(inventory_doc)
                db.my_files_collection.insert_one(inventory_doc)
                
                logger.info(f"Inventory imported successfully with ID: {inventory_result.inserted_id}")
                flash('Inventory imported and submitted successfully!', 'success')
                return redirect(url_for('default_inventory.view_inventory', inventory_id=str(inventory_result.inserted_id)))
            except Exception as e:
                logger.error(f"Failed to import inventory: {str(e)}", exc_info=True)
                flash(f'Failed to import inventory: {str(e)}', 'error')
        elif inventory_data:
            try:
                import json
                data = json.loads(inventory_data)
                rows = data.get('rows', [])
                serial_numbers = [row.get('serial_number') for row in rows if row.get('serial_number')]
                existing_serials = db.inventory_collection.distinct('rows.serial_number') + db.my_files_collection.distinct('rows.serial_number')
                duplicates = [sn for sn in serial_numbers if sn in existing_serials]
                if duplicates:
                    logger.error(f"Duplicate serial numbers found during submission: {duplicates}")
                    flash(f'Duplicate serial numbers found: {", ".join(duplicates)}', 'error')
                    return render_template('default_template.html', user_data=user_data)

                inventory_doc = {
                    'inventory_date': data.get('inventory_date'),
                    'department_school': department_school,
                    'submission_date': datetime.utcnow().isoformat(),
                    'rows': rows,
                    'created_by': session.get('full_name', 'Unknown User'),
                    'user_id': user_id,
                    'last_modified': datetime.utcnow().isoformat()
                }
                
                # Save to collections
                inventory_result = db.inventory_collection.insert_one(inventory_doc)
                db.my_files_collection.insert_one(inventory_doc)
                
                logger.info(f"Inventory submitted successfully with ID: {inventory_result.inserted_id}")
                flash('Inventory submitted successfully!', 'success')
                return redirect(url_for('default_inventory.view_inventory', inventory_id=str(inventory_result.inserted_id)))
            except Exception as e:
                logger.error(f"Failed to submit inventory: {str(e)}", exc_info=True)
                flash(f'Failed to submit inventory: {str(e)}', 'error')
        return redirect(url_for('recent.recent'))
    
    return render_template('default_template.html', user_data=user_data)

@bp.route('/view_inventory/<inventory_id>')
def view_inventory(inventory_id):
    user_id = session.get('user_id')
    user_data = None
    if user_id:
        user_data = db.user_collection.find_one({'_id': ObjectId(user_id)})
    inventory_data = db.inventory_collection.find_one({'_id': ObjectId(inventory_id)}) or db.my_files_collection.find_one({'_id': ObjectId(inventory_id)})
    
    if inventory_data:
        inventory_data['_id'] = str(inventory_data['_id'])
        logger.debug(f"Inventory data retrieved for view_inventory: {inventory_id}")
        return render_template('view_inventory.html', 
                             inventory_data=inventory_data, 
                             user_data=user_data)
    else:
        logger.warning(f"Inventory not found for view_inventory: {inventory_id}")
        flash('Inventory not found.', 'error')
        return redirect(url_for('recent.recent'))