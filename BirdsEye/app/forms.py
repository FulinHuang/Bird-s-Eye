from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, URL
from app.user import User
from flask_wtf.file import FileField, FileAllowed, FileRequired

from app import aws_service
from app import app

# initialization of aws services
manager = aws_service.AWSManager()

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    address = StringField('City', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = manager.query_table_item("Users", "username", username.data)
        if user:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = manager.scan_table_item("Users", "email", email.data)
        if user:
            raise ValidationError('Please use a different email address.')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    new_password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class DeleteAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    submit = SubmitField('Delete')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user.get_username() == 'admin':
            raise ValidationError('You cannot delete the admin!')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')

class URLUploadPhotoForm(FlaskForm):
    photoURL = StringField('PhotoURL', validators=[DataRequired(), Length(min=0, max=255, message='Photo URL is too long!'), URL(require_tld=True, message='Please enter a valid URL!')])
    submit = SubmitField('Upload')

class MyForm(FlaskForm):
    file = FileField('File')
    submit = SubmitField('Upload!')

class PhotoForm(FlaskForm):
    photoname = StringField('photoname', validators=[DataRequired()])
    hashtag = StringField('hashtag')
    description = StringField('description')
    submit = SubmitField('Upload')


class ChangeProfileForm(FlaskForm):
    address = StringField('New Address', validators=[DataRequired()])
    submit = SubmitField('Change Address')

class SearchForm(FlaskForm):
    hashtag = StringField('hashtag')

class AddNewCommentForm(FlaskForm):
    comment = StringField('New Comment', default = "Leave your kind comments here (max: 500 characters)", validators=[DataRequired(), Length(min=1, max=255, message='Comment must between 1 to 500 characters')])
    submit = SubmitField('Submit')
