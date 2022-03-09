##############################################################################
# Gear pages (some require login), will add administrator template at some point
from flask import (
    Blueprint, flash, g, redirect, render_template, flash
)

from app import db
from models import Gear
from forms import  NewGearForm,  NewUserForm


bp = Blueprint('gear', __name__, url_prefix='/gear')

@bp.route('/', methods=['GET'])
def show_gear():
    '''Show a list of gear to the user'''
    gear = Gear.query.all()
    user = g.user if g.user else None
    form = NewUserForm() if not g.user else None
    return render_template("/gear/gear.html", user = user, gear = gear, num_photos_displayed=4, form = form, allow_user_gear_upload = True)

@bp.route('/new', methods=['GET', 'POST'])
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

@bp.route('/<int:gear_id>', methods=['GET'])
def handle_gear(gear_id):
    '''Show information for a particular piece of gear to the user'''
    gear = Gear.query.get_or_404(gear_id)
    return render_template("/gear/gear_item.html", gear = gear, num_photos_displayed=4)

@bp.route('/<int:gear_id>/edit', methods=['GET', 'POST'])
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



