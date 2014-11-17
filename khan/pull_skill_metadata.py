import requests
import csv

#csv format
csv.register_dialect('ALM', delimiter=',', quoting=csv.QUOTE_ALL)

#url = 'http://www.khanacademy.org/api/v1/topictree'
url = 'http://www.khanacademy.org/api/v1/topic/math'
#url = 'http://www.khanacademy.org/api/v1/topic/cc-eighth-grade-math'
#url = 'http://www.khanacademy.org/api/v1/topic/cc-8th-numbers-operations'
#url = 'http://www.khanacademy.org/api/v1/topic/basic-geo-special-right-triangle'

foo = requests.get(url).json()

#globals
global_depth = 0

skill = {
    'd_0': None,
    'd_1': None,
    'd_2': None,
    'd_3': None,
    'd_4': None,
    'd_5': None,
    'd_6': None,
    'domain_slug': None,
    'hide_meta': None,
    'description': None,
    'in_knowledge_map': None,
    'deleted': None
}

def parse_topics(tree):
    print 'CALLED, w/ ' + tree['title']

    global global_depth, skill
    skill['d_'+ str(global_depth)] = tree['node_slug']
    skill['hide_meta'] = tree['hide']
    skill['domain_slug'] = tree['domain_slug']
    skill['description'] = tree['description']
    skill['in_knowledge_map'] = tree['in_knowledge_map']
    skill['deleted'] = tree['deleted']

    if 'children' in tree.keys():
        #print "\t\t...with children. iterating..."

        for i in tree['children']:
            #if the child is a TOPIC, unpack it.
            global_depth += 1

            if i['kind'] == u'Topic':
                #print '\t\t\tchild is a topic.  unpack it'
                child_url = 'http://www.khanacademy.org/api/v1/topic/' + i['node_slug']
                #print '\t\t\t' + child_url
                child_tree = requests.get(child_url).json()

                #update the globals
                skill['d_'+ str(global_depth)] = i['node_slug']
                skill['hide_meta'] = i['hide']

                parse_topics(child_tree)

            #otherwise, record it!
            else:
                #print '\t\t\tchild is NOT a topic.  Parse it!'

                #clean out anything bigger than global depth before calling
                for n in range(0, 6):
                    if n > global_depth:
                        skill['d_'+ str(n)] = None

                #print skill

                record_skill_props(
                  skill_meta=skill,
                  skill_dict=i
                )
                global_depth = 0
    else:
        #print "\t\t...withOUT children."
        child_url = 'http://www.khanacademy.org/api/v1/topic/' + tree['node_slug']
        child_tree = requests.get(child_url).json()
        global_depth += 1
        parse_topics(child_tree)


def record_skill_props(skill_meta, skill_dict):
    #everything from meta, that tracks the parent levels
    #final_dict = skill_meta
    final_dict = {}
    for k, v in skill_meta.items():
        final_dict[k]=v

    #new stuff from the api response
    final_dict['kind'] = skill_dict['kind']
    final_dict['hide'] = skill_dict['hide']
    final_dict['internal_id'] = skill_dict['internal_id']
    final_dict['title'] = skill_dict['title']
    final_dict['slug'] = skill_dict['node_slug']
    final_dict['id'] = skill_dict['id']
    final_dict['url'] = skill_dict['url']

    #print(final_dict)
    master_skills.append(final_dict)
    return None

master_skills = []
parse_topics(foo)

#print master_skills

with open("topic_metadata.csv", 'wb') as f:
    #character encoding, sigh.
    master_skills = dict([(unicode(k).encode("utf-8"), unicode(v).encode("utf-8")) for k, v in master_skills.items()])
    w = csv.DictWriter(f, sorted(master_skills[0].keys()), dialect='ALM')
    w.writeheader()
    for i in master_skills:
        w.writerow(i)
    f.close()