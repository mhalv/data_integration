import oauth2 as oauth
import requests
import time
import os
import sys
import codecs
import csv
from collections import OrderedDict
from pprint import pprint
import pyodbc

khan_user_url = "http://www.khanacademy.org/api/v1/user"
khan_exercises_url = "http://www.khanacademy.org/api/v1/user/exercises"
khan_exercise_states_url = "http://www.khanacademy.org/api/v1/user/exercises/progress_changes"
khan_students_url = "http://www.khanacademy.org/api/v1/user/students"
khan_badges_url = "http://www.khanacademy.org/api/v1/badges"
khan_exercise_metadata_url = "http://www.khanacademy.org/api/v1/exercises"

#global lists to catch output
coach_students = []
stu_details = []
composite_badges = []
badge_detail = []
composite_exercises = []
exercise_states = []

#to access the Khan API you register a consumer key
#this is at the level of the 'application'/organization - unlike the oauth flow
#in create_oauth.py it is not unique per coach.
#more detail at https://github.com/Khan/khan-api/wiki/Khan-Academy-API-Authentication
#these are sourced from a local file (meaning we can stick this script in version control
#without exposing our key or secret).
CONSUMER_KEY = open("C:/data_robot/logistical/khan_consumer_key.txt", "r").read()
CONSUMER_SECRET = open("C:/data_robot/logistical/khan_consumer_secret.txt", "r").read()

# Define where to place data
DATA_DIR = "khan_data"  # relative dir called khan_data
OAUTH_DIR = "oauth_khan"  # relative dir called oauth_khan

#csv format
csv.register_dialect('ALM', delimiter=',', quoting=csv.QUOTE_ALL)

#handle printing of non-ascii characters
sys.stdout = codecs.getwriter("iso-8859-1")(sys.stdout, 'xmlcharrefreplace')

def generate_oauth_params(credentials):
    """Returns a dictionary of OAuth parameters, given a user's token."""
    params = {
        'oauth_version': "1.0",
        'oauth_nonce': oauth.generate_nonce(),
        'oauth_timestamp': int(time.time()),
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_consumer_key': CONSUMER_KEY,
        'oauth_token': credentials['TOKEN']
    }
    return params


def assemble_oauth_request(credentials, params, target_url):
    """Builds an oauth request with credentials, token, and appropriate parameters
    (nonce, signature, etc.)"""
    oauth_request = oauth.Request.from_consumer_and_token(
        consumer=credentials['CONSUMER'],
        token=credentials['TOKEN'],
        http_url=target_url,
        parameters=params,
        http_method='GET'
    )
    oauth_request.sign_request(
        oauth.SignatureMethod_HMAC_SHA1(),
        credentials['CONSUMER'],
        credentials['TOKEN']
    )
    return oauth_request


def cleanup_khan_response(string):
    """Cleans API literal response strings to proper Python syntax."""
    return string.replace("false", "False").replace("true", "True").replace("null", "'null'")


def slugify_user(string):
    """Performs text processing to get back a user slug."""
    # Remove @ for _ and . for _
    slug_string = string.replace("@", "_").replace(".", "_")
    # Some users have http://nouserid.khanacademy.org/7e18f631070c1e260275ff3ea67ef24b
    # Remove http://, replace / with _
    slug_string = slug_string.replace("http://", "").replace("/", "_")
    # Return slugified string
    return slug_string


def get_badges():
    """Hits the main Khan badge url, processes to a dict, and writes to .csv file."""
    print "\tA.\tRetrieving a list of current badges from %s" % khan_badges_url
    parsed_badge_list = requests.get(khan_badges_url).json()
    parsed_badge_result = process_badge_metadata_list(parsed_badge_list)

    #write to file in top level data directory
    with open("%s/badge_metadata.csv" % DATA_DIR, 'wb') as f:
        w = csv.DictWriter(f, parsed_badge_result[0].keys(), dialect='ALM')
        w.writeheader()
        for i in parsed_badge_result:
            w.writerow(i)
        f.close()
    print "\tB.\tWrote all badges to %s/badge_metadata.csv" % DATA_DIR


def get_exercises():
    """Hits the main exercises url, processes a list of dicts, and writes to csv"""
    print "\tC.\tRetrieving a list of current exercises from %s" % khan_exercise_metadata_url
    parsed_exer_list = requests.get(khan_exercise_metadata_url).json()
    parsed_exer_result = process_exer_metadata(parsed_exer_list)

    #write to csv
    with open("%s/exer_metadata.csv" % DATA_DIR, 'wb') as f:
        w = csv.DictWriter(f, parsed_exer_result[0].keys(), dialect='ALM')
        w.writeheader()
        for i in parsed_exer_result:
            w.writerow(i)
        f.close()
    print "\tD.\tWrote all badges to %s/exer_metadata.csv" % DATA_DIR

def process_exer_metadata(exer_list):
    """preps /api/v1/exercises for db"""
    clean_exer_list = []
    for exer in exer_list:
        #convert to ascii string
        exer = dict([(unicode(k).encode("utf-8"), unicode(v).encode("utf-8")) for k, v in exer.items()])
        #just desired fields
        inner_dict = {
            'author_name': exer['author_name']
           ,'creation_date': exer['creation_date']
           ,'deleted': exer['deleted']
           ,'description': exer['description']
           ,'global_id': exer['global_id']
           ,'id': exer['id']
           ,'image_url': exer['image_url']
           ,'is_quiz': exer['is_quiz']
           ,'ka_url': exer['ka_url']
           ,'kind': exer['kind']
           ,'name': exer['name']
           ,'pretty_display_name': exer['pretty_display_name']
           ,'summative': exer['summative']
           ,'title': exer['title']
           ,'tracking_document_url': exer['tracking_document_url']
           ,'tutorial_only': exer['tutorial_only']
           ,'v_position': exer['v_position']
        }
        #wtf, some dictionaries are missing keys?  sigh.
        if 'do_not_publish' in exer:
            inner_dict['do_not_publish'] = exer['do_not_publish']
        else:
            inner_dict['do_not_publish'] = None

        clean_exer_list.append(inner_dict)

    return clean_exer_list


def process_badge_metadata_list(badge_list):
    """Drops un-needed fields and cleans up some nested elements in badge API endpoint"""
    for badge in badge_list:
        if 'can_become_goal' in badge:
            del badge['can_become_goal']
        if 'objectives' in badge:
            del badge['objectives']
        if 'is_owned' in badge:
            del badge['is_owned']
        if 'relative_url' in badge:
            del badge['relative_url']
        if 'user_badges' in badge:
            del badge['user_badges']
            # From the icon key create separate keys with its contents
        badge['icon_small'] = badge['icons']['small']
        badge['icon_compact'] = badge['icons']['compact']
        badge['icon_large'] = badge['icons']['large']
        # And after adding separate keys, remove the large 'icons' content
        del badge['icons']
    return badge_list


def assemble_coach_credentials(coach):
    """Returns a dict with key OAuth data (that was generated by the one-time create_oauth.py script)"""
    coach_tokens = __import__("%s.%s.tokens" % (OAUTH_DIR, slugify_user(coach)), fromlist=["tokens"])
    credentials = {
        "OAUTH_TOKEN": coach_tokens.FINAL_OAUTH_TOKEN,
        "OAUTH_TOKEN_SECRET": coach_tokens.FINAL_OAUTH_TOKEN_SECRET,
        "CONSUMER": oauth.Consumer(key=CONSUMER_KEY, secret=CONSUMER_SECRET),
        "TOKEN": oauth.Token(key=coach_tokens.FINAL_OAUTH_TOKEN, secret=coach_tokens.FINAL_OAUTH_TOKEN_SECRET)
    }
    return credentials


def one_step_oauth_request(coach, target_url):
    """Takes a coach and a target url, returns Khan API response in JSON"""
    #first get credentials
    credentials = assemble_coach_credentials(coach)
    #then build parameters
    params = generate_oauth_params(credentials)
    #put it all together with all the oauth requirements
    api_req = assemble_oauth_request(credentials, params, target_url)
    return api_req


def data_to_csv(target_dir, data_to_write, desired_name):
    """Convenience function to write a dict to CSV with appropriate parameters."""
    #generate directory if doesn't exist
    global d
    if len(data_to_write) == 0:
        return None
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    if type(data_to_write) == dict:
        #order dict by keys
        d = OrderedDict(sorted(data_to_write.items()))
        keys = d.keys()
    if type(data_to_write) == list:
        d = data_to_write
        keys = data_to_write[0].keys()
    with open("%s/%s.csv" % (target_dir, desired_name), 'wb') as f:
        dw = csv.DictWriter(f, keys, dialect='ALM')
        dw.writeheader()
        if type(data_to_write) == dict:
            dw.writerow(d)
        if type(data_to_write) == list:
            dw.writerows(d)
    f.close()


def get_students(coach):
    """Takes a coach; returns a list of students"""
    list_of_students = []
    api_req = one_step_oauth_request(coach, khan_students_url)
    #hand that over to beautiful, beautiful requests and return the json
    r = requests.get(api_req.to_url())
    if r.status_code == requests.codes.ok:
        parsed_resp = r.json()
        #iterate over response, extract emails, and append to list
        for i in parsed_resp:
            list_of_students.append(i['user_id'])
    else:
        print "bad response: " + str(r.status_code)
    return list_of_students


def get_student_details(coach_email, list_of_students, skip_list):
    """Gets relevant stu fields from coach/students API endpoint, appends to stu_details"""
    for student in list_of_students:
        #add list to coach_students list
        coach_students.append({'coach': coach_email, 'student': str(student)})
        #don't call student results twice if they are coached by 2x teachers
        if student in skip_list:
            print '\t\tSkipping %s who has already been evaluated' % student.decode("utf-8")
            continue
        #build request
        stu_url = '%s?userId=%s' % (khan_user_url, student)
        api_req = one_step_oauth_request(coach_email, stu_url)
        r = requests.get(api_req.to_url())
        #if response is valid, build a dict of key fields
        if r.status_code == requests.codes.ok:
            resp_dict = r.json()
            #convert keys to string from unicode
            resp_dict = dict([(str(k), v) for k, v in resp_dict.items()])
            print '\t\t%s (%s points)' % (resp_dict['nickname'], resp_dict['points'])
            #build an inner dict with desired fields
            inner_dict = {
                #collapse json to string
                'student': str(student),
                'all_proficient_exercises': ', '.join(map(str, resp_dict['all_proficient_exercises'])),
                #badge['icon_small'] = badge['icons']['small']
                'badge_lev0': resp_dict['badge_counts'][u'0'],
                'badge_lev1': resp_dict['badge_counts'][u'1'],
                'badge_lev2': resp_dict['badge_counts'][u'2'],
                'badge_lev3': resp_dict['badge_counts'][u'3'],
                'badge_lev4': resp_dict['badge_counts'][u'4'],
                'badge_lev5': resp_dict['badge_counts'][u'5'],
                'coaches': ', '.join(map(str, resp_dict['coaches'])),
                'first_visit': str(resp_dict['first_visit']),
                'joined': str(resp_dict['joined']),
                'registration_date': str(resp_dict['registration_date']),
                'nickname': resp_dict['nickname'].encode('ascii', 'ignore'),
                'points': resp_dict['points'],
                'proficient_exercises': ', '.join(map(str, resp_dict['proficient_exercises'])),
                'profile_root': str(resp_dict['profile_root']),
                'total_seconds_watched': resp_dict['total_seconds_watched'],
                'username': resp_dict['username'].encode('ascii', 'ignore')
            }
            #find @teamstudents email in list of all authorized emails and add to dictionary
            identity_email = [str(x) for x in resp_dict['auth_emails'] if x.endswith("@teamstudents.org")]
            inner_dict['identity_email'] = ', '.join(map(str, identity_email))
            #store data - append to global list
            stu_details.append(inner_dict)
            #write file to directory (not necessary; can eliminate)
            data_to_csv(
                target_dir="%s/%s/%s" % (DATA_DIR, slugify_user(coach_email), slugify_user(student)),
                data_to_write=inner_dict,
                desired_name='details'
            )
        else:
            print "bad response: " + str(r.status_code)


def get_student_badges(coach_email, list_of_students, skip_list):
    """Gets earned status and count for every student/badge, adds dict to global list."""
    counter = 0
    for student in list_of_students:
        print '\t\t%s' % student.decode("utf-8")
        #don't call student results twice if they are coached by 2x teachers
        if student in skip_list:
            print '\t\t\tSkipping %s who has already been evaluated' % student.decode("utf-8")
            continue
        stu_badge_url = '%s?userId=%s' % (khan_badges_url, student)
        api_req = one_step_oauth_request(coach_email, stu_badge_url)
        r = requests.get(api_req.to_url())
        if r.status_code == requests.codes.ok:
            #returns a list of badges
            badge_list = r.json()
            stu_list = []
            stu_list_detail = []
            for badge in badge_list:
                #make a dict of each badge
                dict([(str(k), v) for k, v in badge.items()])
                int_dict = {
                    'student': str(student),
                    'slug': str(badge['slug']),
                    'owned': badge['is_owned'],
                    'count': 0
                }
                #API only returns user badges if badge is owned
                if badge['is_owned']:
                    try:
                        int_dict['count'] = len(badge['user_badges'])
                        #iterate over user badges and store date & context
                        #(badges can be earned multiple times)
                        for detail in badge['user_badges']:
                            dict([(str(k), v) for k, v in detail.items()])
                            int_detail_dict = {
                                'student': str(student),
                                'slug': str(badge['slug']),
                                'date_earned': detail['date'],
                                'context': str(detail['target_context_name'])
                            }
                            stu_list_detail.append(int_detail_dict)
                    except Exception, e:
                        print e
                        int_dict['count'] = 1
                    #append to student dict
                    stu_list.append(int_dict)
            #out of loop now, attach student dict to composite list
            composite_badges.extend(stu_list)
            badge_detail.extend(stu_list_detail)
            #write data file to directory (not necessary for db upload; can eliminate)
            data_to_csv(
                target_dir="%s/%s/%s" % (DATA_DIR, slugify_user(coach_email), slugify_user(student)),
                data_to_write=stu_list,
                desired_name='composite_badges'
            )
            #write file to directory (not necessary for db upload; can eliminate)
            data_to_csv(
                target_dir="%s/%s/%s" % (DATA_DIR, slugify_user(coach_email), slugify_user(student)),
                data_to_write=stu_list_detail,
                desired_name='badge_details'
            )
        counter += 1
    return None


def get_composite_exercises(coach_email, list_of_students, skip_list):
    """Gets exercise status for every student/exercise, adds dict to global list."""
    for student in list_of_students:
        print '\t\t%s' % student.decode("utf-8")
        #don't call student results twice if they are coached by 2x teachers
        if student in skip_list:
            print '\t\t\tSkipping %s who has already been evaluated' % student.decode("utf-8")
            continue
        stu_exercise_url = '%s?userId=%s' % (khan_exercises_url, student)
        api_req = one_step_oauth_request(coach_email, stu_exercise_url)
        r = requests.get(api_req.to_url())
        if r.status_code == requests.codes.ok:
            stu_list = []
            resp = r.json()
            for ex in resp:
                ex_dict = dict([(str(k), v) for k, v in ex.items()])
                int_dict = {
                    'student': student,
                    'exercise': str(ex_dict['exercise']),
                    'maximum_exercise_progress_dt': ex_dict['maximum_exercise_progress_dt'],
                    'streak': ex_dict['streak'],
                    'progress': ex_dict['exercise_progress']['level'],
                    'practiced_date': ex_dict['practiced_date'],
                    'proficient_date': ex_dict['proficient_date'],
                    'total_done': ex_dict['total_done'],
                    'struggling': ex_dict['exercise_states']['struggling'],
                    'proficient': ex_dict['exercise_states']['proficient'],
                    'practiced': ex_dict['exercise_states']['practiced'],
                    'mastered': ex_dict['exercise_states']['mastered'],
                    'level': str(ex_dict['maximum_exercise_progress']['level']),
                    'total_correct': ex_dict['total_correct'],
                    'last_done': ex_dict['last_done'],
                    'longest_streak': ex_dict['longest_streak']
                }
                stu_list.append(int_dict)
            composite_exercises.extend(stu_list)
            #write data file to directory (not necessary)
            data_to_csv(
                target_dir="%s/%s/%s" % (DATA_DIR, slugify_user(coach_email), slugify_user(student)),
                data_to_write=stu_list,
                desired_name='composite_exercises'
            )


def get_exercise_states(coach_email, list_of_students, skip_list):
    """Gets exercise state changes for every student/exercise"""
    counter = 0
    for student in list_of_students:
        print '\t\t%s' % student.decode("utf-8")
        #don't call student results twice if they are coached by 2x teachers
        if student in skip_list:
            print 'Skipping %s who has already been evaluated' % student.decode("utf-8")
            continue
        stu_states_url = '%s?userId=%s' % (khan_exercise_states_url, student)
        api_req = one_step_oauth_request(coach_email, stu_states_url)
        r = requests.get(api_req.to_url())
        if r.status_code == requests.codes.ok:
            stu_list = []
            resp = r.json()
            for ex_st in resp:
                change_dict = dict([(str(k), v) for k, v in ex_st.items()])
                int_dict = {
                    'student': student,
                    'exercise': str(change_dict['exercise_name']),
                    'date': change_dict['date'],	
					'change_type': None,
                    #we COULD grab the 'from' here, as well.  right now we only need 'to'.					
                    'exercise_status': change_dict['to_progress']['level'],
                    'mastery_flag': change_dict['to_progress']['mastered']
                }
                stu_list.append(int_dict)
            exercise_states.extend(stu_list)
            #write data file to directory (not necessary)
            data_to_csv(
                target_dir="%s/%s/%s" % (DATA_DIR, slugify_user(coach_email), slugify_user(student)),
                data_to_write=stu_list,
                desired_name='exercise_states'
            )
            counter += 1


def collapse_dict(dictionary):
    """Some Khan responses have lists nested in the dictionary.  Collapse them into strings.
        ex: ['graphing_points','area_of_parallelograms','axis_of_symmetry']
        to 'graphing_points|area_of_parallelograms|axis_of_symmetry'"""
    for i, j in dictionary.iteritems():
        if type(j) == list:
            dictionary[i] = "|".join(j)
    return dictionary


def main():
    """Main loop that runs the data extract from the API.
    Initialized when file is opened."""
    print "1. COACHES:"
    # Coaches are declared inside coaches.txt (inside oauth_khan) if you want to add
    # a new coach add it to that file.
    print "\tA. Reading coaches.txt in dir %s...." % OAUTH_DIR
    coaches_file = open("%s/coaches.txt" % OAUTH_DIR, "r")
    coaches_list = coaches_file.readlines()
    verified_coaches = []
    print "\tB. Verifying OAuth setup for each coach in coaches.txt"
    for coach_line in coaches_list:
        # Strip carriage line
        coach = coach_line.strip()
        print "\t\tVerifying coach %s " % coach
        ##Check if this user even has an oauth token directory
        try:
            __import__("%s.%s.tokens" % (OAUTH_DIR, slugify_user(coach)), fromlist=["tokens"])
            verified_coaches.append(coach)
        except Exception, e:
            print """\t\tCouldn't find oauth tokens for %s!\n\t
              Run create_oauth.py for this user or remove her from coaches.txt.
              Error details: %s""" % (coach, e)
            continue
    coaches_file.close()
    print "\tC. Finished reading coaches.txt in dir %s." % OAUTH_DIR

    print
    print "2. GLOBAL DATA:"
    #all khan badges
    get_badges()

    get_exercises()

    print
    print "3. STUDENT DATA:"

    #don't do a kid twice
    already_fetched = []

    for coach in verified_coaches:
        print "\tA.\tPulling student list for coach %s " % coach
        roster = get_students(coach)
        print "\t\t%s coaches %s students" % (coach, len(roster))
        # now we have a list of students.
        #we want to hand that list of students to all of the API pulls
        print
        print "\tB.\tAssembling student details for %s's students" % coach
        get_student_details(coach, roster, already_fetched)

        print
        print "\tC.\tGetting student *badge* data for %s's students" % coach
        get_student_badges(coach, roster, already_fetched)

        print
        print "\tD.\tGetting student *exercise* totals for %s's students" % coach
        get_composite_exercises(coach, roster, already_fetched)
        print

        print
        print "\tE.\tGetting exercise state changes for %s's students" % coach
        get_exercise_states(coach, roster, already_fetched)

        #indicate that all the students have been evaluated (prevent dupes)
        already_fetched.extend(roster)

    print
    print "4. EXAMINE DATA:"

    print '\tA.\tcoach_students'
    pprint(coach_students[0:3])
    print
    print '\tB.\tcomposite_badges'
    pprint(composite_badges[0:3])
    print
    print '\tC.\tcomposite_exercises'
    pprint(composite_exercises[0:3])
    print
    print '\tD.\tbadge_detail'
    pprint(badge_detail[0:3])

    print
    print "5. WRITE COMBINED FILES"

    data_to_csv(
        target_dir="%s" % DATA_DIR,
        data_to_write=coach_students,
        desired_name='coach_students'
    )
    data_to_csv(
        target_dir="%s" % DATA_DIR,
        data_to_write=composite_badges,
        desired_name='composite_badges'
    )
    data_to_csv(
        target_dir="%s" % DATA_DIR,
        data_to_write=composite_exercises,
        desired_name='composite_exercises'
    )
    data_to_csv(
        target_dir="%s" % DATA_DIR,
        data_to_write=badge_detail,
        desired_name='badge_detail'
    )
    data_to_csv(
        target_dir="%s" % DATA_DIR,
        data_to_write=stu_details,
        desired_name='stu_detail'
    )
    data_to_csv(
        target_dir="%s" % DATA_DIR,
        data_to_write=exercise_states,
        desired_name='exercise_states'
    )

    print
    print "6. UPLOAD TO DB"

    #get credential
    f = open("C:/data_robot/logistical/nardo_secret.txt", "r")
    secret = f.read()

    #upload
    conn = pyodbc.connect(driver='{SQL Server}', server='WINSQL01\NARDO', database='DIY', uid='sa', pwd=secret)
    conn.execute("exec msdb.dbo.sp_start_job N'Khan | Load Data'")
    conn.commit()
    conn.close()

    #calcs (do as distinct session)
    conn = pyodbc.connect(driver='{SQL Server}', server='WINSQL01\NARDO', database='DIY', uid='sa', pwd=secret)
    conn.execute("exec msdb.dbo.sp_start_job N'Khan | Static Calc Refresh'")
    conn.commit()
    conn.close()

    print "Finished!!%"

if __name__ == '__main__':
    main()