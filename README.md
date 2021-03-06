# khan

### Python scripts to authenticate and pull down student progress data from the Khan API.

#### What's inside
If you don't know much about the Khan API, start with the web-based [API explorer] (http://api-explorer.khanacademy.org/) and the [wiki] (https://github.com/Khan/khan-api/wiki/Khan-Academy-API).


There are two main files here: `oauth_khan/create_oauth.py' and 'get_khan_data.py'.  They handle the two basic things that you want to do with the API: **get authenticated** and **get student data**.

'get_khan_data.py' is the workhorse file.  For all authenticated coaches (more on that below) it iterates over the students they coach and spits back data into .csv files for easy uploading to your database, or for importing into R/Tableau/Excel etc.  

it returns:

1. **badge_metadata**

   generic info about each badge that a student can earn on the Khan site.  This data is not unique to your students.
2. **composite_badges**

   a simple listing of badge, student, earned T/F, and count of times earned
3. **composite_exercises**

   top level stats about every exercise/objective, including mastered T/F, problems done, date proficient, etc.
4. **badge_detail**

   a listing of every badge earned, date, and (if applicable) why the badge was earned
5. **stu_detail**

   total points, seconds of video watched, badge counts, coach and username details
6. **coach_students**

   coach/student value pairs that tell you which coaches coach each student.  the script will only pull a student's data once (even if they have multiple coaches) but coach/students will help you rebuild rosters of who coaches whom.



'create_oauth.py' handles the configuration steps in the OAuth authentication flow process.  [OAuth] (http://developer.chrome.com/extensions/tut_oauth.html) is an authentication protocol that gives a secure way to grant access to certain data without exposing your password.  If you've ever clicked the 'Log in with Google/Facebook' button on a webpage, you've used OAuth.

OAuth flow is non-trivial and kind of a pain in the butt, to be honest.  Necessary and sensible to manage permissions, but definitely the biggest impediment to using the Khan API.  At least when we first tackled this project, the OAuth libraries in Python were [sort of a mess] (https://stackoverflow.com/questions/1666415/python-oauth-library) (highest voted answer - "I think Leah Culver's python-oauth (that you've already found) is the best starting point even though it's not complete..." ugh.) we tapped a consultant on ODesk to help with `create_oauth.py`.  If I was doing a ground floor rewrite [rauth] (https://github.com/litl/rauth) looks promising.

####Workflow
0. Read the Khan API
1. Register for an [API key] (https://www.khanacademy.org/api-apps/register).  This will give you a `CONSUMER_KEY`
and `CONSUMER SECRET', which you see referenced in our scripts.  Needless to say TEAM's keys are not in this repo - we [source them from text files] (https://github.com/TEAMSchools/data_integration/blob/master/khan/get_khan_data.py#L30) in our code.
2. Edit `oauth_khan/coaches.txt`.  Add any coaches for your organization.
3. Edit `create_oauth.py` with appropriate references to your consumer key and secret.  If you're not going to keep these scripts in version control, you can even just hard code the values in.
4. Run `oauth_khan/create_oauth.py`.  It will walk you through an interactive workflow.  Basically, it gives you a url to log in to Khan; after you grant access you copy and paste the response URL back into python, and `create_oauth` will store the tokens locally.  These steps only need to be done *once*/when you add a new coach.
5. Edit consumer key and consumer secret in 'get_khan_data.py'. 
6. Run `get_khan_data.py`.  The code is pretty descriptive about what it is doing, so if/when it chokes, you should have a good sense of what might be going on.  Sample output is below.
7.  In our script, we upload to our data warehouse in step 6.  Basically what we are doing there is calling a database side [load script] (https://github.com/TEAMSchools/data_integration/blob/master/khan/sql%20server%20config/sql%20server%20agent%20job.sql) that reads from the csv files and loads into database tables.  YMMV as to where you want to stick all this data, but I've included a bunch of `CREATE TABLE` scripts as well as the stored procedures which slurp up the text files.  This is  One Weird Trick in SQL Server that I don't think enough people are aware of so I will give a quick overview.  This code will read from a text file and load into a temp table with appropriate headers.
```
 --1. bulk load csv and SELECT INTO temp table
  SELECT sub.*
  INTO #import_badge_detail
  FROM
     (SELECT * 
     FROM OPENROWSET(
       'MSDASQL'
      ,'Driver={Microsoft Access Text Driver (*.txt, *.csv)};'
      ,'select * from C:\data_robot\khan\khan_school\khan_data\badge_detail.csv')
     ) sub;
```
From there you can do a clean MERGE/upsert on that data (preserves everything in the table and inserts new rows), or just truncate the table and push the new data in (sloppier but quick).  
8. If you've got everything running the way you want it, set up a scheduled task/cron job/whatever to do this automatically. 
Ours is literally just a little Windows batch file that opens up the Khan script.
```
cd C:\data_robot\khan\khan_school
khan_script.py
```

If you've got questions submit an issue here on git, or email me at amartin at teamschools dot org

#### Sample output
````
C:\Python27\python.exe Z:/khan/khan_school/get_khan_data_temp.py
1. COACHES:
	A. Reading coaches.txt in dir oauth_khan....
	B. Verifying OAuth setup for each coach in coaches.txt
		Verifying coach fake_teacher_1@gmail.com 
		Verifying coach fake_teacher_2@gmail.com 
	C. Finished reading coaches.txt in dir oauth_khan.

2. GLOBAL DATA:
	A.	Retrieving a list of current badges from http://www.khanacademy.org/api/v1/badges
	B.	Wrote all badges to khan_data/badge_metadata.csv

3. STUDENT DATA:
	A.	Pulling student list for coach fake_teacher_1@gmail.com
		fake_teacher_1@gmail.comcoaches 181 students

	B.	Assembling student details for fake_teacher_1@gmail.com's students
		Student, Fake (336245 points)

	C.	Getting student *badge* data for fake_teacher_1@gmail.com's students
		fake_student_1@teamstudents.org

	D.	Getting student *exercise* totals for fake_teacher_1@gmail.com's students
		fake_student_1@teamstudents.org

	A.	Pulling student list for coach fake_teacher_2@gmail.com 
		fake_teacher_2@gmail.com coaches 102 students

	B.	Assembling student details for mrdempsey.rise@gmail.com's students
		Skipping fake_student_1@teamstudents.org who has already been evaluated

	C.	Getting student *badge* data for mrdempsey.rise@gmail.com's students
		fake_student_1@teamstudents.org
		Skipping fake_student_1@teamstudents.org who has already been evaluated

	D.	Getting student *exercise* totals for mrdempsey.rise@gmail.com's students
		fake_student_1@teamstudents.org
		Skipping fake_student_1@teamstudents.org who has already been evaluated

4. EXAMINE DATA:
	A.	coach_students
[{'coach': 'fake_teacher_1@gmail.com',
  'student': 'fake_student_1@teamstudents.org'},
 {'coach': 'mrdempsey.rise@gmail.com', 'student': 'fake_student_1@teamstudents.org'},
 {'coach': 'travisdempsey@gmail.com', 'student': 'fake_student_1@teamstudents.org'}]

	B.	composite_badges
[{'count': 1,
  'owned': True,
  'slug': 'act-i-scene-i',
  'student': 'fake_student_1@teamstudents.org'},
 {'count': 3,
  'owned': True,
  'slug': 'awesome-streak',
  'student': 'fake_student_1@teamstudents.org'},
 {'count': 3,
  'owned': True,
  'slug': 'going-supersonic',
  'student': 'fake_student_1@teamstudents.org'}]

	C.	composite_exercises
[{'exercise': 'addition_1',
  'last_done': u'2014-02-06T17:20:48Z',
  'level': 'mastery3',
  'longest_streak': 35,
  'mastered': True,
  'maximum_exercise_progress_dt': u'2013-09-18T20:18:28Z',
  'practiced': True,
  'practiced_date': None,
  'proficient': True,
  'proficient_date': u'2013-06-25T13:40:23Z',
  'progress': 1.0,
  'streak': 10,
  'struggling': False,
  'student': u'fake_student_1@teamstudents.org',
  'total_corrrect': 82,
  'total_done': 88},
 {'exercise': 'cas-ecosystem-function',
  'last_done': None,
  'level': 'unstarted',
  'longest_streak': 0,
  'mastered': False,
  'maximum_exercise_progress_dt': None,
  'practiced': False,
  'practiced_date': None,
  'proficient': False,
  'proficient_date': 0,
  'progress': 0.0,
  'streak': 0,
  'struggling': False,
  'student': u'fake_student_1@teamstudents.org',
  'total_corrrect': 0,
  'total_done': 0},
 {'exercise': 'cas-ecosystem-services',
  'last_done': None,
  'level': 'unstarted',
  'longest_streak': 0,
  'mastered': False,
  'maximum_exercise_progress_dt': None,
  'practiced': False,
  'practiced_date': None,
  'proficient': False,
  'proficient_date': 0,
  'progress': 0.0,
  'streak': 0,
  'struggling': False,
  'student': u'fake_student_1@teamstudents.org',
  'total_corrrect': 0,
  'total_done': 0}]

	D.	badge_detail
[{'context': 'None',
  'date_earned': u'2013-07-28T19:30:31Z',
  'slug': 'act-i-scene-i',
  'student': 'fake_student_1@teamstudents.org'},
 {'context': 'Congruent segments',
  'date_earned': u'2013-11-10T03:30:10Z',
  'slug': 'awesome-streak',
  'student': 'fake_student_1@teamstudents.org'},
 {'context': 'Angle types',
  'date_earned': u'2013-07-09T14:38:36Z',
  'slug': 'awesome-streak',
  'student': 'fake_student_1@teamstudents.org'}]

5. WRITE COMBINED FILES

6. UPLOAD TO DB
Finished!!%

Process finished with exit code 0
````

# diy
Pulls down student activity from the diy.org website.
