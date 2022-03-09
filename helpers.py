from flask import  flash, g
from models import Admin
from app import db


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

def adjust_map_options_boundaries(map_options, BUFFER_SIZE = 0.01):
    '''Allows us to add a buffer to the map, so that the activity doesn't touch the map borders'''
    map_options["longitude_min"] -= BUFFER_SIZE
    map_options["latitude_min"]  -= BUFFER_SIZE
    map_options["longitude_max"] += BUFFER_SIZE
    map_options["latitude_max"]  += BUFFER_SIZE
    return map_options

def get_landmark_map_options(landmarks):
    '''creates the map_options object needed to display landmarks on the map'''
    longitudes = [landmark.get_longitude()  for landmark in landmarks]
    latitudes = [landmark.get_latitude() for landmark in landmarks]

    map_options = dict()
    map_options['longitude_min'] = min(longitudes) 
    map_options['longitude_max'] = max(longitudes)
    map_options['latitude_min'] = min(latitudes)
    map_options['latitude_max'] = max(latitudes)
    map_options['zoom'] = 6

    adjust_map_options_boundaries(map_options)
    return map_options





