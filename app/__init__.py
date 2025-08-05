from flask import Flask, url_for
from pymongo import MongoClient
from datetime import datetime
from flask_mail import Mail

database = MongoClient('mongodb://localhost:27017/')
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

from app.routes import home, inventory, default_inventory, recent, registration, login, my_files, stats, view_stats, manage_user
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

