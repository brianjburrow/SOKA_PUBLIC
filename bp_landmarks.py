import os
from flask import Blueprint, render_template, flash, redirect, g
from app import db
from models import Activity,  Landmark
from forms import  NewLandmarkForm, NewUserForm

from helpers import validate_correct_user, validate_signed_in


bp = Blueprint('landmarks', __name__, url_prefix='/landmarks')

##############################################################################
# Landmark routes (some require login), will add administrator stuff at some point

@bp.route('', methods=['GET'])
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

@bp.route('/new', methods=['GET', "POST"])
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

@bp.route('/<int:landmark_id>', methods=['GET'])
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

@bp.route('/<int:landmark_id>/edit', methods=['GET','POST'])
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

@bp.route('/<int:landmark_id>/delete', methods=['POST'])
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