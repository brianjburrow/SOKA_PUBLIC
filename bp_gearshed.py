from flask import render_template, flash, redirect, g, Blueprint
from app import db
from models import UserGear
from forms import NewUserGearForm
from helpers import validate_signed_in, validate_correct_user

bp = Blueprint('gearshed', __name__, url_prefix='/gearshed')

@bp.route('/')
def show_user_gear():
    if not validate_signed_in("You must be logged in to view your Gear Shed!"):
        return redirect("/login")
    gear = UserGear.query.all()
    return render_template("/gear/gear_shed.html", user = g.user, gear = gear, num_photos_displayed=4, allow_user_gear_upload = True)

@bp.route('/<int:gear_id>/delete', methods=['POST'])
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

@bp.route('/new', methods=['GET', 'POST'])
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

    