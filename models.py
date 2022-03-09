"""SQLAlchemy models for Warbler."""

from datetime import datetime
from flask import jsonify
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
import io
from PIL import Image
import gpxpy
from gpx_converter import Converter
from math import  pi, acos, sin, cos, floor
import json
from flask import current_app
from werkzeug.utils import secure_filename
import requests as python_requests
import logging
import boto3
from botocore.exceptions import ClientError

bcrypt = Bcrypt()
db = SQLAlchemy()

def adjust_map_options_boundaries(map_options, BUFFER_SIZE = 0.01):
    '''Allows us to add a buffer to the map, so that the activity doesn't touch the map borders'''
    map_options["longitude_min"] -= BUFFER_SIZE
    map_options["latitude_min"]  -= BUFFER_SIZE
    map_options["longitude_max"] += BUFFER_SIZE
    map_options["latitude_max"]  += BUFFER_SIZE
    return map_options

def connect_db(app):
    """
    Connect this database to provided Flask app.
    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)

class UserFriends(db.Model):
    '''A table for handling follower/foloweee relationships'''
    __tablename__ = 'users_friends'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)

    user_being_followed_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade'),
        primary_key = True
    )

    user_following_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade'),
        primary_key = True
    )
    def to_json(self):
        s = self
        return jsonify({"id":s.id, 
        "user_being_followed_id": s.user_being_followed_id, 
        "user_following_id": s.user_following_id
        })


class ChallengeLandmark(db.Model):
    '''An intermediary table for linking challenges to landmarks'''
    __tablename__='challenges_landmarks'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)

    challenge_id = db.Column(db.Integer,
    ForeignKey('challenges.id', ondelete='cascade'),
    nullable = False)

    landmark_id = db.Column(db.Integer,
    ForeignKey('landmarks.id', ondelete='cascade'),
    nullable = False)

class ActivityComment(db.Model):
    '''An table for storing comments on activities'''
    __tablename__ = 'activities_comments'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow(),
    )

    comment = db.Column(db.Text, nullable = False)

    activity_id = db.Column(db.Integer,
    ForeignKey('activities.id', ondelete='cascade'),
    nullable = True)

    user_id = db.Column(db.Integer,
    ForeignKey('users.id', ondelete='cascade'),
    nullable = True)

    user = db.relationship("User")

    @classmethod 
    def create_activity_comment(cls, user_id, activity_id, comment):
        act_comment = ActivityComment(user_id = user_id, activity_id = activity_id, comment = comment)
        db.session.add(act_comment)
        db.session.commit()
        return act_comment
    
    def jsonify(self):
        return {"user_id":self.user_id, "activity_id":self.activity_id, "comment":self.comment}

class ActivityGear(db.Model):
    '''A table for linking gear to completed activities'''
    __tablename__ = 'activities_gear'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)

    activity_id = db.Column(db.Integer,
    ForeignKey('activities.id', ondelete='cascade'),
    nullable = True)

    gear_id = db.Column(db.Integer,
    ForeignKey('gear.id', ondelete='cascade'),
    nullable = True)

class ChallengeGear(db.Model):
    '''A table for linking recommended gear to challenges'''
    __tablename__ = 'challenges_gear'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)

    challenge_id = db.Column(db.Integer,
    ForeignKey('challenges.id', ondelete='cascade'),
    nullable = True)

    gear_id = db.Column(db.Integer,
    ForeignKey('gear.id', ondelete='cascade'),
    nullable = True)


class ActivityImages(db.Model):
    '''A table for linking user images to activities and users'''
    __tablename__ = 'activities_images'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)

    activity_id = db.Column(db.Integer,
    ForeignKey('activities.id', ondelete='cascade'),
    nullable = True)

    user_id = db.Column(db.Integer,
    ForeignKey('users.id', ondelete='cascade'),
    nullable = False)

    tiny_image_url = db.Column(db.Text, nullable = True)
    medium_image_url = db.Column(db.Text, nullable = True)
    large_image_url = db.Column(db.Text, nullable = True)

    activity = db.relationship("Activity", backref='images')

    user = db.relationship("User", backref = 'images')

    @classmethod
    def create_activity_image(cls, activity_id, user_id, image_data):
        # append user_id to the filename to minimize the chance of collisions
        valid_filesizes = [(500, 500), (320, 320), (128, 128)]
        filenames = []
        for size in valid_filesizes:
            filenames.append(f"{size[0]}_{user_id}_{secure_filename(image_data.filename)}")
        
        # Add the image to the database
        activity_image = ActivityImages(activity_id = activity_id, 
        user_id = user_id,
        tiny_image_url = filenames[2],
        medium_image_url = filenames[1],
        large_image_url = filenames[0]
        )

        db.session.add(activity_image)
        db.session.commit()

        # replace the original image's filename with the new once, and submit to amazon S3 database
        for idx, filename in enumerate(filenames):
            local_img = Image.open(image_data)
            in_memory_file = io.BytesIO()
            size = valid_filesizes[idx]
            local_img.thumbnail(size)
            local_img.save(in_memory_file, format = local_img.format)
            in_memory_file.seek(0)
            response = upload_user_image_to_S3(in_memory_file, current_app.config['SOKA_USER_IMAGE_BUCKET'], filename, image_data.content_type)
        return activity_image

    @classmethod
    def create_activity_image_from_url(cls, activity_id, user_id, image_url_list):
        activity_image = ActivityImages(activity_id = activity_id,
        user_id = user_id,
        tiny_image_url = image_url_list[0],
        medium_image_url = image_url_list[1],
        large_image_url = image_url_list[2])
        db.session.add(activity_image)
        db.session.commit()
        return activity_image
    
    def get_activity_image_s3_url(self, image_size_str = 'medium'):
        # use presigned URL to generate a URL that can display the image on a webpage
        image_object_to_request = None 
        if image_size_str.lower() == 'tiny':
            image_object_to_request = self.tiny_image_url 
        elif image_size_str.lower() == 'medium':
            image_object_to_request = self.medium_image_url 
        elif image_size_str.lower() == 'large':
            image_object_to_request = self.large_image_url
        else:
            raise ValueError("get_activity_image_s3_url: image_size_str must be a member of the set {'tiny', 'medium', 'large'}")
        url = create_presigned_url(current_app.config['SOKA_USER_IMAGE_BUCKET'], f"{image_object_to_request}")
        response = python_requests.get(url)
        return response.url

    def __repr__(self):
        return f"Activity Image {self.id} references activity {self.activity_id} stored at {self.tiny_image_url}."

class Admin(db.Model):
    __tablename__ = 'admins'
    user_id = db.Column(db.Integer, ForeignKey('users.id', ondelete='cascade'), primary_key= True)
    user = db.relationship("User")

###########################################################################
# Create models for individual objects within our schema 
class User(db.Model):
    '''A table for storing user information'''
    __tablename__='users'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    first_name = db.Column(db.String(50), nullable = False)
    last_name =  db.Column(db.String(50), nullable = False)
    password = db.Column(db.Text, nullable = False)
    location = db.Column(db.String(100), nullable = True)
    email = db.Column(db.String(100), nullable = False, unique = True)

    activities = db.relationship('Activity', backref = 'user')

    challenges = db.relationship('Challenge',
    secondary = 'activities',
    backref='users')

    followers = db.relationship(
        'User',
        secondary='users_friends',
        primaryjoin= (UserFriends.user_being_followed_id == id),
        secondaryjoin= (UserFriends.user_following_id == id)
    )

    following = db.relationship(
        'User',
        secondary='users_friends',
        primaryjoin= (UserFriends.user_following_id == id),
        secondaryjoin= (UserFriends.user_being_followed_id == id)
    )
    
    def __repr__(self):
        return f"User #{self.id}: {self.first_name} {self.last_name} in {self.location} with email {self.email}"

    @classmethod 
    def sign_up(cls, email, first_name, last_name, password, location):
        '''Create a user object with a hashed password, and add it to the database.'''
        hashed_pwd = bcrypt.generate_password_hash(password).decode("UTF-8")
        user = User(
            first_name = first_name.capitalize(),
            last_name = last_name.capitalize(),
            email = email,
            password = hashed_pwd,
            location = location.capitalize()
        )
        db.session.add(user)
        db.session.commit()
        return user

    @classmethod
    def authenticate(cls, email, password):
        '''Authenticate a user by email and password'''
        user = cls.query.filter_by(email=email).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user
        return False

    @classmethod
    def sign_up_from_form(cls, form):
        '''Take data from signup form, create a user object, submit it to User.sign_up to add it to the database.'''
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        password = form.password.data
        location = form.location.data
        return User.sign_up(email, first_name, last_name, password, location)

    def get_recent_activities(self, number = 3):
        activities = Activity.query\
            .filter(Activity.user_id == self.id)\
                .order_by(Activity.timestamp.desc())\
                    .limit(number).all()
        return activities

    def is_admin(self):
        admin_ids = [admin.user_id for admin in Admin.query.all()]
        if self.id in admin_ids:
            return True 
        return False

    def get_available_landmarks(self, return_objects = False):
            '''A user only has access to user created landmarks if following the creator or the creator is an admin'''
            valid_ids = [self.id]
            if self.following:   
                valid_ids.extend([user.id for user in self.following])

            admin_ids = [admin.user_id for admin in Admin.query.all()]
            valid_ids.extend(admin_ids)
            landmarks = Landmark.query.filter(Landmark.created_by.in_(valid_ids)).all()
            if return_objects:
                return landmarks
            options = [None] * len(landmarks)
            for idx, landmark in enumerate(landmarks):
                display_string = f"{landmark.name} "
                if landmark.created_by in admin_ids:
                    options[idx] = (landmark.id, display_string + "added by SOKA")
                else:
                    options[idx] = (landmark.id, display_string + f"added by {landmark.creator.first_name} {landmark.creator.last_name}")
            return options

    def get_available_challenges(self, return_objects = False):
        '''A user only has access to user created challenges if following the creator or the creator is an admin'''
        if self.following:   
            valid_ids = [user.id for user in self.following]
        else:
            valid_ids = []
        admin_ids = [admin.user_id for admin in Admin.query.all()]
        valid_ids.extend(admin_ids)
        valid_ids.append(self.id)
        challenges = Challenge.query.filter(Challenge.created_by.in_(valid_ids)).all()
        if return_objects:
            return challenges
        options = [None] * len(challenges)
        for idx, challenge in enumerate(challenges):
            display_string = f"{challenge.name} "
            if challenge.created_by in admin_ids:
                options[idx] = (challenge.id, display_string + "Created by SOKA")
            else:
                options[idx] = (challenge.id, display_string + f"Created by {challenge.creator.first_name} {challenge.creator.last_name}")
        return options

    def get_following_stories(self):
        '''Select stories by users being followed by the instance user'''
        friend_ids = [user.id for user in self.following]
        return Activity.query.filter(Activity.user_id.in_(friend_ids))  

    def get_recent_images(self, number = 12, image_size_str = 'medium'):
        '''get recent images by the current user'''
        image_object_to_request = None 
        if image_size_str.lower() not in ('tiny', 'medium', 'large'):
            raise ValueError("get_activity_image_s3_url: image_size_str must be a member of the set {'tiny', 'medium', 'large'}")
        act_imgs = db.session\
            .query(ActivityImages, Activity.timestamp)\
                .filter(ActivityImages.user_id==self.id, ActivityImages.activity_id==Activity.id)\
                    .order_by(Activity.timestamp.desc())\
                        .limit(number).all()
        return [act_img[0] for act_img in act_imgs]



class Activity(db.Model):
    '''A table for storing information about an uploaded activity'''
    __tablename__='activities'

    id = db.Column(db.Integer, 
    primary_key = True, 
    autoincrement = True)

    name = db.Column(db.String(200), nullable = False)

    user_id = db.Column(db.Integer, 
    db.ForeignKey('users.id', ondelete='cascade'),
    nullable = False)

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow(),
    )

    challenge_id = db.Column(db.Integer, 
        db.ForeignKey('challenges.id', ondelete='cascade'), 
        nullable = False
    )

    was_successful = db.Column(db.Boolean, nullable = True)

    style = db.Column(db.String(40), nullable = True)

    gps_file = db.Column(db.Text(), nullable = True)

    notes = db.Column(db.Text, nullable = True)

    comments = db.relationship("ActivityComment")

    gear = db.relationship('Gear',
    secondary='activities_gear',
    backref = 'activities')

    challenge = db.relationship('Challenge')
    def __repr__(self):
        return f"Activity #{self.id}, was_successful = {self.was_successful} at attempting challenge {self.challenge.name}"
    @classmethod 
    def add_activity(cls, user_id, name, challenge_id, style, gps_data, notes, gear, pics, directory='gpx_files'):
        '''A method for creating a new activity, associating gear/images with the activity/ and adding each to the database'''

        new_activity = Activity(user_id = user_id, 
        name = name.capitalize(), 
        challenge_id = challenge_id, 
        style = style, 
        notes = notes)

        db.session.add(new_activity)
        db.session.commit()

        if gps_data:
            gps_filename = Activity.save_gpx_file(new_activity, gps_data, directory)
            new_activity.gps_file = gps_filename 

        gear_list = Gear.query.filter(Gear.id.in_(gear))
        if gear_list:
            activity_gear = []
            for item in gear_list:
                ag = ActivityGear(activity_id = new_activity.id, gear_id = item.id)
                activity_gear.append(ag)
            db.session.add_all(activity_gear)
            db.session.commit()

        is_successful = Activity.validate_activity(new_activity)

        new_activity.was_successful = is_successful 
        db.session.add(new_activity)
        db.session.commit()

        if pics:
            for pic in pics:
                ActivityImages.create_activity_image(new_activity.id, user_id, pic)
        return new_activity

    @classmethod 
    def save_gpx_file(self, activity, gps_data, directory):
        '''A method for saving an uploaded gpx file to file storage'''
        gpx = gpxpy.parse(gps_data)
        filename = f"./{directory}/{activity.id}.gpx"
        with open(filename, 'w') as storage_file:
            storage_file.write(gpx.to_xml())
        return filename

    @classmethod
    def validate_activity(cls, activity):
        '''A method for ensuring a user visited all of the landmarks for a challenge'''
        challenge = activity.challenge
        if challenge.name == 'None':
            return True 

        if not activity.gps_file:
            return False 

        landmarks = challenge.landmarks
        for landmark in landmarks:
            if not Activity.validate_landmark(activity, landmark):
                return False
        return True

    @classmethod
    def validate_landmark(cls, activity, landmark):
        '''A method for ensuring a user visited a particular landmark'''
        RADIUS = 50 # METERS
        point1 = (landmark.get_longitude(), landmark.get_latitude())
        
        gpx_object = GPXHandler(activity)
        coordinates = gpx_object.map_options['coordinates']
        for coordinate in coordinates:
            if GPXHandler.compute_distance_between_two_points(point1, coordinate) < RADIUS:
                return True
        return False

    def get_processed_datetime_string(self):
        '''format the datetime into a more readable format'''
        t = self.timestamp
        return f"{t.month}-{t.day}-{t.year} at {t.hour}:{t.minute}"

    def setup_gpx_object(self):
        if self.gps_file:
            self.gpx = GPXHandler(self)
        else:
            self.gpx = None
        return self

    def get_static_map(self):
        pass


class Challenge(db.Model):
    '''A table for storing information about a challenge'''
    __tablename__='challenges'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.String(50), nullable = False)
    description = db.Column(db.Text, nullable = False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='cascade'), nullable = False)

    creator = db.relationship('User', backref = 'created_challenges')

    gear = db.relationship('Gear',
    secondary = 'challenges_gear',
    backref = 'challenges')

    landmarks = db.relationship('Landmark',
    secondary='challenges_landmarks',
    backref = 'challenges')


    @classmethod 
    def create_challenge(cls, name, description, gear_ids, landmark_ids, user_id):
        '''A method for creating a challenge, associating gear/landmarks with the challenge, and adding it all to the database'''
        challenge = Challenge(name = name.capitalize(), description = description.capitalize(), created_by = user_id)
        db.session.add(challenge)
        db.session.commit()

        challenge_gear = []
        gear_list = Gear.query.filter(Gear.id.in_(gear_ids))
        for item in gear_list:
            cg = ChallengeGear(challenge_id = challenge.id, gear_id = item.id)
            challenge_gear.append(cg)
        db.session.add_all(challenge_gear)
        db.session.commit()

        landmark_list = Landmark.query.filter(Landmark.id.in_(landmark_ids))
        challenge_landmarks = []
        for landmark in landmark_list:
            cl = ChallengeLandmark(challenge_id = challenge.id, landmark_id = landmark.id)
            challenge_landmarks.append(cl)
        db.session.add_all(challenge_landmarks)
        db.session.commit()
        return challenge
        
    @classmethod
    def get_official_challenges(cls):
        admin_ids = db.session.query(Admin.user_id).all()
        return Challenge.query.filter(Challenge.created_by.in_(admin_ids)).all()

class Landmark(db.Model):
    '''A table for storing information about landmarks'''
    __tablename__= 'landmarks'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    latitude = db.Column(db.String(20), nullable = False)
    longitude = db.Column(db.String(20), nullable = False)
    img_url = db.Column(db.Text, nullable = False)
    name = db.Column(db.String(100), nullable = False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='cascade'), nullable = False)
    creator = db.relationship('User', backref = 'created_landmarks')

    def get_latitude(self):
        '''A method for taking one GPS format (NESW), and converting it into another (radial)'''
        parsed_lat = self.latitude.split(' ')
        latitude = float(parsed_lat[0])
        return latitude if parsed_lat[1].upper() == 'N' else -1 * latitude

    def get_longitude(self):
        '''A method for taking one GPS format (NESW), and converting it into another (radial)'''
        parsed_long = self.longitude.split(' ')
        longitude = float(parsed_long[0])
        return longitude if parsed_long[1].upper() == 'E' else -1 * longitude

    def get_latitude_int(self):
        '''A method for grabbing a coarser GPS representation (integer) instead of float.'''
        return int(self.get_latitude())

    def get_longitude_int(self):
        '''A method for grabbing a coarser GPS representation (integer) instead of float.'''
        return int(self.get_longitude())

    def get_gps_coordinates(self):
        '''A method for extracting gps coordinates in the correct format'''
        return [self.get_longitude(),self.get_latitude()]

    @classmethod 
    def format_lat_long(cls, latitude, longitude):
        '''A method to ensure the precision is correct on GPS coordinates'''
        # latitude format ##.######
        latitude = Landmark.format_coordinate(latitude, 2, 6)

        # longitude format ###.######
        longitude = Landmark.format_coordinate(longitude, 3, 6)
        return latitude, longitude

    @classmethod
    def format_coordinate(cls, value, n_digits, n_required):
        '''A method for handling uploaded GPS coordinates'''
        # split input up into parts

        value = value.replace(u"\N{DEGREE SIGN}", "").replace(" ", "").split(".")

        left_of_decimal = value[0]

        right_of_decimal = value[1][:-1]

        n_places = len(right_of_decimal)
        direction = value[1][-1]

        return f"{left_of_decimal.zfill(n_digits)}.{right_of_decimal.ljust(n_required, '0')} {direction}"

    @classmethod 
    def add_landmark(cls, latitude, longitude, name, img_url, user_id):
        '''A method for adding a landmark to the database'''
        name = name.capitalize()
        new_landmark = Landmark(latitude = latitude, longitude = longitude, name = name, img_url = img_url, created_by = user_id)
        db.session.add(new_landmark)
        db.session.commit()
        return new_landmark

    @classmethod
    def get_official_landmarks(cls):
        admin_ids = db.session.query(Admin.user_id).all()
        return Landmark.query.filter(Landmark.created_by.in_(admin_ids)).all()



class Gear(db.Model):
    '''A table for storing information about gear'''
    __tablename__='gear'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.String(40), nullable = False, unique = True)
    description = db.Column(db.Text, nullable = False)
    store_url = db.Column(db.Text, nullable = True)

    @classmethod 
    def create_gear(cls, name, description, store_url):
        '''A method for creating gear, and adding the information to the database'''
        name = name.capitalize()
        description = description.capitalize()
        if store_url:
            gear = Gear(name = name, description = description, store_url = store_url)
        else:
            gear = Gear(name = name, description = description)
        db.session.add(gear)
        db.session.commit()
        return gear

    def __repr__(self):
        return f"Gear #{self.id}: {self.name} has description '{self.description}'"

class UserGear(db.Model):
    '''A table for storing information about gear'''
    __tablename__='user_gear'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="cascade"))
    name = db.Column(db.String(40), nullable = False, unique = True)
    brand = db.Column(db.String(40), nullable = False)
    model = db.Column(db.String(60), nullable = False)
    weight = db.Column(db.Float, nullable = True)

    time_used = db.Column(db.Float, nullable = False, default= 0)

    @classmethod 
    def create_gear(cls, name, brand, model, weight, time_used, user_id):
        '''A method for creating gear, and adding the information to the database'''
        name = name.capitalize()
        gear = UserGear(name = name, brand=brand.capitalize(), model=model.capitalize(), weight = weight, time_used = time_used, user_id = user_id)
        db.session.add(gear)
        db.session.commit()
        return gear

    def __repr__(self):
        return f"User gear #{self.id}: {self.name} owns a {self.model} by {self.brand} that weights {weight} and has been used for {time_used} hours"

    def to_json(self):
        s = self
        return {
        "id":s.id, 
        "user_id": s.user_id,
        "name": s.name, 
        "brand": s.brand,
        "model": s.model,
        "weight": s.weight,
        "time_used": s.time_used
        }
###########################################################################
# Classes for additional functionality

class GPXHandler():
    '''A class for handling .gpx files and convenience functions'''
    def __init__(self, activity):
        self.gpx_filename = activity.gps_file

        self.map_options = self.construct_map_options_from_gpx()
        self.statistics = self.compute_statistics_from_gpx()
        pass

    def compute_statistics_from_gpx(self):
        '''A method for computing any relevant activity statistics from a gpx file'''
        gpx_filename = self.gpx_filename 
        statistics =dict()
        with open(gpx_filename, 'r') as f:
            gpx = gpxpy.parse(f)
            duration_in_seconds = int(gpx.get_duration())
            minutes = duration_in_seconds / 60
            seconds = floor(duration_in_seconds % 60)
            hours = floor(minutes / 60)
            minutes_remaining = floor(minutes % 60)
            duration = f'{hours}:{minutes_remaining}:{seconds}'
            statistics['duration'] = duration
            climb_descent = gpx.get_uphill_downhill()
            statistics['climb'] = int(climb_descent[0])
            statistics['descent'] = int(climb_descent[1])
            extreme_elevations = gpx.get_elevation_extremes()
            statistics['min_elevation'] = int(extreme_elevations[0])
            statistics['max_elevation'] = int(extreme_elevations[1])
        return statistics

    def construct_map_options_from_gpx(self):
        '''A method for creating the map_options object needed to display the activity on a map'''
        gpx_filename = self.gpx_filename
        with open(gpx_filename,'r') as f:
            gpx = gpxpy.parse(f)
            bounds = gpx.get_bounds()
            minlat, minlong, maxlat, maxlong = bounds.min_latitude, bounds.min_longitude, bounds.max_latitude, bounds.max_longitude
            max_map_extent = GPXHandler.compute_map_distance(minlat, minlong, maxlat, maxlong)
            zoom = GPXHandler.compute_map_zoom(max_map_extent)

            map_options = dict()
            map_options["longitude_min"] = minlong
            map_options["latitude_min"]  = minlat
            map_options["longitude_max"] = maxlong
            map_options["latitude_max"]  = maxlat
            map_options['latitude_center']  = (minlat + maxlat)/2
            map_options['longitude_center'] = (minlong + maxlong)/2
            map_options['zoom'] = zoom

            map_options = adjust_map_options_boundaries(map_options)
            self.convert_gpx_to_json(gpx_filename)

            with open(gpx_filename.replace('.gpx', '.json')) as file:
                json_data =json.load(file)

            map_options['coordinates'] = self.convert_json_to_coordinates(json_data)
            
        return map_options
    @classmethod 
    def compute_map_distance(cls, min_lat, min_long, max_lat, max_long):
        '''Used to compute the size we need for displaying a map that covers specific gps points'''
        # https://www.geeksforgeeks.org/program-distance-two-points-earth/

        # convert lat long to radians
        coordinate_array_degrees = [min_lat, min_long, max_lat, max_long]
        ca_radians = [deg * pi / 180 for deg in coordinate_array_degrees]

        # compute avg lat  long
        avg_lat = (ca_radians[0] + ca_radians[2])/2
        avg_lon = (ca_radians[1] + ca_radians[3])/2

        # Compute vertical and horizontal extent using fixed average values in the perpendicular direction, computed in meters
        map_width = abs(1000 * 1.609344 * 3963.0 * acos((sin(avg_lat) * sin(avg_lat)) + cos(avg_lat) * cos(avg_lat) * cos(ca_radians[1] - ca_radians[3])))
        map_height = abs(1000 * 1.609344 * 3963.0 * acos((sin(ca_radians[3]) * sin(ca_radians[1])) + cos(ca_radians[3]) * cos(ca_radians[1]) * cos(avg_lon - avg_lon)))

        return max(map_width, map_height)

    @classmethod 
    def compute_distance_between_two_points(cls, point1, point2):
        '''Used to compute the distance between two points on a map given lat/long'''
        # https://www.geeksforgeeks.org/program-distance-two-points-earth/

        # convert lat long to radians (long, lat, long, lat)
        coordinate_array_degrees = [point1[1], point1[0], point2[1], point2[0]]
        ca_radians = [deg * pi / 180 for deg in coordinate_array_degrees]

        # Compute vertical and horizontal extent using fixed average values in the perpendicular direction, computed in meters
        distance = abs(1000 * 1.609344 * 3963.0 * acos((sin(ca_radians[1]) * sin(ca_radians[3])) + cos(ca_radians[1]) * cos(ca_radians[3]) * cos(ca_radians[2] - ca_radians[0])))
        return distance

    @classmethod
    def compute_map_zoom(cls, max_map_extent):
        '''A method for computing which map zoom to start a map on (approximately)'''
        # max extent should be in meters

        # zoom levels : meters per pixel (taken from MAPBOX api)
        zoom_levels = {"0": 60000,
        "1": 30000,
        "2": 15000,
        "3": 7500,
        "4": 4000,
        "5": 1900,
        "6": 1000,
        "7": 500,
        "8": 250,
        "9": 120,
        "10":60,
        "11":30,
        "12":15,
        "13":7.5,
        "14":4,
        "15":2,
        "16":1,
        "17":0.5,
        "18":0.299,
        "19":0.149,
        "20":0.075,
        "21":0.037,
        "22":0.019}

        zoom = 22
        NUM_PIXELS = 512
        while zoom > -1:
            meters_per_pixel = zoom_levels[f"{zoom}"]
            map_size = NUM_PIXELS * meters_per_pixel
            if max_map_extent < map_size:
                return zoom
            else:
                zoom -= 1
        pass
        
    def convert_gpx_to_json(self, input_filename):
        '''A method for converting gpx to json, and storing the resulting file on the filesystem'''
        output_filename = input_filename.replace('.gpx', '.json')
        Converter(input_file=f'{input_filename}').gpx_to_json(output_file=output_filename)
        pass

    def convert_json_to_coordinates(self, json_obj):
        '''A method for extracting a coordinate list from the JSON file representation of the original .GPX file'''
        latitudes = json_obj['latitude']
        longitudes = json_obj['longitude']
        times = json_obj['time']
        altitudes=json_obj['altitude']

        coordinates = [[long, lat] for long, lat in zip(longitudes.values(), latitudes.values())]

        return coordinates


#### SETUP AWS, code generally formatted based on code from boto3
def create_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3',
    aws_access_key_id=current_app.config['SOKA_PRESIGNED_URL_ACCESS_KEY'],
    aws_secret_access_key=current_app.config['SOKA_PRESIGNED_URL_SECRET_ACCESS_KEY']
    )

    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response

def upload_user_image_to_S3(file, bucket_name, filename, content_type):
    """
    Docs: http://boto3.readthedocs.io/en/latest/guide/s3.html
    """
    try:
        s3 = boto3.client(
        "s3",
        aws_access_key_id=current_app.config['SOKA_PRESIGNED_URL_ACCESS_KEY'],
        aws_secret_access_key=current_app.config['SOKA_PRESIGNED_URL_SECRET_ACCESS_KEY']
        )
        s3.upload_fileobj(
            file,
            bucket_name,
            filename,
            ExtraArgs={
                "ContentType": content_type    #Set appropriate content type as per the file
            }
        )
    except Exception as e:
        return e
    return filename