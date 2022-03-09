import os
from flask import Blueprint, render_template,  flash, redirect, g, current_app
from app import db
from models import Challenge, Landmark, Gear
from forms import NewChallengeForm, NewUserForm
from helpers import validate_correct_user, validate_signed_in, get_landmark_map_options

def adjust_map_options_boundaries(map_options, BUFFER_SIZE = 0.01):
    '''Allows us to add a buffer to the map, so that the activity doesn't touch the map borders'''
    map_options["longitude_min"] -= BUFFER_SIZE
    map_options["latitude_min"]  -= BUFFER_SIZE
    map_options["longitude_max"] += BUFFER_SIZE
    map_options["latitude_max"]  += BUFFER_SIZE
    return map_options  
##############################################################################
# Challenge routes
bp = Blueprint('challenges', __name__, url_prefix="/challenges")

@bp.route('', methods=['GET'])
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

@bp.route('/new', methods=['GET', 'POST'])
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

@bp.route('/<int:challenge_id>', methods=['GET'])
def handle_challenges(challenge_id):
    '''Show a particular challenge to the user'''
    challenge = Challenge.query.get_or_404(challenge_id)
    map_options = get_landmark_map_options(challenge.landmarks)
    map_options['OPENWEATHERMAP_API_KEY'] = current_app.config['OPENWEATHERMAP_API_KEY']
    return render_template('/challenges/challenge.html', challenge=challenge,
     map_options = map_options, show_map = True, show_planning = True, landmarks=challenge.landmarks,
     num_photos_displayed=4)



@bp.route('/<int:challenge_id>/edit', methods=['GET', 'POST'])
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

@bp.route('/<int:challenge_id>/delete', methods=['POST'])
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

