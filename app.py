import os
from flask import Flask, render_template, request, flash, redirect, session, g, jsonify, send_from_directory
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db
from models import User, Activity, Challenge, Landmark, Gear, UserFriends, Admin, UserGear, ActivityComment
from forms import LoginForm, NewActivityForm, NewGearForm, NewLandmarkForm, NewChallengeForm, EditUserForm, NewUserForm, NewUserGearForm, NewCommentForm
from werkzeug.utils import secure_filename
import secret
import helpers
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


##############################################################################
# User signup/login/logout

def do_login(user):
    """Log in user."""
    session[CURR_USER_KEY] = user.id

def do_logout():
    """Logout user."""
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

def validate_signed_in(msg):
    '''Validate that a user is signed in, or flash an error message'''
    if not g.user:
        flash(f"{msg}", 'error')
        return False 
    return True 

def validate_correct_user(msg, user_id):
    '''Validate that a database entry has same user_id as the one stored in g'''
    if g.user.id != user_id:
        admin_ids = [id_tuple[0] for id_tuple in db.session.query(Admin.user_id).all()]
        if g.user.id not in admin_ids:
            flash(f"{msg}", 'error')
            return False 
    return True

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

##############################################################################
# Home pages (i.e., no requirement to be logged in)

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

@app.route('/users', methods=['GET'])
def show_all_users():
    '''Display all users, and handle friends if the user is logged in'''
    if not validate_signed_in("You must be logged in to view users"):
        return redirect('/login')
    users = User.query.all()
    return render_template('/users/users.html',users = users, num_photos_displayed=2)

##############################################################################
# User pages (require log in)

@app.route('/users/<int:user_id>', methods=['GET'])
def handle_individual_user(user_id):
    '''Show an individual user's page if accessed by a logged in user'''
    if not validate_signed_in("You must be logged in to view user page."):
        return redirect('/login')

    user = User.query.get_or_404(user_id)
    activities = [activity.setup_gpx_object() for activity in user.get_recent_activities()]

    return render_template('/users/user.html', user = user, activities=activities, 
     is_current_user = validate_correct_user('', user_id),
     num_photos_displayed=4)


@app.route('/users/<int:user_id>/delete', methods=["POST"])
def delete_user(user_id):
    '''Delete a user (if logged in, and deleting own account)'''
    if not validate_signed_in("You must be logged in to delete your account"):
        return redirect("/login")
    
    if not validate_correct_user("You can only delete your own account.",user_id):
        return redirect(f'/users/{g.user.id}')
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    return redirect('/register')

@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
def update_user(user_id):
    '''Show the update user profile form, and handle its submission'''
    if not validate_signed_in("You must be logged in to edit your account"):
        return redirect('/login')

    if not validate_correct_user("You can only edit your own account.", user_id):
        return redirect(f'/users/{user_id}')

    form = EditUserForm(obj=g.user)
    user = User.query.get_or_404(user_id)
    if form.validate_on_submit():
        form.populate_obj(user)
        db.session.commit()
        return redirect(f'/users/{user_id}')

    return render_template('/users/edit_user.html', form = form)


@app.route('/users/<int:user_id>/feed', methods=['GET'])
def show_user_feed(user_id):
    '''Show activities completed by athletes that the user is following'''
    if (not validate_signed_in("You must be logged in to view your feed.")):
        return redirect("/login")

    if not validate_correct_user("You can only view your own feed.", user_id):
        return redirect(f'/users/{g.user.id}/feed')
    
    activities = g.user.get_following_stories()
    activities = [activity.setup_gpx_object() for activity in activities]

    return render_template('/users/feed.html', user = g.user, activities = activities,
    num_photos_displayed=4)

##############################################################################
# Challenge routes

@app.route('/challenges', methods=['GET'])
def show_challenges():
    '''Show a list of challenges'''
    if g.user and g.user.is_admin():
        challenges = Challenge.query.all()
    elif g.user:
        challenges = g.user.get_available_challenges(return_objects = True)
    else:
        challenges = Challenge.get_official_challenges()
    if g.user:
        form= None 
    else:
        form = NewUserForm()
    return render_template('/challenges/challenges.html', 
    challenges = challenges, 
    form=form, 
    show_map = False, 
    show_planning = False, 
    allow_challenge_upload = True,
    num_photos_displayed=4)

@app.route('/challenges/new', methods=['GET', 'POST'])
def create_challenge():
    '''show a form to create challenges and handle its submission'''
    if not validate_signed_in('You must be signed in to create a challenge'):
        return redirect('/login')

    form = NewChallengeForm()

    form.gear.choices = [(item.id, f"{item.name}") for item in Gear.query.all()]

    form.landmarks.choices = g.user.get_available_landmarks()

    if form.validate_on_submit():
        name = form.name.data 
        description = form.description.data 
        gear = form.gear.data 

        landmarks = form.landmarks.data 
        try:
            challenge = Challenge.create_challenge(name, description, gear, landmarks, g.user.id)
            flash("Challenge created successfully", 'success')
            return redirect(f'/challenges/{challenge.id}')
        except Exception as e:
            flash("There was a server error, please try again.", 'error')
            flash(f"{e}", 'error')
            return redirect('/challenges/new')
    return render_template('challenges/new_challenge.html', form = form)

@app.route('/challenges/<int:challenge_id>', methods=['GET'])
def handle_challenges(challenge_id):
    '''Show a particular challenge to the user'''
    challenge = Challenge.query.get_or_404(challenge_id)
    map_options = helpers.get_landmark_map_options(challenge.landmarks)
    map_options['OPENWEATHERMAP_API_KEY'] = app.config['OPENWEATHERMAP_API_KEY']
    return render_template('/challenges/challenge.html', challenge=challenge,
     map_options = map_options, show_map = True, show_planning = True, landmarks=challenge.landmarks,
     num_photos_displayed=4)



@app.route('/challenges/<int:challenge_id>/edit', methods=['GET', 'POST'])
def edit_challenge(challenge_id):
    '''Show a form to edit a challenge, and handle its submission'''
    if not validate_signed_in("You must be logged in to edit challenges."):
        return redirect('/login')
    challenge = Challenge.query.get_or_404(challenge_id)

    if not validate_correct_user("You can only edit challenges that you created.", challenge.created_by):
        return redirect(f'/challenges/{challenge_id}')

    form = NewChallengeForm()
    if form.validate_on_submit():
        form.populate_obj(challenge)
        db.session.commit()
        return redirect(f'/challenges/{challenge_id}', form = form)

    form.name.data = challenge.name
    form.description.data = challenge.description
    gear = Gear.query.all()
    form.gear.choices = [(item.id, f"{item.name}") for item in gear]

    landmarks = Landmark.query.all()
    form.landmarks.choices = g.user.get_available_landmarks()
    return render_template('challenges/edit_challenge.html', form = form)

@app.route('/challenges/<int:challenge_id>/delete', methods=['POST'])
def delete_challenge(challenge_id):
    '''Delete a challenge from the database'''
    if not validate_signed_in("You must be logged in to delete a challenge"):
        return redirect("/login")

    challenge = Challenge.query.get_or_404(challenge_id)
    if not validate_correct_user("You can only delete challenges that you created.", challenge.created_by):
        return redirect(f"/users/{g.user.id}")
        
    db.session.delete(challenge)
    db.session.commit()
    flash("Challenge deleted successfully", 'success')
    return redirect(f"/challenges")


##############################################################################
# Landmark routes (some require login), will add administrator stuff at some point

@app.route('/landmarks', methods=['GET'])
def show_landmarks():
    '''Show a list of landmarks to the user'''
    if not g.user:
        landmarks = Landmark.get_official_landmarks()
    elif g.user.is_admin():
        landmarks = Landmark.query.all()
    else:
        landmarks = g.user.get_available_landmarks(return_objects=True)
    form = NewUserForm()
    return render_template('/landmarks/landmarks.html', 
    landmarks=landmarks, 
    user = g.user, 
    form=form,
    num_photos_displayed=4, 
    allow_landmark_upload = True)

@app.route('/landmarks/new', methods=['GET', "POST"])
def create_landmarks():  
    '''Show a form to create a landmark, and handle its submission'''
    if not validate_signed_in("You must be signed in to create a landmark"):
        return redirect('/login')

    form = NewLandmarkForm()
    if form.validate_on_submit():
        latitude = form.latitude.data
        longitude = form.longitude.data
        latitude, longitude = Landmark.format_lat_long(latitude, longitude)
        
        name = form.name.data
        img_url = form.img_url.data
        try:
            landmark = Landmark.add_landmark(latitude, longitude, name,img_url, g.user.id)
            flash("Successfully uploaded landmark", 'success')
            return redirect(f'/landmarks/{landmark.id}')
        except Exception as e:
            flash("There was an error during upload, try again", 'error')
            flash(f"{e}")
            return redirect("/landmarks/new")
    return render_template('/landmarks/new_landmark.html', form = form)

@app.route('/landmarks/<int:landmark_id>', methods=['GET'])
def handle_landmarks(landmark_id):
    '''Show a particular landmark to the user'''
    landmark = Landmark.query.get_or_404(landmark_id)
    if validate_signed_in(""):
        friend_ids = [f.id for f in g.user.following]
        activities = Activity.query.filter(Activity.user_id.in_(friend_ids)).all()
        for activity in activities:
            activity.setup_gpx_object()
        form = None
    else:
        form = NewUserForm()
        activities = None
    return render_template('/landmarks/landmark.html', 
    form = form,
    landmark=landmark,  
    activities=activities,
    num_photos_displayed=4, allow_landmark_upload = True)

@app.route('/landmarks/<int:landmark_id>/edit', methods=['GET','POST'])
def edit_landmarks(landmark_id):
    '''Show a form to edit a landmark and handle its submission'''
    landmark = Landmark.query.get_or_404(landmark_id)
    form = NewLandmarkForm()
    if form.validate_on_submit():
        form.populate_obj(landmark)
        db.session.commit()
        return redirect(f'/landmarks/{landmark_id}')
    else:
        form.latitude.data = landmark.latitude
        form.longitude.data = landmark.longitude 
        form.img_url.data = landmark.img_url
        form.name.data = landmark.name
    return render_template('landmarks/edit_landmark.html', form = form)

@app.route('/landmarks/<int:landmark_id>/delete', methods=['POST'])
def delete_landmarks(landmark_id):
    '''Delete a landmark'''
    if not validate_signed_in("You must be logged in to delete a landmark"):
        return redirect("/login")

    landmark = Landmark.query.get_or_404(landmark_id)

    if not validate_correct_user("You can only delete landmarks that you uploaded", landmark.created_by):
        return redirect(f'/users/{g.user.id}')
        
    db.session.delete(landmark)
    db.session.commit()
    return redirect('/landmarks')


##############################################################################
# Gear pages (some require login), will add administrator template at some point


@app.route('/gear', methods=['GET'])
def show_gear():
    '''Show a list of gear to the user'''
    gear = Gear.query.all()
    user = g.user if g.user else None
    form = NewUserForm() if not g.user else None
    return render_template("/gear/gear.html", user = user, gear = gear, num_photos_displayed=4, form = form, allow_user_gear_upload = True)

@app.route('/gear/new', methods=['GET', 'POST'])
def create_gear():
    '''Show a form to create a new piece of gear and handle its submission'''
    if not g.user or not g.user.is_admin():
        # only admin can create gear
        flash("You must be an administrator to create gear", 'error')
        return redirect('/')
    
    form = NewGearForm()
    if form.validate_on_submit():
        name = form.name.data 
        description = form.description.data
        store_url = form.store_url.data
        try:
            gear = Gear.create_gear(name, description, store_url)
            flash("Gear added successfully", 'success')
            return redirect(f"/gear/{gear.id}")
        except Exception as e:
            flash("An error occurred, please try again", 'error')
            flash(f"{e}")
            return redirect("/gear/new")
        
    return render_template("/gear/new_gear_item.html", form=form)

@app.route('/gear/<int:gear_id>', methods=['GET'])
def handle_gear(gear_id):
    '''Show information for a particular piece of gear to the user'''
    gear = Gear.query.get_or_404(gear_id)
    return render_template("/gear/gear_item.html", gear = gear, num_photos_displayed=4)

@app.route('/gear/<int:gear_id>/edit', methods=['GET', 'POST'])
def edit_gear(gear_id):
    '''Show a form to edit a piece of gear, and handle its submission'''
    item = Gear.query.get_or_404(gear_id)
    form = NewGearForm(obj=item)
    if form.validate_on_submit():
        try:
            form.populate_obj(item)
            db.session.commit()
            return redirect(f"/gear/{gear_id}")
        except Exception as e:
            flash("A server error occurred editing gear, please try again.", 'error')
            flash(f"{e}", 'error')
        return redirect(f'/gear/{gear_id}/edit')

    return render_template("/gear/edit_gear.html", form = form)

@app.route('/gearshed')
def show_user_gear():
    if not validate_signed_in("You must be logged in to view your Gear Shed!"):
        return redirect("/login")
    gear = UserGear.query.all()
    return render_template("/gear/gear_shed.html", user = g.user, gear = gear, num_photos_displayed=4, allow_user_gear_upload = True)

@app.route('/gearshed/<int:gear_id>/delete', methods=['POST'])
def delete_gear(gear_id):
    '''Delete a piece of gear from the database'''
    if not validate_signed_in("You must be logged in to delete gear"):
        return redirect("/login")

    gear = UserGear.query.get_or_404(gear_id)
    if not validate_correct_user("You can only delete gear from your own gearshed.",gear.user_id):
        return redirect("/gearshed")

    db.session.delete(gear)
    db.session.commit()
    return redirect(f"/gearshed")

@app.route('/gearshed/new', methods=['GET', 'POST'])
def create_user_gear():
    '''Show a form to create a new piece of gear and handle its submission'''
    if not validate_signed_in("You must be logged in to create gear for your Gear Shed."):
        return redirect("/login")

    form = NewUserGearForm()
    if form.validate_on_submit():
        name = form.name.data 
        model = form.model.data
        brand = form.brand.data
        weight = form.weight.data
        time_used = form.time_used.data
        try:
            UserGear.create_gear(name, brand, model, weight, time_used, g.user.id)
            flash("Gear added successfully", 'success')
            return redirect("/gearshed")
        except Exception as e:
            flash("An error occurred, please try again", 'error')
            flash(f"{e}")
            return redirect("/gearshed/new")
        
    return render_template("gear/new_gear_item.html", form=form)


##############################################################################
# Activity pages (some require login)


@app.route('/activities/new', methods=['GET', "POST"])
def create_activity():
    '''Show a form to create a new activity, and handle its submission'''
    if not validate_signed_in("You must be logged in to upload an activity"):
        return redirect("/login")

    form = NewActivityForm()

    form.challenge.choices = g.user.get_available_challenges()
    gear = Gear.query.all()
    form.gear.choices = [(item.id, item.name) for item in gear]

    if form.validate_on_submit():
        try:
            name = form.name.data
            challenge_id = form.challenge.data
            style = form.style.data 
            if form.gps_file.data:
                gps_data = request.files['gps_file'].read()
            else:
                gps_data = None
            pics = request.files.getlist(form.images.name)
            notes = form.notes.data 
            gear = form.gear.data

            activity = Activity.add_activity(g.user.id, name, challenge_id, style, gps_data, notes, gear, pics, directory = app.config['UPLOAD_FOLDER'])
            return redirect(f'/activities/{activity.id}')
        
        except Exception as e:
            flash("There was an error uploading this activity", 'error')
            flash(f"{e}", 'error')
            return redirect('/activities/new')
    return render_template('activities/new_activity.html', form= form)

@app.route('/activities/<int:activity_id>', methods=['GET'])
def show_activity(activity_id):
    '''Show a particular activity to a user'''
    activity = Activity.query.get_or_404(activity_id)

    if not validate_signed_in("You must be logged in to view users activities"):
        return redirect("/login")

    if (activity.user is not g.user ) and (activity.user not in g.user.following) and not g.user.is_admin():
        flash("You must be following an athlete to view their activities.", 'error')
        return redirect(f'/users')

    if activity.gps_file:
        activity.setup_gpx_object()
    
    comment_form = NewCommentForm()
    return render_template('/activities/activity.html', activity=activity, num_photos_displayed=4, comment_form = comment_form)


@app.route('/activities/<int:activity_id>/delete', methods=['POST'])
def delete_user_activities(activity_id):
    '''Delete an activity from the database'''
    if not validate_signed_in("You must be logged in to delete an activity."):
        return redirect("/login")

    activity = Activity.query.get_or_404(activity_id)

    if (g.user.id != activity.user_id) and (not g.user.is_admin()):
        flash("You can only delete your own activities", 'error')
        return redirect(f'/users/{g.user.id}')


    db.session.delete(activity)
    db.session.commit()
    flash("Activity deleted successfully", "success")
    return redirect(f"/users/{g.user.id}")
    
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