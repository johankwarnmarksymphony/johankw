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


###
###
###
if len(sys.argv) == 1:
    #job_name =  'SFE-Lite'
    #job_name2 = 'PR-E2E'
    job_name = 'SFE-RTC'
    #job_name2 = 'PR%20IntTest%20runner%20C1'
    job_name2 = 'PR%20IntTest%20runner%20C2'

    show_number_of_pull_requests = 10

    web_url = ''
elif len(sys.argv) == 5:
    job_name                     = sys.argv[1]
    job_name2                    = sys.argv[2]
    show_number_of_pull_requests = int(sys.argv[3])
    web_url                      = sys.argv[4]
else:
    usage()


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
def get_latest_pr_number(prefix_url, job_name, job_name2):
    url = prefix_url + job_name + '/job/' + job_name2 + '/view/change-requests/'

    r = requests.get(url + '/api/json')

    if r.status_code != 200:
        print('get_latest_pr_number, Failed to get data')
        sys.exit(1)

    biggest = 0

    for x in r.json()['jobs']:
        number = int(x['name'].split('-')[1])

        if number > biggest:
            biggest = number

    return biggest
    
###
###
###
def get_status_of_pull_request_attempt(url, silent):
    r = requests.get(url)

    if r.status_code != 200:
        print('get_status_of_pull_request_attempt, Failed to get data')
        sys.exit(1)

    duration_s = r.json()['duration']/1000

    duration_text = duration_readable(duration_s)

    #print('data: ' + json.dumps(r.json(), indent=2))

    if r.json()['building']:
        if not silent:
            print('    Building ' + url)
        return ['BUILDING', '0']
    else:
        if not silent:
            print('    ' + r.json()['result'] + '  ' + url)
        return [r.json()['result'], duration_text]


###
###
###
def get_number_of_attempts_pull_request(prefix_url, job_name, job_name2, pr_number):
    url = prefix_url + job_name + '/job/' + job_name2 + '/job/' + pr_number
    
    r = requests.get(url + '/api/json')

    if r.status_code != 200:
        print('url: ' + url)
        print('get_number_of_attempts_pull_request, Failed to get data')
        return 0

    number_of_tries = r.json()['lastBuild']['number']

    return number_of_tries


###
###
###
def get_pull_request_status(prefix_url, job_name, job_name2, pr_number):
    url = prefix_url + job_name + '/job/' + job_name2 + '/job/' + pr_number

    r = requests.get(url + '/api/json')

    if r.status_code != 200:
        print('get_pull_request_status, Failed to get data')
        sys.exit(1)

    attempt = r.json()['lastBuild']['number']

    url = url + '/' + str(attempt) + '/api/json'
    [result, duration] = get_status_of_pull_request_attempt(url, True)

    return [result, duration]

###
###
###
def send_message_to_symphony(subject, body, webhook):
    data = '<messageML><b>' + subject + '</b><br/>' + body + '</messageML>'

    print('')
    print(data)
    print('')
    if webhook == '':
        return

    r = requests.post(webhook, data=data)

    print('send_message_to_symphony, r            : ' + str(r))
    print('send_message_to_symphony, r.status_code: ' + str(r.status_code))


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

    #print('hours  : ' + str(hours))
    #print('minutes: ' + str(minutes))

    if hours > 0:
        return str(hours) + 'h ' + str(minutes) + 'min' 
    else:
        return str(minutes) + 'min' 

###
###
###
def create_link(link):
    return '<a href=\"' + link + '\" />'

#################################################

NEW_LINE = '<br/>\n'
BOLD = '<b>'
BOLD_RESET = '</b>'

subject = job_name + ' ' + job_name2.replace('%20', ' ') + '  Pull-Requests' + ' (last ' + str(show_number_of_pull_requests) + ' pull requests)'
body = ''

print(subject)

url = 'https://jenkins.rtc.dev.symphony.com/job/'

body += create_link(url + job_name + '/job/' + job_name2) + NEW_LINE

# Get latest PR number
last_pr = get_latest_pr_number(url, job_name, job_name2)


###
### Print status of the last X pull requests
###

nr_pass     = 0
nr_fail     = 0
nr_building = 0
nr_aborted  = 0

for x in range(last_pr-show_number_of_pull_requests+1, last_pr+1):
    pr_name = 'PR-' + str(x)

    print('pr_name: ' + pr_name)

    number_of_attempts = get_number_of_attempts_pull_request(url, job_name, job_name2, pr_name)

    if number_of_attempts == 0:
        continue

    [pr_status, duration] = get_pull_request_status(url, job_name, job_name2, pr_name)

    if pr_status == 'SUCCESS':
        body += '   ' + pr_name + ' ' + '{:8}'.format(pr_status) + '  attempts: ' + str(number_of_attempts) + ' duration: ' + duration + NEW_LINE
        nr_pass += 1
    elif pr_status == 'FAILURE':
        body += '   ' + pr_name + ' ' + '{:8}'.format(pr_status) + '  attempts: ' + str(number_of_attempts) + ' duration: ' + duration + NEW_LINE
        nr_fail += 1
    elif pr_status == 'BUILDING':
        body += '   ' + pr_name + ' ' + '{:8}'.format(pr_status) + '  attempts: ' + str(number_of_attempts) + NEW_LINE
        nr_building += 1
    elif pr_status == 'ABORTED':
        body += '   ' + pr_name + ' ' + '{:8}'.format(pr_status) + '  attempts: ' + str(number_of_attempts) + NEW_LINE
        nr_aborted += 1
    else:
        print('error pr_status: ' + pr_status)

print('body: ' + body)

body += '-----------------------------------------' + NEW_LINE

body += '   Number of failed  : ' + BOLD + str(nr_fail) + BOLD_RESET + NEW_LINE
body += '   Number of aborted : ' + BOLD + str(nr_aborted) + BOLD_RESET + NEW_LINE
body += '   Number of building: ' + BOLD + str(nr_building) + BOLD_RESET + NEW_LINE
body += '   Number of pass    : ' + BOLD + str(nr_pass) + BOLD_RESET + NEW_LINE

body += '-----------------------------------------' + NEW_LINE
if nr_pass + nr_fail != 0:
    body += BOLD + 'TL;TR, pass-rate: ' + '{:2.1f}'.format(nr_pass/(nr_pass + nr_fail)*100) + '%' + BOLD_RESET + NEW_LINE


send_message_to_symphony(subject, body, web_url)

