import sys
import requests
import json
import time
from datetime import datetime
import urllib.parse
import os
import socket


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
def add_test_case(class_name, name, pr_name, status):
    key = class_name + '-' + name

    if key in test_case_list:
        test_case_list[key].append(status)
    else:
        test_case_list[key] = [status]
        
###
###
###
def print_test_case_list():
    #print(test_case_list)
    nr_of_stable_tests = 0
    nr_of_failed_tests = 0

    flaky_test = []

    for x in test_case_list:

        number_of_times_this_test_run = len(test_case_list[x])
        
        if number_of_times_this_test_run > 2:
            if 'FAILED' in test_case_list[x]:
                #print('x: ' + x + '  ' + str(test_case_list[x]))
                #print('x: ' + x)
                #print('    ' + str(test_case_list[x]))

                nr_of_failed_tests += 1
                flaky_test.append({'test_case': x, 'result': test_case_list[x]})
            else:
                nr_of_stable_tests += 1
        #else:
        #    print('unique: ' + x + '  ' + str(test_case_list[x]))
    #print('length: ' + str(len(test_case_list)))

    #print('nr_of_stable_tests: ' + str(nr_of_stable_tests))
    #print('nr_of_failed_tests : ' + str(nr_of_failed_tests))

    return [nr_of_stable_tests, flaky_test]

failed_test_case_list = {}
###
###
###
def add_failed_test_case(class_name, name, pr_name):
    key = class_name + '-' + name

    if key in failed_test_case_list:
        if not pr_name in failed_test_case_list[key]:
            failed_test_case_list[key].append(pr_name)
        #else:<
        #    print('duplicate ' + key)

        # = failed_test_case_list[key] + ' ' + pr_name
    else:
        failed_test_case_list[key] = [pr_name]
        

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

    # print('data: ' + json.dumps(r.json(), indent=2))

    building = r.json()['building']
    result = r.json()['result']

    duration_s = r.json()['duration']/1000

    if building:
        add_build(build_number, 'BUILDING', '')
        return 'BUILDING'
    else:
        add_build(build_number, result, duration_s)
        return result

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
    text2 += '=========================================' + NEW_LINE
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

    if (nr_fail < 50):
        for x in r.json()['suites']:
            for y in x['cases']:
                class_name = y['className']
                name = y['name']
                status = y['status']

                if status == 'FAILED' or status == 'REGRESSION':
                    add_test_case(class_name, name, build_number, 'FAILED')
                elif status == 'PASSED' or status == 'FIXED':
                    add_test_case(class_name, name, build_number, 'PASSED')
                elif status == 'SKIPPED':
                    add_test_case(class_name, name, build_number, 'SKIPPED')
                else:
                    print('error status: ' + status)
    else:
        print('MORE THAN 50 failures!!!!!')
        # sys.exit(5)

    add_build2(build_number, nr_fail, nr_pass, nr_skip)

###
###
###
def create_link(link):
    return '<a href=\"' + link + '\" />'


###
###
###
def create_path_name():
    # datetime object containing current date and time
    now = datetime.now()
    
    return now.strftime("%Y-%m-%d-%H-%M")

###
###
###
def write_test_cases(path, filename, test_cases):
    print('write_test_cases, path      : ' + path)
    print('write_test_cases, filename  : ' + filename)
    print('write_test_cases, test_cases: ' + str(test_cases))
    
    # Create directory
    if not os.path.exists(path):
        os.makedirs(path)

    f = open(path + '/' + filename, 'w')

    for x in test_cases:
        f.write(x + '<br/>\n')
    f.close()


#################################################

my_ip_address = (socket.gethostbyname_ex(socket.gethostname())[-1])[0]

print('my_ip_address: ' + my_ip_address)


if len(sys.argv) == 1:
    web_url = ''
    bot = False
elif len(sys.argv) == 2:
    web_url = sys.argv[1]
    bot = True
else:
    usage()

show_number_of_builds = 10
web_server_path = '/Users/johan.kwarnmark/src/web-server/'


if bot:
    NEW_LINE   = '<br/>\n'
    BOLD       = '<b>'
    BOLD_RESET = '</b>'

else:
    NEW_LINE   = '\n'
    BOLD       = '\033[1m'
    BOLD_RESET = '\033[39m' + '\u001b[0m'



subject = 'SFE-Lite Continuous-Integration MASTER' + ' (last ' + str(show_number_of_builds) + ' builds)'
body = ''

url = 'https://jenkins.rtc.dev.symphony.com/job/'
job_name =  'SFE-Lite'
job_name2 = 'Continuous-Integration-Master'
#job_name2 = 'Continuous-Integration-20.8'

last_build_number = get_last_build_number(url, job_name, job_name2)

print('last_build_number: ' + str(last_build_number))

body += NEW_LINE

body += create_link(url + job_name + '/job/' + job_name2) + NEW_LINE

for x in range(last_build_number-show_number_of_builds+1, last_build_number+1):
    print('build-number: ' + str(x))
    result = get_build_status(url, job_name, job_name2, x)

    print('result: ' + result)

    if result == 'ABORTED':
        continue
    get_build_test_report(url, job_name, job_name2, x)

[text, text2] = get_build_list()
body += text

body += '-----------------------------------------' + NEW_LINE

body += text2

[nr_of_stable_tests, test_failed] = print_test_case_list()


skipped_test = []
failed_always_test = []
failed_last_2 = []
flaky_test = []

for x in test_failed:
    
    #print('Flaky: ' + str(x))
    #print('q: ' + (x['result'])[-1])

    if (x['result'])[-1] == 'SKIPPED':
        skipped_test.append(x['test_case'])
        continue

    if not 'PASSED' in x['result']:
        failed_always_test.append(x['test_case'])
        continue

    if (x['result'])[-1] == 'FAILED' and (x['result'])[-2] == 'FAILED':
        failed_last_2.append(x['test_case'])
        continue

    if 'PASSED' in x['result']:
        #print('at least one passed: ' + str(x['result']))
        flaky_test.append(x['test_case'])

folder_name = create_path_name()
path = web_server_path + folder_name

if skipped_test:
    body += BOLD + '   Test skipped in the last run: ' + str(len(skipped_test)) + BOLD_RESET + NEW_LINE
    write_test_cases(path, 'skipped_test.html', skipped_test)
    body += '       tests: ' + create_link('http://' + my_ip_address + ':8080/' + folder_name + '/skipped_test.html') + NEW_LINE

    #for x in skipped_test:
    #    body += '      ' + x + NEW_LINE

if failed_always_test:
    body += BOLD + '   Test failed 100%: ' + str(len(failed_always_test)) + BOLD_RESET + NEW_LINE
    write_test_cases(path, 'failed_always_test.html', failed_always_test)
    body += '       tests: ' + create_link('http://' + my_ip_address + ':8080/' + folder_name + '/failed_always_test.html') + NEW_LINE

    #for x in failed_always_test:
    #    body += '      ' + x + NEW_LINE

if failed_last_2:
    body += BOLD + '   Test failed in the last two runs: ' + str(len(failed_last_2)) + BOLD_RESET + NEW_LINE
    write_test_cases(path, 'failed_last_two_runs_test.html', failed_last_2)
    body += '       tests: ' + create_link('http://' + my_ip_address + ':8080/' + folder_name + '/failed_last_two_runs_test.html') + NEW_LINE

    #for x in failed_last_2:
    #    body += '      ' + x + NEW_LINE

if flaky_test:
    body += BOLD + '   Flaky tests: ' + str(len(flaky_test))  + BOLD_RESET + NEW_LINE
    write_test_cases(path, 'flaky_test.html', flaky_test)
    body += '       tests: ' + create_link('http://' + my_ip_address + ':8080/' + folder_name + '/flaky_test.html') + NEW_LINE

    #for x in flaky_test:
    #    body += '      ' + x + NEW_LINE

nr_of_flaky_tests = len(flaky_test)

body += NEW_LINE

body += 'Extract test data from the last: ' + str(show_number_of_builds) + NEW_LINE
body += 'Exclude runs that is aborted!' + NEW_LINE
body += 'Exclude runs that have more than 50 failures (pod down?)' + NEW_LINE
body += '-----------------------------------------' + NEW_LINE
body += 'Number of stable tests                   : ' + BOLD + str(nr_of_stable_tests) + BOLD_RESET + NEW_LINE
body += 'Number of flaky tests                    : ' + BOLD + str(nr_of_flaky_tests) + BOLD_RESET + NEW_LINE
body += 'Number of tests that fails 100%          : ' + BOLD + str(len(failed_always_test)) + BOLD_RESET + NEW_LINE
body += 'Number of tests that failed last two runs: ' + BOLD + str(len(failed_last_2)) + BOLD_RESET + NEW_LINE
body += '-----------------------------------------' + NEW_LINE
if not (nr_of_stable_tests == 0 and nr_of_flaky_tests == 0):
    body += 'Flakiness             : ' + BOLD + '{:2.1f}'.format(nr_of_flaky_tests/(nr_of_flaky_tests + nr_of_stable_tests)*100) + '%' + BOLD_RESET + NEW_LINE
body += '=========================================' + NEW_LINE


print(body)

print('bot: ' + str(bot))

if bot:
    send_message_to_symphony(subject, body, web_url)