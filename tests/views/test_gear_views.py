"""Gear View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest <name-of-python-file>

import os, io
from unittest import TestCase

from models import db, User, Admin, Activity, Challenge, Landmark, Gear, ChallengeLandmark, ActivityGear, ChallengeGear, UserFriends, UserGear

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///SOKA-test"

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

# Now we can import app

from app import app, CURR_USER_KEY
app.config['SQLALCHEMY_ECHO'] = False
app.config['WTF_CSRF_ENABLED'] = False

db.drop_all()
db.create_all()


class GearViewTestCase(TestCase):
    """Test views for an activity, and associated functionality.
    
    This class will test views for non-logged in users, logged in users who do not own the activity, 
    logged in users who own the activity, and admin.

    """
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):

        """Create test client, add sample data."""
        self.client = app.test_client()
        db.drop_all()
        db.create_all()     

        seed_test_file()
        ## create a test user
        email = 'testemail@email.com'
        first_name = 'test'
        last_name = 'user'
        password = 'password'
        location = 'boston'
        User.sign_up(email, first_name, last_name, password, location) # no admin, no activities, nothing special about them

        self.testuser =User.query.filter(User.email=='testemail@email.com').first();

        self.admin = Admin.query.first().user; # get the user associated with the first admin

        pass
    def test_gear_routes(self):
        with self.client as c:
            ###################################
            # Test without any user logged in
            ###################################
            # Response should show the registration card
            resp = c.get('/gear')
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text = True)

            self.assertIn("<span class='col-12 text-center'>Register Today</span>",html)

            resp = c.get('/gear/new', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text = True)
            self.assertIn("You must be an administrator to create gear", html)

            data = {"name":"TestGear", "description":"testdesc", "store_url":"amazon.com"}
            resp = c.post('/gear/new', follow_redirects=True, data=data)
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text = True)
            self.assertIn("You must be an administrator to create gear", html)

            resp = c.get('/gearshed', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertIn("You must be logged in to view your Gear Shed!",html)

            resp = c.post('/gearshed/1/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertIn("You must be logged in to delete gear",html)

            resp = c.get('/gearshed/new', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertIn("You must be logged in to create gear for your Gear Shed.",html)

            resp = c.post('/gearshed/new', follow_redirects=True, data = {})
            html = resp.get_data(as_text=True)
            self.assertIn("You must be logged in to create gear for your Gear Shed.",html)


            

            ###################################
            # Change the session user to an Admin
            ###################################
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.admin.id

            resp = c.get('/gear')
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text = True)
            # user card should be displayed instead of the registration form
            self.assertNotIn("<span class='col-12 text-center'>Register Today</span>",html)

            resp = c.get('/gear/new', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text = True)
            self.assertNotIn("You must be an administrator to create gear", html)

            data = {"name":"TestGear", "description":"testdesc", "store_url":"amazon.com"}
            resp = c.post('/gear/new', follow_redirects=True, data=data)
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text = True)
            self.assertNotIn("You must be an administrator to create gear", html)


            ###################################
            # Change the session user to a user who isn't following anyone
            # and the user has not created any challenges
            ###################################
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/gear')
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text = True)
            # user card should be displayed instead of the registration form
            self.assertNotIn("<span class='col-12 text-center'>Register Today</span>",html)

            resp = c.get('/gear/new', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text = True)
            self.assertIn("You must be an administrator to create gear", html)

            resp = c.post('/gear/new', follow_redirects=True, data={})
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text = True)
            self.assertIn("You must be an administrator to create gear", html)

            resp = c.get('/gearshed', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertNotIn("You must be logged in to view your Gear Shed!",html)

            resp = c.get('/gearshed/new', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertNotIn("You must be logged in to create gear for your Gear Shed.",html)

            data = {"name":"test", "model":"test","brand":"test","weight":14,"time_used":0}
            resp = c.post('/gearshed/new', follow_redirects=True, data = data)
            html = resp.get_data(as_text=True)
            self.assertNotIn("You must be logged in to create gear for your Gear Shed.",html)

            gear = UserGear.query.first()
            resp = c.post(f'/gearshed/{gear.id}/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertNotIn("You must be logged in to delete gear",html)

            






def seed_test_file():
    """Seed database with sample data."""
    users = [User(first_name='Brian', last_name='Burrows', 
    password='daisy', location='Boston', email='brianjburrow@gmail.com'),
    User(first_name='Daisy', last_name='Burrows', 
    password='daisy', location='Boston', email="challenger@email.com"),
    User(first_name='Follows', last_name='Daisy', 
    password='daisy', location='Boston', email="follower@email.com")]


    for user in users:
        User.sign_up(user.email, user.first_name, user.last_name, user.password, user.location)

    admin = [Admin(user_id = 1)]

    db.session.add_all(admin)
    db.session.commit

    challenges = [Challenge(name='None', description='No challenge', created_by = 1),
    Challenge(name = 'All arches', description='challengeDesc', created_by=2),
    Challenge(name = 'Landscape Arch', description='challengeDesc', created_by=2),
    Challenge(name = 'Double O Arch', description='challengeDesc', created_by=2),
    Challenge(name = 'Balanced Rock', description='challengeDesc', created_by=2),
    Challenge(name = "Delicate Arch", description='challengeDesc', created_by=2),
    Challenge(name="Devil's Bridge", description="A hike up to Devil's Bridge in Sedona, AZ.  Planned paths exist, but other routes are possible.", created_by=1)]

    db.session.add_all(challenges)
    db.session.commit()

    utah_landmarks = [Landmark(name = "Delicate Arch",
        latitude="38.7436 N", 
    longitude="109.4993 W", 
    img_url = "https://images.squarespace-cdn.com/content/v1/5c507a04ec4eb7b4b061b1ef/1627049457145-3IMAM613VX7RIVCPHMDN/Delicate-Arch.jpg", created_by=1),
    Landmark(name = "Landscape Arch",
        latitude="38.7910 N", 
    longitude="109.6062 W", 
    img_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Landscape_Arch_Utah_%2850MP%29.jpg/1200px-Landscape_Arch_Utah_%2850MP%29.jpg", created_by=1),
    Landmark(name = "Double O Arch",
        latitude="38.7991 N", 
    longitude="109.6211 W", 
    img_url = "https://www.desertsolitude.com/wp-content/uploads/2018/03/double-o-sandstone-arch-national-park.jpg", created_by=1),
    Landmark(name = "Balanced Rock",
        latitude="38.7010 N", 
    longitude="109.5645 W", 
    img_url = "https://media.deseretdigital.com/file/563dfe1611?type=jpeg&quality=55&c=15&a=4379240d", created_by=1),
    Landmark(name="Devil's Bridge",
    latitude = "34.9028 N",
    longitude="111.8138 W",
    img_url="https://hiking-and-fishing.nyc3.cdn.digitaloceanspaces.com/2019/11/26224234/Devils-Bridge-Sedona-Arizona.png", created_by=1)
    ]
    db.session.add_all(utah_landmarks)
    db.session.commit()

    north_carolina_landmarks = [
        Landmark(name= "Chimney Rock", latitude = "35.4393 N", longitude = "82.2465 W",
        img_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/5/54/Chimney_Rock_State_Park-20080811.jpeg/1024px-Chimney_Rock_State_Park-20080811.jpeg",
        created_by=1)
    ]

    db.session.add_all(north_carolina_landmarks)
    db.session.commit()


    challenges_landmarks = [ChallengeLandmark(challenge_id = 2, landmark_id = 1),
    ChallengeLandmark(challenge_id = 2, landmark_id = 2),
    ChallengeLandmark(challenge_id = 2, landmark_id = 3),
    ChallengeLandmark(challenge_id = 2, landmark_id = 4)]

    db.session.add_all(challenges_landmarks)
    db.session.commit()

    gpx = "./gpx_files/test.gpx"
    Activities = [Activity(name='ARCHES!', user_id=1,challenge_id=1,gps_file=gpx),
    Activity(name='ARCHES!', user_id=2,challenge_id=2,gps_file=gpx),
    Activity(name='ARCHES!', user_id=2,challenge_id=3,gps_file=gpx),
    Activity(name='ARCHES!', user_id=2,challenge_id=1,gps_file=gpx)]

    db.session.add_all(Activities)
    db.session.commit()

    for activity in Activities:
        activity.was_successful = Activity.validate_activity(activity)

    db.session.add_all(Activities)
    db.session.commit()

    gear = [Gear(name='Ice axe', description='An axe for self arrests in snowy conditions', store_url="https://www.rei.com/c/ice-axes"),
    Gear(name='Technical ice axe', description='An axe for climbing ice cliffs', store_url="https://www.rei.com/c/ice-axes?ir=category%3Aice-axes&r=c%3Bbest-use%3AIce+Climbing")
    ]

    db.session.add_all(gear)
    db.session.commit()


    activity_gear = [ActivityGear(activity_id=1, gear_id=1),
    ActivityGear(activity_id=1, gear_id=2)]

    db.session.add_all(activity_gear)
    db.session.commit()


    challenge_gear = [ChallengeGear(challenge_id = 2, gear_id = 1),
    ChallengeGear(challenge_id = 2, gear_id = 2),
    ChallengeGear(challenge_id = 3, gear_id = 2),
    ChallengeGear(challenge_id = 3, gear_id = 1)]

    db.session.add_all(challenge_gear)
    db.session.commit()

    user_friends = [UserFriends(user_following_id = 3,user_being_followed_id = 2)]

    db.session.add_all(user_friends)
    db.session.commit()