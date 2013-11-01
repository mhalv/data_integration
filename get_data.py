import requests
import pyodbc
import json
import csv
from pprint import pprint

csv.register_dialect('ALM', delimiter=',', quoting=csv.QUOTE_ALL)

def csv_dict_writer(file_path, file_name, data):
    with open("%s/%s" % (file_path, file_name),'wb') as f:
        w = csv.DictWriter(f,data[0].keys(), dialect='ALM')
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
       SELECT diy_nickname
       FROM KIPP_NJ..CUSTOM_STUDENTS
       WHERE diy_nickname IS NOT NULL""")
    columns = [column[0] for column in cursor.description]
    #return as list
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
        #close db connection
    conn.close()
    #return results
    return [{'diy_nickname': u'determinator'}]

def build_stu_url(resource, maker, property='', parameters=''):
    base = 'https://brain.diy.org/'
    #only add parameters if value passed
    if parameters != '':
        parameters = '?' + parameters
    url = base + resource + '/' + maker + '/' + property + parameters
    return url


def get_badges(nickname):
    #build the url
    badge_url = build_stu_url('makers', nickname, 'achievements', 'limit=999')
    print badge_url
    #request the data
    r = requests.get(badge_url)
    #diy returns unicode string; decode the json
    resp = json.loads(r.text)
    #narrow down the response to skills
    badges = resp['response']['skills']

    #empty list - will insert dictionaries for each badge
    student_badge_list = []
    #make a dict out of each item in the json; append to master_badges list
    for skill in badges:
        badge_dict = {}
        badge_dict['nickname'] = str(nickname)
        badge_dict['badge'] = str(skill['title'])
        badge_dict['earned'] = skill['stats']['earned']
        badge_dict['date_earned'] = skill['stats']['earned_at']
        student_badge_list.append(badge_dict)

    return(student_badge_list)

#main loop that runs the sequence
def main():
    #get TEAM students who have a diy.org username
    print '1. GETTING STUDENTS'
    global all_students

    all_students = get_students()
    pprint(all_students)

    #list to hold all the projects
    master_badges = []
    master_project = []
    addtl_proj_det = []

    print
    print '2. FETCHING BADGES'

    for row in all_students:
        stu = row['diy_nickname']
        #get badges
        stu_badges = get_badges(stu)
        #append to master list if the student has badges
        if len(stu_badges) > 0:
            master_badges.extend(stu_badges)

    print
    print '3. WRITING DATA TO CSV'
    file_dir = 'C:/data_robot/diy/data'

    csv_dict_writer(file_dir, 'badges.csv', master_badges)

    print
    print '4. CALLING DATA LOAD ON THE DATABASE'
    conn = make_db_conn()
    #conn.execute("exec msdb.dbo.sp_start_job N'DIY | Load Data'")
    conn.execute("exec [dbo].[sp_LoadDIYBadges]")
    conn.commit()
    conn.close()

if __name__ == '__main__':
    main()
