from datetime import datetime
from time import time
import jwt
from app import app, login, aws_service
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

manager = aws_service.AWSManager()
# rewrite User class to cooperate with Dynamo DB

class User(UserMixin):
    def __init__(self, response):
        if response:
            self.username = response[0]["username"]
            self.id = response[0]["username"] # id is used for flask_login only
            self.password = response[0]["password"]
            self.email = response[0]["email"]
            self.address = response[0]["address"]
            self.avatar = response[0]["avatar"]
            self.active_level = response[0]["active_level"]
            self.registration_time = response[0]["registration_time"]
        else: # to prevent data deletion when the brow
            print("ERROR: the logged user is not in the database.")

    def get_id(self): # https://flask-login.readthedocs.io/en/latest/_modules/flask_login/mixins.html
        return self.id

    def set_username(self, username):
        self.username = username
        self.id = username
        return

    def set_password(self, password):
        self.password = generate_password_hash(password)
        return

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_username(self):
        return self.username

    def get_email(self):
        return self.email

    def get_address(self):
        return self.address

    def get_reset_passwored_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        response = manager.query_table_item('Users', 'username', id)
        user = User(response)
        return user

# class User(UserMixin, db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(64), index=True, unique=True)
#     email = db.Column(db.String(120), index=True, unique=True, nullable=True)
#     password = db.Column(db.String(128))
#     avatar = db.Column(db.String(255))
#     address = db.Column(db.String(128))
#
#     def __repr__(self):
#         return '<User {}>'.format(self.username)
#
#     def set_password(self, password):
#         self.password = generate_password_hash(password)
#
#     def check_password(self, password):
#         return check_password_hash(self.password, password)
#
#     def get_username(self):
#         return (self.username)
#
#     def get_email(self):
#         return (self.email)
#
#     def get_address(self):
#         return (self.address)
#
#     def set_address(self, address):
#         self.address = address
#
#     def get_reset_password_token(self, expires_in=600):
#         return jwt.encode(
#             {'reset_password': self.id, 'exp': time() + expires_in},
#             app.config['SECRET_KEY'], algorithm='HS256')
#
#     def set_avatar(self, avatar):
#         self.avatar = avatar
#
#     def get_avatar(self):
#         return (self.avatar)
#
#     @staticmethod
#     def verify_reset_password_token(token):
#         try:
#             id = jwt.decode(token, app.config['SECRET_KEY'],
#                             algorithms=['HS256'])['reset_password']
#         except:
#             return
#         return User.query.get(id)
#
# @login.user_loader
# def load_user(id):
#     return User.query.get(int(id))

@login.user_loader
def load_user(id):
    response = manager.query_table_item('Users', 'username', id)
    user = User(response)
    return user