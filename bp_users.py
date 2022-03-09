from flask import Blueprint, render_template,  redirect, session, g
from models import User
from forms import  EditUserForm
from helpers import validate_correct_user, validate_signed_in
from app import db 
bp = Blueprint('users', __name__, url_prefix="/users")

@bp.route('', methods=['GET'])
def show_all_users():
    '''Display all users, and handle friends if the user is logged in'''
    if not validate_signed_in("You must be logged in to view users"):
        return redirect('/login')
    users = User.query.all()
    return render_template('/users/users.html',users = users, num_photos_displayed=2)

##############################################################################
# User pages (require log in)

@bp.route('/<int:user_id>', methods=['GET'])
def handle_individual_user(user_id):
    '''Show an individual user's page if accessed by a logged in user'''
    if not validate_signed_in("You must be logged in to view user page."):
        return redirect('/login')

    user = User.query.get_or_404(user_id)
    activities = [activity.setup_gpx_object() for activity in user.get_recent_activities()]

    return render_template('/users/user.html', user = user, activities=activities, 
     is_current_user = validate_correct_user('', user_id),
     num_photos_displayed=4)


@bp.route('/<int:user_id>/delete', methods=["POST"])
def delete_user(user_id):
    '''Delete a user (if logged in, and deleting own account)'''
    if not validate_signed_in("You must be logged in to delete your account"):
        return redirect("/login")
    
    if not validate_correct_user("You can only delete your own account.",user_id):
        return redirect(f'/users/{g.user.id}')
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    # remove user from the session
    session.clear()
    return redirect('/register')

@bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
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


@bp.route('/<int:user_id>/feed', methods=['GET'])
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
