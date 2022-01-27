from flask import Flask
from app.config import Config
from flask_login import LoginManager
from flask_mail import Mail
import time

app = Flask(__name__)
app.config.from_object(Config)
login = LoginManager(app)
login.login_view = 'login'
mail = Mail(app)
instance_start_time = time.time()

from app import routes
from app import user
from app import email_reset
from app import forms