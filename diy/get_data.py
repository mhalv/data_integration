import requests
import pyodbc
import json
import csv
import sys
#gahhhhh datetime
from dateutil import parser
from pprint import pprint

log_to = 'C:/data_robot/diy/data/run_log.txt'
#log_to = ('//winsql01/data/run_log.txt')
old_stdout = sys.stdout
log_file = open(log_to,"w")
sys.stdout = log_file

csv.register_dialect('ALM', delimiter=',', quoting=csv.QUOTE_ALL)

def csv_dict_writer(file_path, file_name, data):
    with open("%s/%s" % (file_path, file_name), 'wb') as f:
        w = csv.DictWriter(f, data[0].keys(), dialect='ALM')
        w.writeheader()
        for arow in data:
            w.writerow(arow)
    f.close()


def make_db_conn():
    f = open("C:/data_robot/logistical/nardo_secret.txt", "r")
    secret = f.read()
    conn = pyodbc.connect(driver='{SQL Server}', server='WINSQL01\NARDO', database='DIY', uid='sa', pwd=secret)
    return conn


def get_students():
    #make db connection
    conn = make_db_conn()
    #get diy nicknames
    cursor = conn.cursor()
    cursor.execute("""
       SELECT cust.diy_nickname
             ,s.first_name + ' ' + s.last_name AS stu_name
             ,s.grade_level
             ,sch.abbreviation AS school
       FROM KIPP_NJ..CUSTOM_STUDENTS cust
       JOIN KIPP_NJ..STUDENTS s
         ON cust.studentid = s.id
       JOIN KIPP_NJ..SCHOOLS sch
         ON s.schoolid = sch.school_number
       WHERE cust.diy_nickname IS NOT NULL""")
    columns = [column[0] for column in cursor.description]
    #return as list
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
        #close db connection
    conn.close()
    #for testing
    #return [{'diy_nickname': u'determinator'}]
    return results


def build_stu_url(resource, maker, property_='', parameters=''):
    base = 'https://brain.diy.org/'
    #only add parameters if value passed
    if parameters != '':
        parameters = '?' + parameters
    url = base + resource + '/' + maker + '/' + property_ + parameters
    return url


def get_badges(nickname):
    #build the url
    badge_url = build_stu_url('makers', nickname, 'achievements', 'limit=999')
    #print badge_url
    #request the data
    r = requests.get(badge_url)
    #make sure we're not hitting the rate limit
    if r.status_code == 429:
        print 'rate limit!'
    #diy returns unicode string; decode the json
    resp = json.loads(r.text)
    #narrow down the response to skills
    badges = resp['response']['skills']
    #initialize empty list - will insert dictionaries for each badge
    stu_badge_list = []
    #make a dict out of each item in the json; append to master_badges list
    for skill in badges:
        badge_dict = {}
        badge_dict['nickname'] = str(nickname)
        badge_dict['badge'] = str(skill['title'])
        badge_dict['earned'] = skill['stats']['earned']
        badge_dict['date_earned'] = skill['stats']['earned_at']
        stu_badge_list.append(badge_dict)

    return stu_badge_list


def get_projects(nickname):
    #build the url
    proj_url = build_stu_url('makers', nickname, 'projects', 'limit=999')
    #print proj_url
    #request the data
    r = requests.get(proj_url)
    #make sure we're not hitting the rate limit
    if r.status_code == 429:
        print 'rate limit!'
    #diy returns unicode string; decode the json
    resp = json.loads(r.text)
    #narrow down the response to skills
    projects = resp['response']

    #initialize empty list - will insert dictionaries for each badge
    stu_proj_list = []
    #make a dict out of each item in the json; append to master_badges list
    for proj in projects:
        proj_dict = {}
        proj_dict['title'] = str(proj['title'])
        proj_dict['url'] = 'http://diy.org/' + nickname + '/' + proj['id']
        #reduce to date
        parsed_date = parser.parse(proj['stamp'])
        format_date = parsed_date.strftime('%Y-%m-%d')
        proj_dict['created'] = format_date
        proj_dict['comments'] = proj['stats']['comments']
        proj_dict['featured'] = proj['stats']['featured']
        proj_dict['favorites'] = proj['stats']['favorites']
        proj_dict['forks'] = proj['stats']['forks']
        #test if achievement is null and return no, otherwise return title
        if proj['achievement'] is None:
            proj_dict['skill'] = 'No'
        else:
            proj_dict['skill'] = proj['achievement']['skill']['title']
        proj_dict['nickname'] = str(nickname)
        stu_proj_list.append(proj_dict)

    return stu_proj_list


#main loop that runs the sequence
def main():
    #get TEAM students who have a diy.org username
    print '1. GETTING STUDENTS'
    global all_students

    all_students = get_students()
    print '...' + str(len(all_students)) + ' student records'
    #pprint(all_students)

    #list to hold all the projects
    master_badges = []
    master_projects = []

    print
    print '2. FETCHING BADGES'

    for row in all_students:
        stu = row['diy_nickname']
        print '..for ' + str(stu) + ' (' + str(row['grade_level']) + ' ' + row['school'] + ')'
        #get badges
        stu_badges = get_badges(stu)
        #append to master list if the student has badges
        if len(stu_badges) > 0:
            master_badges.extend(stu_badges)

    print
    print '3. FETCHING PROJECTS'

    for row in all_students:
        stu = row['diy_nickname']
        print '..for ' + str(stu) + ' (' + str(row['grade_level']) + ' ' + row['school'] + ')'
        #get projects
        stu_projects = get_projects(stu)
        #append to master list if the student has badges
        if len(stu_projects) > 0:
            master_projects.extend(stu_projects)

    print
    print '4. WRITING DATA TO CSV'
    file_dir = 'C:/data_robot/diy/data'
    #file_dir = '//winsql01/data'
    csv_dict_writer(file_dir, 'badges.csv', master_badges)
    csv_dict_writer(file_dir, 'projects.csv', master_projects)

    print
    print '5. CALLING DATABASE IMPORT VIA SQL SERVER AGENT JOB'
    conn = make_db_conn()
    #excuting as server agent job gives history, runtime stats, etc
    conn.execute("exec msdb.dbo.sp_start_job N'DIY | Load Data'")
    #conn.execute("exec [dbo].[sp_LoadDIYBadges]")
    #conn.execute("exec [dbo].[sp_LoadDIYProjects]")
    conn.commit()
    conn.close()

    #log file
    sys.stdout = old_stdout
    log_file.close()

if __name__ == '__main__':
    main()
