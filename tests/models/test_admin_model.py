"""Admin model tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest <name-of-python-file>

import os
from unittest import TestCase

from models import db, Admin, User
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


class AdminModelTestCase(TestCase):
    """docstring."""

    def setUp(self):
        """Create test client, add sample data."""

        Admin.query.delete()
        User.query.delete()
        # make a user
        self.testuser = User.sign_up('testemail@email.com',
        "test_first_name", 'test_last_name',
        'testpassword', 'testlocation')

    def test_admin_model(self):
        """Does basic model work?"""
        # add an activity to the database
        admin = Admin(user_id = self.testuser.id)
        db.session.add(admin)
        db.session.commit()
        # make sure the landmark was uploaded to the database

        self.assertTrue(self.testuser.is_admin())
        self.assertEqual(self.testuser.id,admin.user_id)
        self.assertEqual(self.testuser, admin.user)
        pass