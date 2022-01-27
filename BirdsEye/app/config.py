import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ece1779'


    #SQLALCHEMY_DATABASE_URI = 'mysql://ece1779:ece1779project1@ece1779-a1.cbqorhddlq5b.us-east-1.rds.amazonaws.com/ece1779a1'
    SQLALCHEMY_DATABASE_URI = 'mysql://allen_admin:lu19920218@allen-ece1779-a1.c7mezzt0p0rf.us-east-1.rds.amazonaws.com/dbname'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    S3_BUCKET_NAME = 'custom-labels-console-us-east-1-f4d7083aff' # must be globally unique, only one of us can have bucket with this name
    S3_BUCKET_ADDRESS = 'https://'+S3_BUCKET_NAME+'.s3.amazonaws.com/'
    S3_PHOTO_FOLDER = 'photo'
    S3_AVATAR_FOLDER = 'avatar'

    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = 1
    MAIL_USERNAME = 'ece1779allen@gmail.com'
    MAIL_PASSWORD = 'doubanjiang'
    ADMINS = ['ece1779@gmail.com']
    POSTS_PER_PAGE = 25
    UPLOAD_FOLDER = basedir + '/static/image'
    OUTPUT_FOLDER = basedir + '/static/output'
    AVATAR_FOLDER = basedir + '/static/avatar'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # prevent large file size
    UPLOAD_PHOTO_EXTENSIONS = ['.JPG', '.jpg', '.PNG', '.png', '.GIF', '.gif', '.JPEG', '.jpeg', 'TIFF', 'tiff', 'RAW', 'raw']