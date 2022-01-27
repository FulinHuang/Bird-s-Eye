from flask import render_template, url_for, redirect, flash, jsonify, make_response, request
from wtforms import StringField

from app import app, aws_service
from flask_login import login_user, logout_user, current_user, login_required
from app.forms import LoginForm, RegistrationForm, DeleteAccountForm, URLUploadPhotoForm, ChangePasswordForm, PhotoForm, ChangeProfileForm, AddNewCommentForm, SearchForm
from app.user import User
from app.forms import ResetPasswordRequestForm
from app.email_reset import send_password_reset_email
from app.forms import ResetPasswordForm
from app.aws_image import detect_labels
import uuid
import os
import random
import time
import urllib.request
from werkzeug.utils import secure_filename
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

# initialization of aws services
manager = aws_service.AWSManager()

@app.route('/', methods=['GET', 'POST'])
def initial():
    return render_template('initial.html')


@app.route('/about_us', methods=['GET', 'POST'])
def about_us():
    return render_template('about_us.html')


@app.route('/home', methods=['GET'])
@login_required
def home(): # update complete yw
    form1 = PhotoForm()
    all_files = []

    user_info = manager.query_table_item('Users', "username", current_user.get_username())
    photo_all = manager.scan_table_item('Photos', "username", current_user.get_username())

    time_array = []
    for photo in photo_all:
        post_time_new = datetime.strptime(photo["post_time"], '%m/%d/%Y, %H:%M:%S') #convert from string to time
        time_array.append(post_time_new)
        all_files.append([post_time_new, photo["photourl"], photo["photoname"]])
    all_files.sort()

    print(app.config['S3_BUCKET_ADDRESS'] + app.config['S3_AVATAR_FOLDER'] + '/' + current_user.avatar)
    print('This User was registered on', current_user.registration_time)
    return render_template('home.html',
                           title='Home',
                           all_files=all_files,
                           form1=form1,
                           register_time = current_user.registration_time,
                           storage_address=app.config['S3_BUCKET_ADDRESS'],
                           folder_name=app.config['S3_PHOTO_FOLDER'],
                           avatar_folder_name=app.config['S3_AVATAR_FOLDER'],
                           posts=user_info[0]["num_of_posts"],
                           popularity=round(user_info[0]["popularity"]))

@app.route('/photos/<hashtag>', methods=['GET'])
@login_required
def photos(hashtag=""):
    all_files = []
    form_search = SearchForm()
    enable_search = False

    photo_all = manager.scan_table_contain_item('Photos', 'hashtag', hashtag.capitalize())

    for photo in photo_all:
        post_time_new = datetime.strptime(photo["post_time"], '%m/%d/%Y, %H:%M:%S')  # convert from string to time
        all_files.append([post_time_new, photo["photourl"], photo["photoname"], photo["username"]])
    all_files.sort()

    return render_template('list_photo.html',
                           title='photos',
                           enable_search=enable_search,
                           all_files=all_files,
                           form_search=form_search,
                           storage_address=app.config['S3_BUCKET_ADDRESS'],
                           folder_name=app.config['S3_PHOTO_FOLDER'])

@app.route('/photos', methods=['GET', 'POST'])
@login_required
def photos_search():
    form_search = SearchForm()
    all_files = []
    all_users = set()
    recommend_photos = []
    all_recommend_files = []
    recommend_all = []
    recommend_num = 3
    enable_search = True
    user_info = manager.scan_table_condition_item('Users', "num_of_posts", 0)
    for user in user_info:
        all_users.add(user['username'])

    photo_all = []
    for user in all_users:
        photos = manager.scan_table_item('Photos', 'username', user)
        for photo in photos:
            photo_all.append(photo)

    rec_photos = manager.scan_table_item('Photos', 'is_recommended', True)
    if len(rec_photos) > 0:
        for photo in rec_photos:
            recommend_photos.append(photo)

    for photo in photo_all:
        post_time_new = datetime.strptime(photo["post_time"], '%m/%d/%Y, %H:%M:%S')  # convert from string to time
        all_files.append([post_time_new, photo["photourl"], photo["photoname"], photo["username"]])
    all_files.sort()

    if (len(recommend_photos) > 0):
        if len(recommend_photos) < recommend_num:
            recommend_num = len(recommend_photos)
        random_list = [random.randint(0, len(recommend_photos)-1) for i in range(recommend_num)]
        for i in random_list:
            recommend_all.append(recommend_photos[i])

        for photo in recommend_all:
            post_time_new = datetime.strptime(photo["post_time"], '%m/%d/%Y, %H:%M:%S')  # convert from string to time
            all_recommend_files.append([post_time_new, photo["photourl"], photo["photoname"], photo["username"]])
        all_recommend_files.sort()


    if form_search.validate_on_submit() and form_search.hashtag.data != '':
        hashtag = form_search.hashtag.data
        return redirect(url_for('photos',
                                hashtag=hashtag))


    return render_template('list_photo.html',
                           title='photos',
                           enable_search=enable_search,
                           all_files=all_files,
                           all_recommend_files=all_recommend_files,
                           form_search=form_search,
                           storage_address=app.config['S3_BUCKET_ADDRESS'],
                           folder_name=app.config['S3_PHOTO_FOLDER'])

@app.route('/login', methods=['GET', 'POST'])
def login(): # update complete yw
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user_info = manager.query_table_item('Users', 'username', form.username.data)
        if not user_info or not check_password_hash(user_info[0]["password"], form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        user_info = User(user_info)  # transform into the class User
        login_user(user_info, remember=form.remember_me.data)
        return redirect(url_for('home'))
    return render_template('login.html', title='LOGIN', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register(): # update complete yw
    form = RegistrationForm()
    if form.validate_on_submit():
        user = {
            "username": form.username.data,
            "password": generate_password_hash(form.password.data),
            "email": form.email.data ,
            "address": form.address.data.upper(),
            "self_description": "",
            "avatar": "dft.png",
            "registration_time":  datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
            "last_login": datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
            "num_of_posts": 0,
            "active_level": 1,
            "popularity": 0
            }
        manager.add_table_item('Users', user)
        flash('Congratulations, you just registered!')
        return redirect(url_for('login'))
    return render_template('register.html', title='REGISTER', form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request(): # update complete yw
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        response = manager.scan_table_item('Users', 'email', form.email.data)
        if response:
            user = User(response)
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token): # update complete yw
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('home'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        manager.update_table_item(table_name = 'Users',
                                      key = {"username": user.username},
                                      column = "password",
                                      new_value = generate_password_hash(form.password.data))
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password(): # update complete yw
    if current_user.is_authenticated:
        form = ChangePasswordForm()
        if form.validate_on_submit():
            user = current_user
            if not user.check_password(form.old_password.data):
                flash('Your original password is incorrect')
                return render_template('change_password.html', title='CHANGE PASSWORD', form=form)
            #change password
            manager.update_table_item(table_name='Users',
                                      key={"username": user.username},
                                      column="password",
                                      new_value=generate_password_hash(form.new_password.data))
            flash('You have changed your password, please re-login')
            logout_user()
            return redirect(url_for('login'))
        return render_template('change_password.html', title='CHANGE PASSWORD', form=form)
    flash('Please login first')
    return redirect(url_for('login'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/upload', methods=['POST']) # upload
@login_required
def upload_page(): # update complete yw

    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    file_ext = os.path.splitext(filename)[1]
    filename = str(uuid.uuid4()) + file_ext

    if uploaded_file.filename != '':
        if file_ext not in app.config['UPLOAD_PHOTO_EXTENSIONS']:
            flash('Please choose a photo with correct format!')
            return redirect(url_for('upload'))

        manager.s3_client.put_object(ACL='public-read',
                                     Bucket=app.config['S3_BUCKET_NAME'],
                                     Key=app.config['S3_PHOTO_FOLDER']+'/'+ filename,
                                     Body=uploaded_file)
        photo = {
            "username": current_user.username,
            "photourl": filename,
            "hashtag": "",
            "photoname": "New Post",
            "description": "",
            "comments": [],
            "post_time": datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
            "click_rate": 0,
            "is_recommended": False
        }
        manager.add_table_item('Photos', photo)
        # add user, number_of_post by 1
        manager.increase_table_column(table_name = 'Users',
                                      key = {"username": current_user.username},
                                      column = "num_of_posts",
                                      increase = 1)
        flash('New photo has been successfully uploaded')
    else:
        flash('Please select a file!')
        return redirect(url_for('upload'))

    return redirect(url_for('next_page', filename=filename))


@app.route('/next/<filename>', methods=['GET', 'POST'])# upload next step
@login_required
def next_page(filename):
    form1 = PhotoForm()
    if form1.hashtag.data == None:
        labels = detect_labels('photo/' + filename, app.config['S3_BUCKET_NAME'])
        form1.hashtag.data = labels

    if form1.validate_on_submit():
        manager.update_table_item(table_name='Photos',
                                  key={"photourl": filename},
                                  column="photoname",
                                  new_value=form1.photoname.data)
        manager.update_table_item(table_name='Photos',
                                  key={"photourl": filename},
                                  column="hashtag",
                                  new_value=form1.hashtag.data)
        manager.update_table_item(table_name='Photos',
                                  key={"photourl": filename},
                                  column="description",
                                  new_value=form1.description.data)
        flash('Post details has been successfully changed')
        return redirect(url_for('home'))
    return render_template('next.html', title='Changing Details of Post', form1=form1, file=filename, storage_address=app.config['S3_BUCKET_ADDRESS'], folder_name=app.config['S3_PHOTO_FOLDER'])


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload(): # OBSOLETE?
    form1 = PhotoForm()
    return render_template('upload.html', title='Upload', form1=form1)


@app.route('/change_profile', methods=['GET', 'POST'])
@login_required
def change_profile(): # update complete yw
    if current_user.is_authenticated:
        address = ""
        form = ChangeProfileForm()
        form.address.data = address #StringField('New Address', default = address, validators=[DataRequired()])
        #form.update_default_address("balabala")
        if form.validate_on_submit():
            manager.update_table_item(table_name='Users',
                                      key={"username": current_user.username},
                                      column="address",
                                      new_value=form.address.data)
            flash('You have changed your address!')
            return redirect(url_for('home'))
        return render_template('change_profile.html', title='Change Profile', form=form)
    flash('Please login first')
    return redirect(url_for('login'))


@app.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar_page(): # update complete yw
    # form1 = PhotoForm()
    #user = current_user
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    file_ext = os.path.splitext(filename)[1]
    filename = str(uuid.uuid4()) + file_ext
    if uploaded_file.filename != '':
        if file_ext not in app.config['UPLOAD_PHOTO_EXTENSIONS']:
            flash('Please choose a photo with correct format!')
            return redirect(url_for('upload_avatar'),
                            storage_address=app.config['S3_BUCKET_ADDRESS'],
                            avatar_folder_name=app.config['S3_AVATAR_FOLDER']
                            )

        # uploaded_file.save(os.path.join(app.config['AVATAR_FOLDER'], filename))

        # add new Avatar to the S3
        manager.s3_client.put_object(ACL='public-read',
                                     Bucket=app.config['S3_BUCKET_NAME'],
                                     Key=app.config['S3_AVATAR_FOLDER']+'/'+ filename,
                                     Body=uploaded_file)

        # delete the old Avatar in S3 if it is not default
        if current_user.avatar != "dft.png":
            manager.s3_client.delete_object(Bucket=app.config['S3_BUCKET_NAME'],
                                            Key=app.config['S3_AVATAR_FOLDER']+'/'+ current_user.avatar)
        # update the new Avatar
        current_user.avatar = filename #zxcvb
        manager.update_table_item(table_name='Users',
                                  key={"username": current_user.username},
                                  column="avatar",
                                  new_value=filename)
        flash('Success!')
    else:
        flash('Please select a file!')
        return redirect(url_for('upload_avatar'),
                        storage_address=app.config['S3_BUCKET_ADDRESS'],
                        avatar_folder_name=app.config['S3_AVATAR_FOLDER']
                        )

    return redirect(url_for('home'))


@app.route('/upload_avatar', methods=['GET', 'POST'])
@login_required
def upload_avatar(): # update complete yw
    # form1 = PhotoForm()
    return render_template('upload_avatar.html',
                           title='Upload Avatar',
                           storage_address=app.config['S3_BUCKET_ADDRESS'],
                           avatar_folder_name=app.config['S3_AVATAR_FOLDER']
                           )


@app.route('/user/<username>')
@login_required
def user(username): # update complete yw
    response = manager.query_table_item('Users', 'username',username)
    user_view = User(response)

    all_files = []
    photo_all = manager.scan_table_item('Photos', "username", username)

    time_array = []
    for photo in photo_all:
        post_time_new = datetime.strptime(photo["post_time"], '%m/%d/%Y, %H:%M:%S') #convert from string to time
        time_array.append(post_time_new)
        all_files.append([post_time_new, photo["photourl"], photo["photoname"]])
    all_files.sort()

    return render_template('user.html',
                           title=username,
                           all_files=all_files,
                           posts=response[0]['num_of_posts'],
                           popularity=round(response[0]['popularity']),
                           user=user_view,
                           register_time=user_view.registration_time,
                           storage_address=app.config['S3_BUCKET_ADDRESS'],
                           folder_name=app.config['S3_PHOTO_FOLDER'],
                           avatar_folder_name=app.config['S3_AVATAR_FOLDER']
                           )


@app.route('/user/<username>/<post>', methods=['GET', 'POST'])
@login_required
def post(username, post):
    new_comment_form = AddNewCommentForm()
    if new_comment_form.validate_on_submit():
        all_comments = manager.append_table_item(table_name="Photos",
                                                 key={"photourl": post},
                                                 column="comments",
                                                 value=[[current_user.username,
                                                        #current_user.avatar,
                                                        #current_user.address,
                                                        new_comment_form.comment.data,
                                                        datetime.now().strftime("%m/%d/%Y, %H:%M:%S")]])['Attributes']['comments']
    else:
        all_comments = manager.query_table_item(table_name="Photos",
                                                key="photourl",
                                                value=post
                                                )[0]['comments']
    # if all_comments: # for comments visualization
    avatar_list = []
    address_list = []
    for each_comment in all_comments:
        response = manager.query_table_item('Users', 'username', each_comment[0])[0]
        avatar_list.append(response['avatar'])
        address_list.append(response['address'])
    all_comments = [[all_comments[i][0], avatar_list[i], address_list[i], all_comments[i][1], all_comments[i][2]] for i in range(len(all_comments))]

    response = manager.query_table_item('Users', 'username',username)
    user_view = User(response)
    photo = manager.query_table_item('Photos', 'photourl', post)
    photo_name = photo[0]['photoname']
    photo_hashtag = photo[0]['hashtag']
    photo_des = photo[0]['description']
    # update click_rate and popularity
    if username != current_user.username: # cannot increase clickrate by myself
        manager.increase_table_column(table_name='Photos',
                                      key={"photourl": post},
                                      column="click_rate",
                                      increase=current_user.active_level)
        manager.increase_table_column(table_name='Users',
                                      key={"username": username},
                                      column="popularity",
                                      increase=current_user.active_level)


    return render_template('post.html',
                           title='wa',
                           user=user_view,
                           file=post,
                           photo_name=photo_name,
                           photo_hashtag=photo_hashtag,
                           photo_des=photo_des,
                           storage_address=app.config['S3_BUCKET_ADDRESS'],
                           folder_name=app.config['S3_PHOTO_FOLDER'],
                           avatar_folder_name=app.config['S3_AVATAR_FOLDER'],
                           comment_list = all_comments,
                           form1 = new_comment_form)


@app.route('/post/<username>/<post>')
@login_required
def delete_photo(username, post): #这个我也没找到。。
    if current_user.username == username:
        # Photo.query.filter_by(photourl=post).delete()
        # db.session.commit()
        # os.remove(os.path.join(app.config['UPLOAD_FOLDER'], post))

        # remove the photo record from database
        manager.delete_table_item(table_name='Photos', item={"photourl": post})

        # remove the photo from S3
        manager.s3_client.delete_object(Bucket=app.config['S3_BUCKET_NAME'],
                                        Key=app.config['S3_PHOTO_FOLDER'] + '/' + post)

        # update the number of post
        manager.increase_table_column(table_name = 'Users',
                                      key = {"username": current_user.username},
                                      column = "num_of_posts",
                                      increase = -1)
        flash('You have deleted this post successfully!')
        return redirect(url_for('home'))
    return redirect(url_for('home'))


@app.route('/list', methods=['GET', 'POST'])
@login_required
def list(): # update complete yw
    user_list = []
    user_parse = manager.dynamodb.Table('Users').scan()['Items']
    for username in user_parse:
        user_list.append([username['username'], username['avatar'], username['num_of_posts']])

    return render_template('list.html',
                           title='List of All Users',
                           user_list=user_list,
                           storage_address=app.config['S3_BUCKET_ADDRESS'],
                           folder_name=app.config['S3_PHOTO_FOLDER'],
                           avatar_folder_name=app.config['S3_AVATAR_FOLDER']
                           )

