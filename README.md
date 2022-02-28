# SOKA

https://sokaadventures.herokuapp.com/

## About

SOKA is a social media site for orienteers, explorers, and adventurers that provides challenging missions for any mode of transportation. Each challenge requires you to plan, prepare, and share activities that will get you outdoors and enjoying new destinations.

Each challenge consists of a set of landmarks, GPS coordinates, and a set of gear recommendations. It’s up to you to determine your route, mode of transportation, equipment, and time to hit the trails.

SOKA provides you with tools to plan your activity, check local weather forecasts, and gear track of gear usage. Our algorithms will check your activity against the challenge requirements, and our servers will provide a platform for you to share your activities with your friends and families.


## How to use.

#### Official Challenges, Landmarks, and Gear

Simply register a new account or log into an existing account to gain access to available challenges, view available landmarks.  The challenges tab will provide you with a summary of available challenges.  You can view official challenges created by SOKA as well as challenges created by athletes that you follow.  

Clicking on an individual challenge will allow you to view more detailed information about a particular challenge.  This will include a map that displays the location of the landmarks that you will attempt to visit (provided by Mapbox and OpenStreetMap).  It will also include some functionality to plan your activity.  First is some information about the current weather at each of the landmarks for planning immediate trips.  

![alt text](https://github.com/brianjburrow/SOKA/blob/main/readme_images/current_weather.png)

Second, a two day weather forecast is displayed for each landmark, which can be used to plan your route, determine the order of landmarks to visit for the best experience, and select appropriate gear for the day.  

![alt text](https://github.com/brianjburrow/SOKA/blob/main/readme_images/weather_forecast.png)

Last is a gear checklist, this feature will display all gear that you have uploaded to SOKA.  You can checkoff each item as you pack them, and it will keep track of how much weight you will be carrying in total, in your pack, and on your person.  Of course, you'll need some gear to track, which can be added in your gearshed.  You will see a message similar to:

![alt text](https://github.com/brianjburrow/SOKA/blob/main/readme_images/plan_activity.png)

Navigating to the My Gear tab will display a list of gear next to your user information.  Of course, this will be empty the first time you visit the site.  Your user card should have a button to upload your gear.  

gear_page_empty.png
![alt text](https://github.com/brianjburrow/SOKA/blob/main/readme_images/gear_page_empty.png)

Click on this to add gear to your gearshed.  Make sure to weigh your gear in your preferred units (e.g., pounds, grams, etc.).  Whatever unit you choose, be sure to be consistent so that pack weights can be added correctly.  

![alt text](https://github.com/brianjburrow/SOKA/blob/main/readme_images/gear_upload.png)

Once you have added all of the items needed for your trip, your gearshed should look like this.

gear_page_final.png
![alt text](https://github.com/brianjburrow/SOKA/blob/main/readme_images/gear_page_final.png)

Then you can return to the challenge of your choosing, and pack accordingly.  Check the box whenever you've packed an item, and determine where you will be carrying each item. 

packing.png
![alt text](https://github.com/brianjburrow/SOKA/blob/main/readme_images/packing.png)

If you're missing recommended gear for your activity, and it seems necessary for the route that you've picked, then clicking on the recommended gear name will take you to our affiliate link to browse options available to meet that gear requirement.  Or visit Explore Gear for a more comprehensive list.


![alt text](https://github.com/brianjburrow/SOKA/blob/main/readme_images/explore_gear.png)

#### Creating Challenges and Landmarks

Our official challenges try to explore well known landmarks in each state, province, and country.  Local favorites are omitted intentionally, for locals to keep their favorite trails quiet, while still sharing with close friends.  Soka provides functionality for users to create private landmarks and challenges, which are only viewable by followers.  Each landmark must consist of a set of latitude, longitude values.  These values must be input in the following form:

![alt text](https://github.com/brianjburrow/SOKA/blob/main/readme_images/landmark_upload.png)

You can also create challenges using all landmarks available to you.  The list of available landmarks is limited to official landmarks (added by Soka), landmarks added by users that you follow, and landmarks that you have created yourself.  

![alt text](https://github.com/brianjburrow/SOKA/blob/main/readme_images/create_challenge.png)

#### Uploading Challenge Attempts

You can upload activities that do not attempt challenges, and you can provide as much or as little information as you desire about your activity.  The upload form is:

![alt text](https://github.com/brianjburrow/SOKA/blob/main/readme_images/upload_activity.png)

If desired, select a challenge from the pull down menu.  Only one challenge may be attempted per upload.  Select any gear used from the menu, holding command (mac) to select multiple entries.  Select a style to let people know if you biked, hiked, ran, or drove between landmarks.  Additional notes can be added to let your followers know what to expect if they attempt the same route (river crossings, 5.6+ climbing, etc.).  Four images can be uploaded per activity, and a .GPX file can be uploaded of your activity.  .FIT files are not currently supported, but if you upload your activity to Strava or TrailForks (we have no affiliation to either), you can then download your .GPX file to upload on Soka as well.

Once uploaded, your activity will be available on your profile page as well as the feed of any user who follows you.

## Enabling Technologies

We would like to thank all of the open source projects that made this work possible.

### API for data gathering and visualization

###### Weather data

https://openweathermap.org/api/one-call-api

###### Map display

https://docs.mapbox.com/api/overview/

### Numerical Computing and File Parsing

https://readthedocs.org/projects/gpxpy/

### Web Framework's, Databases, and Servers

https://flask-wtf.readthedocs.io/en/1.0.x/

https://flask.palletsprojects.com/en/2.0.x/

https://flask-sqlalchemy.palletsprojects.com/en/2.x/

https://getbootstrap.com/docs/5.0/getting-started/introduction/

https://axios-http.com/docs/intro

https://dashboard.heroku.com/login

https://boto3.amazonaws.com/v1/documentation/api/latest/index.html

aws.amazon.com



