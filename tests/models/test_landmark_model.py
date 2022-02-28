"""Landmark model tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest <name-of-python-file>

import os
from unittest import TestCase

from models import db, Activity, User, ActivityGear, ActivityImages, Gear, Challenge, ChallengeGear, Landmark, ChallengeLandmark

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


class LandmarkModelTestCase(TestCase):
    """methods for testing the landmark model, database connection, and associated functionality"""

    def setUp(self):
        """Create test client, add sample data."""

        Activity.query.delete()  # change to Model.query.delete()
        User.query.delete()
        ActivityGear.query.delete()
        ActivityImages.query.delete()
        Gear.query.delete()
        Challenge.query.delete()

        # make a user
        self.testuser = User.sign_up('testemail@email.com',
        "test_first_name", 'test_last_name',
        'testpassword', 'testlocation')

    def test_landmark_model(self):
        """Does basic model work?"""
        # add an activity to the database
        landmark = Landmark.add_landmark("30.610927 N", "96.318101 W", "test landmark", TEST_IMAGE_URL, self.testuser.id)

        # make sure the landmark was uploaded to the database
        self.assertIsNotNone(landmark.id)
        self.assertEqual(landmark.name, 'Test landmark')
        self.assertEqual(landmark.img_url, TEST_IMAGE_URL)
        long, lat = landmark.get_gps_coordinates()
        self.assertEqual(lat, float("30.610927"))
        self.assertEqual(long, float("-96.318101"))

        self.assertEqual(landmark.get_latitude_int(), 30)
        self.assertEqual(landmark.get_longitude_int(), -96  )
        pass