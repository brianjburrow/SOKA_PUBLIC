"""Challenge model tests."""

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


class ChallengeModelTestCase(TestCase):
    """Methods for testing the Challenge Model, database connection, and associated functionality"""

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

        # add some gear
        self.gear = [Gear(name = 'axe', description = 'it is an axe', store_url = 'amazon.com'),
        Gear(name='shovel', description='it is a shovel', store_url='amazon.com')]
        db.session.add_all(self.gear)
        db.session.commit()

        # add a landmark to the database
        self.landmarks = [Landmark.add_landmark("30.610927 N", "96.318101 W", "test landmark", TEST_IMAGE_URL, self.testuser.id),
        Landmark.add_landmark("31.610927 N", "96.318101 W", "test landmark", TEST_IMAGE_URL, self.testuser.id)]

        self.client = app.test_client()

    def test_challenge_model(self):
        """Does basic model work?"""
        landmark_ids = [landmark.id for landmark in self.landmarks]

        gear_ids = [item.id for item in self.gear]
        name = "test challenge"
        description = "this is a test challenge."
        challenge = Challenge.create_challenge(name, description, gear_ids, landmark_ids, self.testuser.id)
        
        # ensure capitalization is correct
        self.assertEqual(challenge.name, 'Test challenge')
        self.assertEqual(challenge.description, "This is a test challenge.")
        
        # check to make sure secondary tables are filled correctly
        self.assertEqual(len(ChallengeGear.query.all()), 2)
        self.assertEqual(len(ChallengeLandmark.query.all()), 2)
        pass
