"""Seed database with sample data."""

from app import db
from models import User, Admin, Activity, Challenge, Landmark, Gear, UserFriends, ChallengeLandmark, ActivityComment, ActivityGear, ChallengeGear, ActivityImages


db.drop_all()
db.create_all()



users = [User(first_name='Brian', last_name='Burrows', 
password='adminPassword132!@#', location='Colorado Springs', email='brianjburrow@gmail.com')]


for user in users:
    User.sign_up(user.email, user.first_name, user.last_name, user.password, user.location)

admin = [Admin(user_id = 1)]

db.session.add_all(admin)
db.session.commit

challenges = [Challenge(name='None', description='No challenge', created_by = 1),
Challenge(name = 'All arches', description='This challenge visits several iconic formations within Arches National Park', created_by=1),
Challenge(name = 'Landscape Arch', description='A direct hike to Landscape Arch in Arches National Park', created_by=1),
Challenge(name = 'Double O Arch', description='A direct hike to Double O Arch in Arches National Park', created_by=1),
Challenge(name = 'Balanced Rock', description='A direct hike to Balanced Rock in Arches National Park', created_by=1),
Challenge(name = "Delicate Arch", description='A direct hike to Delicate Arch in Arches National Park', created_by=1),
Challenge(name="Devil's Bridge", description="An incredible natural bridge in Sedona, AZ.", created_by=1)]

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
ChallengeLandmark(challenge_id = 2, landmark_id = 4),
ChallengeLandmark(challenge_id = 3, landmark_id = 2),
ChallengeLandmark(challenge_id = 4, landmark_id = 3),
ChallengeLandmark(challenge_id = 5, landmark_id = 4),
ChallengeLandmark(challenge_id = 6, landmark_id = 1),
ChallengeLandmark(challenge_id=7, landmark_id = 5)]

db.session.add_all(challenges_landmarks)
db.session.commit()

gpx = "./gpx_files/test.gpx"
Activities = [Activity(name='ARCHES!', user_id=1,challenge_id=1,gps_file=gpx)]

db.session.add_all(Activities)
db.session.commit()

for activity in Activities:
    activity.was_successful = Activity.validate_activity(activity)

db.session.add_all(Activities)
db.session.commit()

gear = [Gear(name='Ice axe', description='An axe for self arrests in snowy conditions', store_url="https://www.rei.com/c/ice-axes"),
Gear(name='Technical ice axe', description='An axe for climbing ice cliffs', store_url="https://www.rei.com/c/ice-axes?ir=category%3Aice-axes&r=c%3Bbest-use%3AIce+Climbing"),
Gear(name='Climbing rope', description='Equipment for crossing rivers and climbing rock', store_url="https://www.rei.com/c/climbing-ropes"),
Gear(name='Crampons', description='Footware for walking/climbing on icy terrain', store_url="https://www.rei.com/c/crampons"),
Gear(name='Traction', description='Footware for walking/climbing on icy terrain', store_url="https://www.rei.com/c/winter-traction-devices"),
Gear(name='Climbing rack', description='A full rack for trad climbing', store_url="https://www.rei.com/c/climbing-protection"),
Gear(name='Whitewater kayak', description='A boat specific to technical whitewater.',store_url="https://www.rei.com/c/kayaks"),
Gear(name='Climbing Harness', description='Equipment for belaying climbers safely.',store_url="https://www.rei.com/c/climbing-harnesses"),
Gear(name='Climbing Protection', description='Equipment for securing ropes to rocks and harnesses.',store_url="https://www.rei.com/c/climbing-hardware"),
Gear(name='Bouldering Pads', description='Large pads to protect climbers from short falls while bouldering.',store_url="https://www.rei.com/c/bouldering-crash-pads"),
Gear(name='Climbing Essentials', description='The basics for keeping hands and feet attached to the wall.',store_url="https://www.rei.com/c/climbing-essentials"),
Gear(name='Webbing and Cords', description='Helpful equiment for climbing and backpacking.',store_url="https://www.rei.com/c/webbing-and-cords"),
Gear(name='Ice Protection', description='Helpful equiment for climbing ice.', store_url="https://www.rei.com/c/snow-and-ice-protection"),
Gear(name='Climbing Helmet', description='A hard shell to protect your noggin.',store_url="https://www.rei.com/c/climbing-helmets"),
Gear(name='Mountain Bike', description='Two wheels and whatever level of suspension makes you comfortable to ride rad terrain.',store_url="https://www.rei.com/c/mountain-bikes"),
Gear(name='Road Bike', description='Stiff, aerodynamic, elegant, and fast.  Will get you from point to point with a smile on your face and a burn in your legs.',store_url="https://www.rei.com/c/road-bikes"),
Gear(name='Gravel Bike', description='Two wheels with wide tires to smoothly ride over varied terrain.',store_url="https://www.rei.com/c/road-bikes"),
Gear(name='Bike Helmet', description='A hard shell to protect your noggin.',store_url="https://www.rei.com/c/bike-helmets"),
Gear(name='Bike Storage', description='Mountable containers to store your belongings.',store_url="https://www.rei.com/c/bike-packs-bags-trailers"),
Gear(name='Bike Computer', description='A small, mountable computer for tracking activities and navigation on bike rides.',store_url="https://www.rei.com/c/bike-computers"),
Gear(name='Bike Tools', description='Various lightweight tools for bike repairs on the road.',store_url="https://www.rei.com/c/bike-tools-and-maintenance")
]

db.session.add_all(gear)
db.session.commit()


# the object name in the aws bucket
filenames_set = [['128_1_17f50279-0b71-4e22-9a4e-529c055f1b9d.jpg',
'320_1_17f50279-0b71-4e22-9a4e-529c055f1b9d.jpg',
'500_1_17f50279-0b71-4e22-9a4e-529c055f1b9d.jpg'
],
['128_1_7b3bdc10-a05c-4a74-8a95-77b971eed775.jpg',
'320_1_7b3bdc10-a05c-4a74-8a95-77b971eed775.jpg',
'500_1_7b3bdc10-a05c-4a74-8a95-77b971eed775.jpg'
],
['128_1_7b585eab-8933-4323-9ad6-a7f6fd621067.jpg',
'320_1_7b585eab-8933-4323-9ad6-a7f6fd621067.jpg',
'500_1_7b585eab-8933-4323-9ad6-a7f6fd621067.jpg'],
['128_1_7cfe5bc4-3e8c-469d-8429-4cd5b15e3a86.jpg',
'320_1_7cfe5bc4-3e8c-469d-8429-4cd5b15e3a86.jpg',
'500_1_7cfe5bc4-3e8c-469d-8429-4cd5b15e3a86.jpg']
]



for idx, activity in enumerate(Activities):
    for filenames in filenames_set:
        act_img = ActivityImages.create_activity_image_from_url(
            activity.id, 
            activity.user.id, 
            filenames
            )
        db.session.add(act_img)
        db.session.commit()

