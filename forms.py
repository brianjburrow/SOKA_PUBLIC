from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, FileField, TextField, SelectMultipleField, SubmitField, FieldList, FloatField, MultipleFileField
from wtforms.validators import Email, Length, InputRequired, NumberRange, URL
from flask_wtf.file import FileAllowed

class LoginForm(FlaskForm):
    email = StringField('Email', 
    validators=[InputRequired("Must provide an e-mail to login."),
    Email()])
    password = PasswordField("Password",
    validators=[InputRequired("Please provide your password to login."),
    Length(min = 5, max = 30, message="Password must be between 5 and 30 characters inclusive.")])

class NewActivityForm(FlaskForm):
    name = StringField("Activity Name", validators=[InputRequired("Must provide a name for the activity"),
    Length(min=1,max=200)])
    challenge = SelectField("Challenge", coerce=int, validators=[InputRequired("Must select a challenge")])
    gear = SelectMultipleField("Gear", coerce=int)
    style = StringField("Style")
    notes = TextAreaField("Notes")
    images = MultipleFileField("Upload Images", validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], "Files must be .jpg, jpeg, or .png"),
        Length(min=-1, max=4, message="Can upload between 1 and 4 images"),
    ], render_kw={'multiple': True})

    gps_file = FileField(".GPX file", validators=[FileAllowed(['gpx'])])

class NewGearForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired("Must provide a name"), Length(min=1,max=40,message="Name must be less than 40 characters.")])
    description = TextAreaField('Description', validators=[InputRequired("Must provide a description")])
    store_url = TextField('Store URL', validators=[URL(message="URL must be valid.")])

class NewUserGearForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired("Must provide a name"), Length(min=1,max=40,message="Name must be less than 40 characters.")])

    brand = StringField('Brand', validators=[InputRequired("Must provide the brand name."), Length(min=1, max=40, message="Brand name must be less than 40 characters.")])
    
    model = StringField('Model', validators=[InputRequired("Must provide the model name."), Length(min=1, max=60, message="Brand name must be less than 60 characters.")])
    weight = FloatField('Weight', validators=[InputRequired("Must provide a weight (-1 if unknown)")])
    time_used = FloatField("Hours Used", validators = [InputRequired("Must provide the number of hours used.")])

class NewLandmarkForm(FlaskForm):
    # setup validators
    coord_func = InputRequired("Must provide coordinates")
    leng_func = Length(min=7, max=20, message="Coordinates must be between 7 and 20 characters.")

    # setup fields
    name = StringField(validators=[InputRequired("Must provide a name"), Length(min=1, max=100, message="Name must be less than 100 characters")])
    latitude = StringField(validators=[coord_func, leng_func])
    longitude = StringField(validators=[coord_func, leng_func])
    img_url = TextField(validators=[URL(message="Must be a valid url")])

class NewChallengeForm(FlaskForm):
    name = StringField("Challenge Name", validators=[InputRequired("Must provide a name"),
    Length(min=1, max=50, message="Must provide a challenge name.")])
    description = TextAreaField('Description', validators=[InputRequired("Must provide a description")])
    gear = SelectMultipleField("Gear", coerce = int, validators=[InputRequired("Must provide a gear selection")])
    landmarks = SelectMultipleField("Landmarks", coerce=int, validators=[InputRequired("Must select at least one landmark")])

class NewUserForm(FlaskForm):
    name_check = InputRequired("Must provide a full name.")
    length_check = Length(min=1, max=50, message="First and last names must be less than 50 characters in length each")
    first_name = StringField('First Name', validators=[name_check, length_check])
    last_name = StringField('Last Name', validators=[name_check, length_check])
    location = StringField('Location', validators=[Length(min=1,max=100, message="Location name must be less than 100 characters in length.")])
    email = StringField('Email', validators=[InputRequired("Must provide a valid email address"), Email("Must provide a valid email address"),
    Length(min=1,  max=100, message="Email address must be less than 100 characters in length.")])
    password = PasswordField(validators=[InputRequired("Must provide a password"),
    Length(min = 5, max = 30, message="Password must be between 5 and 30 characters inclusive.")])
    confirm = PasswordField()

class EditUserForm(FlaskForm):
    name_check = InputRequired("Must provide a full name.")
    length_check = Length(min=1, max=50, message="First and last names must be less than 50 characters in length each")
    first_name = StringField('First Name', validators=[name_check, length_check])
    last_name = StringField('Last Name', validators=[name_check, length_check])
    location = StringField('Location', validators=[Length(min=1,max=100, message="Location name must be less than 100 characters in length.")])
    email = StringField('Email', validators=[InputRequired("Must provide a valid email address"), Email("Must provide a valid email address"),
    Length(min=1,  max=100, message="Email address must be less than 100 characters in length.")])
    password = PasswordField("Confirm Password")

class NewCommentForm(FlaskForm):
    comment_check = InputRequired("Must provide a comment to submit a comment.")
    length_check = Length(min = 1, max = 280, message="Message length should be less than 280 characters.")
    comment = TextAreaField("Comment", validators = [comment_check, length_check])
