import sys
import requests
import json
import time
from datetime import datetime
import urllib.parse


###
###
###
def usage():
    print('')
    print('  python ' + sys.argv[0])
    print('')
    print('  (' + str(sys.argv) + ')')
    print('')

    sys.exit(3)


test_case_list = {}
###
###
###
def add_failed_test_case(class_name, name, pr_name):
    key = class_name + '-' + name

    if key in test_case_list:
        if not pr_name in test_case_list[key]:
            test_case_list[key].append(pr_name)
        #else:
        #    print('duplicate ' + key)

        # = test_case_list[key] + ' ' + pr_name
    else:
        test_case_list[key] = [pr_name]
        
###
###
###
def print_test_case_list():
    test_list = []

    return_text = ''

    for x in test_case_list:
        y = x.replace('\uff0e', '.') 
        test_list.append('{:02d}'.format(len(test_case_list[x]))   + '  ' + str(y))

    q = sorted(test_list, reverse=True)

    for x in q:
        #if not (x.startswith('01') or x.startswith('02') or x.startswith('03') or x.startswith('04') or x.startswith('05')):
        return_text += '   ' + x + NEW_LINE
        


    return return_text

###
###
###
def send_message_to_symphony(subject, body, webhook):
    data = '<messageML><b>' + subject + '</b><br/>' + body + '</messageML>'

    print('data: ' + data)

    if webhook == '':
        return

    r = requests.post(webhook, data=data)

    print('r: ' + str(r))
    print('r.status_code: ' + str(r.status_code))


###
###
###
def get_last_build_number(prefix_url, job_name, job_name2):
    url = prefix_url + job_name + '/job/' + job_name2

    r = requests.get(url + '/api/json')

    if r.status_code != 200:
        print('get_last_build_number, Failed to get data')
        sys.exit(1)

    return int(r.json()['lastBuild']['number'])


###
###
###
def duration_readable(duration):
    hours = int(duration / 3600)
    minutes = int((duration - hours*3600)/60)

    if hours > 0:
        return str(hours) + 'h ' + str(minutes) + 'min' 
    else:
        return str(minutes) + 'min' 
        

###
###
###
def get_build_status(prefix_url, job_name, job_name2, build_number):
    url = prefix_url + job_name + '/job/' + job_name2 + '/' + str(build_number)

    r = requests.get(url + '/api/json')

    if r.status_code != 200:
        print('get_last_build_number, Failed to get data')
        sys.exit(1)

    #print('data: ' + json.dumps(r.json(), indent=2))

    building = r.json()['building']
    result = r.json()['result']

    duration_s = r.json()['duration']/1000

    if building:
        add_build(build_number, 'BUILDING', '')
    else:
        add_build(build_number, result, duration_s)


build_list = {}
###
###
###
def add_build(build_number, result, duration):
    build_list[build_number] = {'result': result, 'duration': duration}

###
###
###
def add_build2(build_number, failed, passed, skipped):
    build_list[build_number].update({'failed': failed, 'passed': passed, 'skipped': skipped})

###
###
###
def get_build_list():
    nr_fail = 0
    nr_pass = 0
    nr_building = 0
    nr_aborted = 0

    text = ''
    text2 = ''

    total_duration = 0

    for x in build_list:
        if build_list[x]['duration'] == '':
            text += '   ' + str(x) + ' ' + build_list[x]['result'] + NEW_LINE
        else:   
            if 'failed' in build_list[x]:
                text += '   ' + str(x) + ' ' + build_list[x]['result'] + '  duration: ' + duration_readable(build_list[x]['duration']) + ' (fail: ' + str(build_list[x]['failed']) + ' skip: ' + str(build_list[x]['skipped']) + ' pass: ' + str(build_list[x]['passed']) + ')' + NEW_LINE
            else:
                text += '   ' + str(x) + ' ' + build_list[x]['result'] + '  duration: ' + duration_readable(build_list[x]['duration'])  + NEW_LINE

            total_duration += build_list[x]['duration']

        if build_list[x]['result'] == 'FAILURE':
            nr_fail += 1
        elif build_list[x]['result'] == 'BUILDING':
            nr_building += 1
        elif build_list[x]['result'] == 'ABORTED':
            nr_aborted += 1
        else:
            nr_pass += 1

    text2 += '   Number of failed  : ' + str(nr_fail) + NEW_LINE
    text2 += '   Number of aborted : ' + str(nr_aborted) + NEW_LINE
    text2 += '   Number of building: ' + str(nr_building) + NEW_LINE
    text2 += '   Number of passed  : ' + str(nr_pass) + NEW_LINE
    text2 += '   Average duration  : ' + duration_readable(total_duration/(nr_fail + nr_aborted + nr_pass)) + NEW_LINE
    text2 += '-----------------------------------------' + NEW_LINE
    text2 += BOLD + 'TL;TR, pass-rate: ' + '{:2.1f}'.format(nr_pass/(nr_pass + nr_fail + nr_aborted)*100) + '%' + BOLD_RESET + NEW_LINE

    return [text, text2]

###
###
###
def get_build_test_report(prefix_url, job_name, job_name2, build_number):
    url = prefix_url + job_name + '/job/' + job_name2 + '/' + str(build_number) + '/testReport/'

    r = requests.get(url + '/api/json')

    if r.status_code != 200:
        return

    nr_pass = 0
    nr_fail = 0
    nr_skip = 0

    for x in r.json()['suites']:
        for y in x['cases']:
            class_name = y['className']
            name = y['name']
            status = y['status']

            if status == 'FAILED' or status == 'REGRESSION': 
                add_failed_test_case(class_name, name, build_number)
                nr_fail += 1
            elif status == 'PASSED' or status == 'FIXED':
                nr_pass += 1
            elif status == 'SKIPPED':
                nr_skip += 1
            else:
                print('error status: ' + status)
    add_build2(build_number, nr_fail, nr_pass, nr_skip)

###
###
###
def create_link(link):
    return '<a href=\"' + link + '\" />'


#################################################
if len(sys.argv) == 1:
    web_url = ''
elif len(sys.argv) == 2:
    web_url = sys.argv[1]
else:
    usage()

show_number_of_builds = 20

NEW_LINE = '<br/>\n'
BOLD = '<b>'
BOLD_RESET = '</b>'

subject = 'SFE-Lite Continuous-Integration' + ' (last ' + str(show_number_of_builds) + ' builds)'
body = ''

url = 'https://jenkins.rtc.dev.symphony.com/job/'
job_name =  'SFE-Lite'
job_name2 = 'Continuous-Integration'


last_build_number = get_last_build_number(url, job_name, job_name2)

body += NEW_LINE

body += create_link(url + job_name + '/job/' + job_name2) + NEW_LINE

for x in range(last_build_number-show_number_of_builds+1, last_build_number+1):
    get_build_status(url, job_name, job_name2, x)

    get_build_test_report(url, job_name, job_name2, x)

[text, text2] = get_build_list()
body += text

body += '-----------------------------------------' + NEW_LINE

body += '<b>Test case report: </b>' + NEW_LINE
body += print_test_case_list()

body += '-----------------------------------------' + NEW_LINE
body += text2

send_message_to_symphony(subject, body, web_url)
