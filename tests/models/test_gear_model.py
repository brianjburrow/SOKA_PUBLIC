"""Gear model tests."""

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
# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
db.drop_all()
db.create_all()


class GearModelTestCase(TestCase):
    """A class for performing unit tests on the Gear Model, connections to the database, and related functionality"""

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

        # create a challenge
        self.challenge = Challenge(name='Test Challenge', 
        description='this is a test',
        created_by =self.testuser.id)
        db.session.add(self.challenge)
        db.session.commit()

        # add some recommmended gear to the challenge
        cg = ChallengeGear(challenge_id = self.challenge.id,
        gear_id = self.gear[0].id)
        db.session.add(cg)
        db.session.commit()

        # add a landmark to the database
        self.landmark = Landmark.add_landmark("30.610927 N", "96.318101 W", "test landmark", TEST_IMAGE_URL, self.testuser.id)
        self.wrong_landmark = Landmark.add_landmark("31.610927 N", "96.318101 W", "test landmark", TEST_IMAGE_URL, self.testuser.id)

        # add the landmark to the challenge
        cl = ChallengeLandmark(challenge_id = self.challenge.id, landmark_id = self.landmark.id)
        db.session.add(cl)
        db.session.commit()
        self.client = app.test_client()

    def test_gear_model(self):
        """Does basic model work?"""
        # add an activity to the database
        name = 'test_gear'
        description = 'this is test gear'
        store_url = 'amazon.com'
        gear = Gear.create_gear(name, description, store_url)
        
        self.assertEqual(gear.name, 'Test_gear')
        self.assertEqual(gear.description, 'This is test gear')
        self.assertEqual(gear.store_url, store_url)

        repr = gear.__repr__()

        self.assertEqual(repr, f"Gear #{gear.id}: Test_gear has description 'This is test gear'")

