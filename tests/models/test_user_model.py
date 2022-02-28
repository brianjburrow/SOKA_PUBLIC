"""User model tests."""

# run these tests like:
#
#   FLASK_ENV=production python -m unittest <name-of-python-file>

import os
from unittest import TestCase

from models import db, Activity, User, ActivityGear, ActivityImages, Gear, Challenge

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///SOKA-test"

TEST_IMAGE_URL = 'https://en.wikipedia.org/wiki/Standard_test_image#/media/File:SIPI_Jelly_Beans_4.1.07.tiff'
# Now we can import app

from app import app

GPX_FOLDER = 'test_gpx_files'
ALLOWED_EXTENSIONS = {'gpx'}
app.config['UPLOAD_FOLDER'] = GPX_FOLDER
app.config['TESTING'] = True
print("CONFIG", app.config['UPLOAD_FOLDER'])
# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
db.drop_all()
db.create_all()


class UserModelTestCase(TestCase):
    """Methods for testing the User model, database connection, and associated functionality"""

    def setUp(self):
        """Create test client, add sample data."""

        Activity.query.delete()  # change to Model.query.delete()
        User.query.delete()
        ActivityGear.query.delete()
        ActivityImages.query.delete()
        Gear.query.delete()
        Challenge.query.delete()


    def test_user_model(self):
        """Does basic model work?"""
        email = 'testemail@email.com'
        first_name = 'test'
        last_name = 'user'
        password = 'password'
        location = 'boston'
        user = User.sign_up(email, first_name, last_name, password, location)

        self.assertIsNotNone(user.id)
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertNotEqual(user.password, password)

        is_user = User.authenticate(email, password)
        self.assertEqual(user, is_user)

    