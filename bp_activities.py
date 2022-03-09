##############################################################################
# Activity pages (some require login)

from flask import Blueprint, render_template, request, flash, redirect, g
from app import db
from models import Activity, Gear
from forms import NewActivityForm, NewCommentForm

from  helpers import validate_signed_in
bp = Blueprint('activities', __name__, url_prefix='/activities')

def adjust_map_options_boundaries(map_options, BUFFER_SIZE = 0.01):
    '''Allows us to add a buffer to the map, so that the activity doesn't touch the map borders'''
    map_options["longitude_min"] -= BUFFER_SIZE
    map_options["latitude_min"]  -= BUFFER_SIZE
    map_options["longitude_max"] += BUFFER_SIZE
    map_options["latitude_max"]  += BUFFER_SIZE
    return map_options

@bp.route('/new', methods=['GET', "POST"])
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

@bp.route('/<int:activity_id>', methods=['GET'])
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


@bp.route('/<int:activity_id>/delete', methods=['POST'])
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