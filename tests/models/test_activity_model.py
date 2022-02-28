"""Activity model tests."""

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


class ActivityModelTestCase(TestCase):
    """A model for performing unit tests on the Activity model, database connection, and associated functionality"""

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
        created_by = self.testuser.id)
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

    def test_activity_model(self):
        """Does basic model work?"""
        # add an activity to the database
        with self.client as c:
            user_id = self.testuser.id
            name =  'test name'
            challenge_id = self.challenge.id
            style = "Biking"
            resp = c.get('/uploads/test.gpx')

            gps_data = resp.data

            notes = "This is a test activity."
            gear = [item.id for item in self.gear]
            pics = []

            activity = Activity.add_activity(user_id,name, challenge_id,style, gps_data, notes, gear, pics, directory=GPX_FOLDER)
            self.assertIsNotNone(activity.id)
            # test that the activity name was uppercased, and data uploaded correctly
            self.assertEqual(activity.name, 'Test name')
            self.assertEqual(activity.challenge_id, challenge_id)
            self.assertEqual(activity.style, 'Biking')

            # test that the model added ActivityImages and ActivityGear correctly
            self.assertEqual(len(ActivityImages.query.all()), 0)
            self.assertEqual(len(ActivityGear.query.all()), 2)
            # test that the model validation was correct
            self.assertTrue(activity.was_successful)

            ## validate an activity who's landmark we didn't visit
            # add a new landmark to the challenge
            cl = ChallengeLandmark(challenge_id = self.challenge.id, landmark_id = self.wrong_landmark.id)
            db.session.add(cl)
            db.session.commit()
            # Make an activity who's landmark won't be on the GPS track
            unsuccessful_activity = Activity.add_activity(user_id,name, challenge_id, style, gps_data, notes, gear, pics, directory=GPX_FOLDER)
            self.assertFalse(unsuccessful_activity.was_successful)
            pass
