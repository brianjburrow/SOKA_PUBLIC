import os
from flask import Flask, render_template, request, flash, redirect, session, g, jsonify, send_from_directory
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db
from models import User, Activity, Challenge, Landmark, Gear, UserFriends, Admin, UserGear, ActivityComment
from forms import LoginForm, NewActivityForm, NewGearForm, NewLandmarkForm, NewChallengeForm, EditUserForm, NewUserForm, NewUserGearForm, NewCommentForm
from werkzeug.utils import secure_filename
import secret
import requests as python_requests
from datetime import datetime

CURR_USER_KEY = "curr_user"
GPX_FOLDER = '/gpx_files'
ALLOWED_EXTENSIONS = {'gpx'}
WEATHER_API_BASE_URL = "https://api.openweathermap.org/data/2.5/onecall"


app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql:///SOKA')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secret.FLASK_SECRET_KEY)
app.config['SOKA_PRESIGNED_URL_ACCESS_KEY'] = os.environ.get('SOKA_PRESIGNED_URL_ACCESS_KEY', secret.SOKA_PRESIGNED_URL_ACCESS_KEY)
app.config['SOKA_PRESIGNED_URL_SECRET_ACCESS_KEY'] = os.environ.get('SOKA_PRESIGNED_URL_SECRET_ACCESS_KEY', secret.SOKA_PRESIGNED_URL_SECRET_ACCESS_KEY)
app.config['SOKA_USER_IMAGE_BUCKET'] = os.environ.get("SOKA_USER_IMAGE_BUCKET", secret.SOKA_USER_IMAGE_BUCKET)
app.config['OPENWEATHERMAP_API_KEY'] = os.environ.get("OPENWEATHERMAP_API_KEY", secret.OPENWEATHERMAP_API_KEY)
app.config['UPLOAD_FOLDER'] = GPX_FOLDER
NUM_MEGABYTE_LIMIT = 10
app.config['MAX_CONTENT_LENGTH'] = NUM_MEGABYTE_LIMIT * 1000 * 1000




toolbar = DebugToolbarExtension(app)

connect_db(app)

import bp_activities , bp_challenges, bp_gear, bp_gearshed, bp_users, bp_landmarks

app.register_blueprint(bp_activities.bp)
app.register_blueprint(bp_challenges.bp)
app.register_blueprint(bp_gear.bp)
app.register_blueprint(bp_gearshed.bp)
app.register_blueprint(bp_users.bp)
app.register_blueprint(bp_landmarks.bp)

##############################################################################
# User signup/login/logout

def do_login(user):
    """Log in user."""
    session[CURR_USER_KEY] = user.id

def do_logout():
    """Logout user."""
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


def allowed_file(filename):
    '''Check to make sure the user uploaded a valid filename'''
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""
    if CURR_USER_KEY in session:
        g.user = User.query.get_or_404(session[CURR_USER_KEY])
    else:
        g.user = None

@app.route('/uploads/<name>')
def download_file(name):
    # taken from FLASK documentation
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


@app.route('/')
def show_home():
    '''Show the user the homepage'''
    form = NewUserForm()
    return render_template('home.html', form=form)

@app.route('/login', methods=['GET', "POST"])
def handle_login():
    '''Show the user the login form, and handle its submission'''
    form = LoginForm()
    if form.validate_on_submit():

        user = User.authenticate(form.email.data , form.password.data)
        if user:
            do_login(user)
            g.user = user
            return redirect(f'/users/{g.user.id}/feed')
        else:
            flash("Incorrect credentials.", 'error')
            return redirect('/login')
    return render_template('/users/login.html', form = form)

@app.route('/logout')
def handle_logout():
    '''Log out a user'''
    do_logout()
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def show_register_form():
    '''Show the user the registration form, and handle its submission'''
    form = NewUserForm()
    if form.validate_on_submit():
        if form.password.data != form.confirm.data:
            flash("Passwords must match.", 'error')
            return redirect('/register')

        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Email is already registered to an account.")
            return redirect('/register')

        try:
            new_user = User.sign_up_from_form(form)
            do_login(new_user)
            flash("Registration Successful", 'success')
            return redirect(f'/users/{new_user.id}/feed')
        except Exception as e:
            flash("Error during registration, please try again", 'error')
            flash(f"{e}")
            return redirect('/register')

    return render_template('/users/register.html', form=form)


@app.route('/admin', methods=['GET'])
def show_all_admin():
    '''Display all users, and handle friends if the user is logged in'''
    users = [admin.user for admin in Admin.query.all()]
    return render_template('/users/admin.html', users = users, num_photos_displayed=2)


##############################################################
# Create API for adding/removing friends

@app.route('/users/<int:follower_id>/<int:following_id>', methods=['POST', 'DELETE'])
def handle_friendship(follower_id, following_id):
    '''A method to handle one user following another user'''
    if not validate_signed_in("You must be signed in to add a friend"):
        return (jsonify({}), 401)
    if not validate_correct_user("You cannot force other users to follow others.", follower_id):
        return (jsonify({}), 400)
    if g.user.id == following_id:
        flash("You cannot follow yourself")
        return (jsonify({}), 400)

    User.query.get_or_404(follower_id)
    User.query.get_or_404(following_id)
    if request.method == 'POST':
        user_friend = UserFriends(user_following_id=follower_id, user_being_followed_id=following_id)
        db.session.add(user_friend)
        db.session.commit()
        return (user_friend.to_json(), 200)
    elif request.method == 'DELETE':
        user_friend = UserFriends.query.filter(UserFriends.user_following_id==follower_id,UserFriends.user_being_followed_id==following_id).first()
        json = user_friend.to_json()
        db.session.delete(user_friend)
        db.session.commit()
        return (json, 200)


def get_weather_data(landmark, units="imperial"):
    '''Perform the API call to open weather maps and return the JSON data'''
    QUERY_STRING = f"?lat={landmark.get_latitude()}&lon={landmark.get_longitude()}&exclude=minutely,daily&appid={app.config['OPENWEATHERMAP_API_KEY']}&units={units}"
    response = python_requests.get(WEATHER_API_BASE_URL + QUERY_STRING)
    return response.status_code, response.json()

def process_datetimes(unix_datetime, timezone_offset, format = "%Y-%m-%d %H:%M"):
    dt = int(unix_datetime) + int(timezone_offset)
    return datetime.utcfromtimestamp(dt).strftime(format)

@app.route('/API/weather/<int:landmark_id>')
def get_weather(landmark_id):
    landmark = Landmark.query.get_or_404(landmark_id)

    status_code, weather_json = get_weather_data(landmark)
    if status_code != 200:
        return jsonify({"status":status_code})

    current = weather_json['current']
    hourly = weather_json['hourly']
    tz_offset = weather_json['timezone_offset']

    current['timezone'] = weather_json['timezone']
    current['dt'] = process_datetimes(current['dt'], tz_offset)
    current['sunrise'] = process_datetimes(current['sunrise'], tz_offset).split(" ")[1]
    current['sunset'] = process_datetimes(current['sunset'], tz_offset).split(" ")[1]
    current['main'] = current['weather'][0]["main"]
    current['description'] = current['weather'][0]["description"]
    for idx, hour in enumerate(hourly):
        hourly[idx]['dt'] = process_datetimes(hour['dt'], tz_offset)

    return jsonify({
    "current_weather":current,
    "hourly_weather":hourly}, 200)

@app.route('/API/gearshed/<int:user_id>')
def get_user_gear_api(user_id):
    user = User.query.get_or_404(user_id)
    
    gear_list = [item.to_json() for item in UserGear.query.filter(UserGear.user_id == user.id)]
    return jsonify({"gear_list":gear_list}, 200)

@app.route("/API/comment/", methods=["POST"]) 
def add_user_comment_to_activity():
    data = request.get_json()
    act_comment = ActivityComment.create_activity_comment(data["user_id"], data["activity_id"], data["comment"])
    return jsonify({"data":act_comment.jsonify()}, 200)