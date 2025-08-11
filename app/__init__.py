from flask import Flask, url_for
from pymongo import MongoClient
from datetime import datetime
from flask_mail import Mail
import logging
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
database =  MongoClient(os.getenv('MONGO_URI', 'mongodb+srv://kambole520:U1PmBvuwI94ClgCF@inventory.nberfep.mongodb.net/?retryWrites=true&w=majority&appName=Inventory'))
db = database['Inventory']
user_collection = db['user_collection']
pending_users = db['Pending Users']
inventory_collection = db['Default Inventory']  
customized_inventory_collection = db['Customized Inventory']
my_files_collection = db['My Inventories']

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = '72bfe6969c561b5fad098d569d3d957d'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'kambole520@gmail.com'
app.config['MAIL_PASSWORD'] = 'nvyg lzlh kqjm aspy'
app.config['MAIL_DEFAULT_SENDER'] = 'kambole520@gmail.com' 

mail = Mail(app)

# Creating a default user
default_email = 'kambole520@yahoo.com'
default_password = '12345678'
if not user_collection.find_one({'email': default_email}):
    hashed_password = generate_password_hash(default_password)
    user_collection.insert_one({
        'email': default_email,
        'fname': 'Chomba',
        'lname': 'Kambole',
        'role': 'admin',
        'phone_number': '0965226263',
        'student_number': 'N/A',
        'password': hashed_password,
        'status': 'approved',
        'submission_time': datetime.utcnow().isoformat() + 'Z'
    })
    logger.info(f"Default admin created: {default_email}")

from app.routes import (
    home, inventory, default_inventory, recent, registration, login, my_files, stats, view_stats, manage_user, tutorials,
    client

    ) 
app.register_blueprint(home.bp)
app.register_blueprint(inventory.bp)
app.register_blueprint(default_inventory.bp)
app.register_blueprint(recent.bp)
app.register_blueprint(registration.bp)
app.register_blueprint(login.bp)
app.register_blueprint(my_files.bp)
app.register_blueprint(stats.bp)
app.register_blueprint(view_stats.bp)
app.register_blueprint(manage_user.bp)
app.register_blueprint(tutorials.bp)
app.register_blueprint(client.bp)