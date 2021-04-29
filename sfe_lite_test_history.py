import sys
import requests
import json
import time
from datetime import datetime
import urllib.parse
import os
import socket
from requests import get

exclude_run_if_failures = 100

###
###
###
def usage():
    print('')
    print('  python ' + sys.argv[0] + ' <bot websocket> <web_server_directory> <Continuous-Integration-Master>')
    print('')
    print('  (' + str(sys.argv) + ')')
    print('')

    sys.exit(3)


###
###
###
def get_new_code_in_pipeline(json_data):
    if len(json_data['changeSets']) == 0:
        return False

    changes = json_data['changeSets'][0]['items']

    #print('get_new_code_in_pipeline, changes: ' + json.dumps(json_data, indent=2))

    if len(changes) == 0:
        return False
    else:
        return True

###
###
###
def calculate_pass_rate(number_of_failed, number_of_passed):
    total = number_of_failed + number_of_passed

    if total != 0:
        return '{:5.2f}'.format(number_of_passed/total*100) + '%'
    else:
        return ''

test_case_list = {}
###
###
###
def add_test_case(class_name, name, duration, build_number, status, test_log_url):
    key = class_name + '-' + name

    #if test_log_url:
    #    print('add_test_case, test_log_url: ' + test_log_url)

    if key in test_case_list:
        test_case_list[key].append({'status': status, 'duration': duration, 'build_number': build_number, 'test_log': test_log_url})
    else:
        test_case_list[key] = [{'status': status, 'duration': duration, 'build_number': build_number, 'test_log': test_log_url}]

###
###
###
def has_status(list, status):
    for x in list:
        if x['status'] == status:
            return True
        
    return False

###
###
###
def print_test_case_list():
    #print(test_case_list)
    nr_of_stable_tests = 0
    nr_of_failed_tests = 0

    flaky_test = []

    test_case_duration_list = {}

    smoke_test = {}

    for x in test_case_list:
        # Only put passed test in duration-list
        if test_case_list[x][0]['status'] == 'PASSED':
            test_case_duration_list[x] = [test_case_list[x][0]['duration'], test_case_list[x][0]['status']]

        number_of_times_this_test_run = len(test_case_list[x])
        
        if '#smoke' in x:
            #print(str(len(test_case_list[x])) + ' ' + x + '  test_case_list[x]: ' + str(test_case_list[x]))
            smoke_test[x] = test_case_list[x]

        if number_of_times_this_test_run > 2:
            if has_status(test_case_list[x], 'FAILED'):
                #print('x: ' + x + '  ' + str(test_case_list[x]))
                #print('x: ' + x)
                #print('    ' + str(test_case_list[x]))

                nr_of_failed_tests += 1
                flaky_test.append({'test_case': x, 'result': (test_case_list[x])})
            else:
                nr_of_stable_tests += 1
        #else:
        #    print('unique: ' + x + '  ' + str(test_case_list[x]))
    #print('length: ' + str(len(test_case_list)))

    #print('nr_of_stable_tests: ' + str(nr_of_stable_tests))
    #print('nr_of_failed_tests : ' + str(nr_of_failed_tests))

    # Sort after duration
    test_case_duration_list = sorted(test_case_duration_list.items(), key = lambda kv:(kv[1], kv[0]), reverse=True)

    return [nr_of_stable_tests, flaky_test, test_case_duration_list, smoke_test]


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

    print('===> get_last_build_number, url: ' + url)

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
        print('get_build_status, Failed to get data (' + url + ')')
        sys.exit(1)

    # print('data: ' + json.dumps(r.json(), indent=2))

    building = r.json()['building']
    result = r.json()['result']

    duration_s = r.json()['duration']/1000

    if building:
        add_build(build_number, 'BUILDING', '', get_new_code_in_pipeline(r.json()))
        return 'BUILDING'
    else:
        add_build(build_number, result, duration_s, get_new_code_in_pipeline(r.json()))
        return result

build_list = {}
###
###
###
def add_build(build_number, result, duration, new_code):
    build_list[build_number] = {'result': result, 'duration': duration, 'new_code': new_code}

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
        if build_list[x]['new_code']:
            new_code = BOLD + '  New code' + BOLD_RESET
        else:
            new_code = ''

        if build_list[x]['duration'] == '':
            text += '   ' + str(x) + ' ' + build_list[x]['result'] + new_code + NEW_LINE
        else:
            if build_list[x]['result'] == 'FAILURE' or build_list[x]['result'] == 'UNSTABLE':
                if 'failed' in build_list[x]:
                    text += '   ' + str(x) + '  ' + calculate_pass_rate(build_list[x]['failed'], build_list[x]['passed']) + '  ' + build_list[x]['result'] + '  duration: ' + duration_readable(build_list[x]['duration']) + ' (fail: ' + str(build_list[x]['failed']) + ' skip: ' + str(build_list[x]['skipped']) + ' pass: ' + str(build_list[x]['passed']) + ')' + new_code + NEW_LINE
            elif build_list[x]['result'] == 'ABORTED':
                text += '   ' + str(x) + '   0.00%' + '  ' + build_list[x]['result'] + '  duration: ' + duration_readable(build_list[x]['duration']) + new_code + NEW_LINE
            else:
                text += '   ' + str(x) + ' 100.00%  ' + build_list[x]['result'] + '  duration: ' + duration_readable(build_list[x]['duration'])  + ' (fail: ' + str(build_list[x]['failed']) + ' skip: ' + str(build_list[x]['skipped']) + ' pass: ' + str(build_list[x]['passed']) + ')' + new_code + NEW_LINE

            total_duration += build_list[x]['duration']

        if build_list[x]['result'] == 'FAILURE' or build_list[x]['result'] == 'UNSTABLE':
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
    if nr_fail + nr_aborted + nr_pass != 0:
        text2 += '   Average duration  : ' + duration_readable(total_duration/(nr_fail + nr_aborted + nr_pass)) + NEW_LINE
    text2 += '-----------------------------------------' + NEW_LINE
    if nr_pass + nr_fail + nr_aborted != 0:
        text2 += BOLD + 'TL;TR, pass-rate: ' + '{:2.1f}'.format(nr_pass/(nr_pass + nr_fail + nr_aborted)*100) + '%' + BOLD_RESET + NEW_LINE
    text2 += '=========================================' + NEW_LINE
    return [text, text2, build_list]

###
###
###
def set_log_prefix(list):
    return_string = ''

    for i in reversed(list):
        return_string += i + ' / '

    return_string = return_string.replace(

        ' ', '_').replace('/', '_').replace('-', '_')
    return (return_string)

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
                #add_failed_test_case(class_name, name, build_number)
                nr_fail += 1
            elif status == 'PASSED' or status == 'FIXED':
                nr_pass += 1
            elif status == 'SKIPPED':
                nr_skip += 1
            else:
                print('error status: ' + status)

    if (nr_fail < exclude_run_if_failures):
        for x in r.json()['suites']:
            log_prefix = set_log_prefix(x['enclosingBlockNames'])
            print('log_prefix: ' + log_prefix)
            for y in x['cases']:
                class_name = y['className']
                name = y['name']
                status = y['status']
                duration = y['duration']

                if status == 'FAILED' or status == 'REGRESSION':
                    tmp_name = name.replace('"', '_').replace(' ', '_').replace(':', '_').replace('#', '_').replace('.', '_').replace('-', '_').replace(',', '_').replace('/', '_').replace('(', '_').replace(')', '_').replace('@', '_').replace('&', '_')
                    tmp_class_name = class_name.replace(':', '_').replace('/', '_')

                    test_log_url = url + '(root)/' + urllib.parse.quote(tmp_class_name + '/') + log_prefix + tmp_name + '/'

                    #print('tmp_class_name: ' + tmp_class_name)
                    #print('tmp_name: ' + tmp_name)
                    #print('test_log_url: ' + test_log_url)

                    add_test_case(class_name, name, duration, build_number, 'FAILED', test_log_url)
                elif status == 'PASSED' or status == 'FIXED':
                    add_test_case(class_name, name, duration, build_number, 'PASSED', '')
                elif status == 'SKIPPED':
                    add_test_case(class_name, name, duration, build_number, 'SKIPPED', '')
                else:
                    print('error status: ' + status)
    else:
        print('MORE THAN ' + str(exclude_run_if_failures) + ' failures!!!!!')
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
    
    return job_name + '/' + job_name2.replace('%20', '-') + '/' + now.strftime("%Y-%m-%d-%H-%M")


###
###
###
def write_test_cases(path, filename, test_cases):
    #print('write_test_cases, path      : ' + path)
    #print('write_test_cases, filename  : ' + filename)
    #print('write_test_cases, test_cases: ' + str(test_cases))
    
    # Create directory
    if not os.path.exists(path):
        os.makedirs(path)

    f = open(path + '/' + filename, 'w')

    for x in test_cases:
        f.write('<b>' + x['testcase'] + '</b><br/>\n')
        #print('   ' + filename + ': ' + x['testcase'])

        for q in x['result']:
            if q['test_log']:
                f.write('   <p><a href=\"' + q['test_log'] + '\">' + 'log</a></p>\n')
                #print('      ' + q['test_log'])
    f.close()

###
###
###
def write_failures_test_cases(path, filename, test_cases):
    # Create directory
    if not os.path.exists(path):
        os.makedirs(path)

    f = open(path + '/' + filename, 'w')

    for x in test_cases:
        f.write('<b>' + x + '</b><br/>\n')

    f.close()

###
###
###
###
###
###
def write_all_test_cases(path, filename, tests):
    # Create directory
    if not os.path.exists(path):
        os.makedirs(path)

    f = open(path + '/' + filename, 'w')

    for x in tests:
        f.write('<b>' + x + '</b><br/>\n')
        for q in tests[x]:
            f.write('&nbsp;&nbsp;&nbsp;build ' + str(q['build_number']) + ': ' + q['status'] + '<br/>\n')

    f.close()

###
###
###
def write_test_cases_duration(path, filename, tests):
    # Create directory
    if not os.path.exists(path):
        os.makedirs(path)

    f = open(path + '/' + filename, 'w')

    #for x in q:
    #    print(str(x[1]) + '   ' + str(x[0]))write_test_cases

    for x in tests:
        f.write(str(x[1][0]) + '&nbsp;&nbsp;&nbsp;&nbsp;' + str(x[1][1]) + '&nbsp;&nbsp;&nbsp;&nbsp;' + str(x[0]) + '<br/>\n')

    f.close()


###
###
###
def write_test_cases_smoke(path, filename, tests):
    # Create directory
    if not os.path.exists(path):
        os.makedirs(path)

    f = open(path + '/' + filename, 'w')

    for x in smoke_test:
        f.write('<b>' + x + '</b><br/>\n')
        for q in smoke_test[x]:
            f.write('&nbsp;&nbsp;&nbsp;build ' + str(q['build_number']) + ': ' + q['status'] + '<br/>\n')

    f.close()


###
###
###
def at_least_one_build_success(build_list):
    for x in build_list:
        if build_list[x]['result'] == 'SUCCESS':
            return True
    
    return False

###
###
###
def last_two_builds_failed(build_list):
    nr_of_failures = 0
    for x in reversed(build_list):
        if build_list[x]['result'] == 'ABORTED':
            continue

        if build_list[x]['result'] == 'BUILDING':
            continue
        
        if build_list[x]['result'] == 'SUCCESS':
            return False

        if build_list[x]['result'] == 'FAILURE':
            nr_of_failures += 1

            if nr_of_failures == 2:
                return True

    return False

###
###
###
def extract_all_test_failed():
    list_of_test_failed = []
    #print('extract_all_test_failed, test_case_list: ' + json.dumps(test_case_list, indent=2))

    for x in test_case_list:
        for q in test_case_list[x]:
            if q['status'] == 'FAILED':
                list_of_test_failed.append(x)
                break

    return list_of_test_failed


###
###
###
def extract_all_p1_p1_test_failed(list_of_test_failed):
    for x in list_of_test_failed:
        if '#p1-p1' in x:
            print('>>>> ' + x)

###
###

#################################################

my_ip_address = '10.245.20.105' #get('https://api.ipify.org').text
#url = 'https://jenkins.rtc.dev.symphony.com/job/'
url = 'https://warpdrive-lab.dev.symphony.com/jenkins/job/mana/job/'


print('my_ip_address: ' + my_ip_address)

show_number_of_builds = 5

if len(sys.argv) == 1:
    show_number_of_builds = 3
    web_url = ''
    web_server_path = '/Users/johan.kwarnmark/src/web-server/'
    #job_name =  'SFE-Lite'
    #job_name2 = 'Continuous-Integration-Master'
    job_name = 'EPOD-CI-TEST'
    job_name2 = 'EPOD-CI-MASTER'
    #job_name2 = 'EPOD-CI-20-12'
    #job_name2 = 'Continuous-Integration-20.9'
    #job_name = 'SFE-RTC'
    #job_name2 = 'Daily%20E2E%20CI%20St2%20C2'
    #job_name2 = 'Daily%20E2E%20CI%20St2%20C1'
    bot = False
elif len(sys.argv) == 5:
    web_url = sys.argv[1]
    web_server_path = sys.argv[2]
    job_name = sys.argv[3]
    job_name2 = sys.argv[4]
    bot = True
else:
    usage()




if bot:
    NEW_LINE   = '<br/>\n'
    BOLD       = '<b>'
    BOLD_RESET = '</b>'

else:
    NEW_LINE   = '\n'
    BOLD       = '\033[1m'
    BOLD_RESET = '\033[39m' + '\u001b[0m'



subject = job_name + ' ' + job_name2.replace('%20', ' ')  + ' (last ' + str(show_number_of_builds) + ' builds)'
body = ''



last_build_number = get_last_build_number(url, job_name, job_name2)

print('last_build_number: ' + str(last_build_number))

body += NEW_LINE

body += create_link(url + job_name + '/job/' + job_name2) + NEW_LINE

for x in range(last_build_number-show_number_of_builds+1, last_build_number+1):
    if x < 1:
        continue
    print('build-number: ' + str(x))
    result = get_build_status(url, job_name, job_name2, x)

    print('result: ' + result)

    if result == 'ABORTED':
        continue
    get_build_test_report(url, job_name, job_name2, x)

[text, text2, build_list] = get_build_list()

body += text

body += '-----------------------------------------' + NEW_LINE

body += text2

[nr_of_stable_tests, test_failed, test_case_duration_list, smoke_test] = print_test_case_list()

skipped_test = []
failed_always_test = []
failed_last_2 = []
flaky_test = []

list_of_test_failed = extract_all_test_failed()

#list_of_p1_p1_test_failed = extract_all_p1_p1_test_failed(list_of_test_failed)

#print('zz: ' + list_of_p1_p1_test_failed)

#sys.exit(5)

for x in test_failed:

    if x['result'][-1]['status'] == 'SKIPPED':
        skipped_test.append({'testcase': x['test_case'], 'result': x['result']})
        continue

    #if not 'PASSED' in x['result']:
    if (not has_status(x['result'], 'PASSED')) and (not at_least_one_build_success(build_list)):
        failed_always_test.append({'testcase': x['test_case'], 'result': x['result']})
        continue

    if (last_two_builds_failed(build_list) and x['result'][-1]['status'] == 'FAILED') and (x['result'][-2]['status'] == 'FAILED'):
        failed_last_2.append({'testcase': x['test_case'], 'result': x['result']})
        continue

    flaky_test.append({'testcase': x['test_case'], 'result': x['result']})

folder_name = create_path_name()
path = web_server_path + folder_name

if skipped_test:
    body += BOLD + '   Test skipped in the last run: ' + str(len(skipped_test)) + BOLD_RESET + NEW_LINE
    write_test_cases(path, 'skipped_test.html', skipped_test)
    body += '       tests: ' + create_link('http://' + my_ip_address + ':8080/' + folder_name + '/skipped_test.html') + NEW_LINE

if failed_always_test:
    body += BOLD + '   Test failed 100%: ' + str(len(failed_always_test)) + BOLD_RESET + NEW_LINE
    write_test_cases(path, 'failed_always_test.html', failed_always_test)
    body += '       tests: ' + create_link('http://' + my_ip_address + ':8080/' + folder_name + '/failed_always_test.html') + NEW_LINE

if failed_last_2:
    body += BOLD + '   Test failed in the last two runs: ' + str(len(failed_last_2)) + BOLD_RESET + NEW_LINE
    write_test_cases(path, 'failed_last_two_runs_test.html', failed_last_2)
    body += '       tests: ' + create_link('http://' + my_ip_address + ':8080/' + folder_name + '/failed_last_two_runs_test.html') + NEW_LINE


if flaky_test:
    body += BOLD + '   Flaky tests: ' + str(len(flaky_test))  + BOLD_RESET + NEW_LINE
    write_test_cases(path, 'flaky_test.html', flaky_test)
    body += '       tests: ' + create_link('http://' + my_ip_address + ':8080/' + folder_name + '/flaky_test.html') + NEW_LINE

if test_case_duration_list:
    body += BOLD + '   Test cases duration ' + BOLD_RESET + NEW_LINE
    write_test_cases_duration(path, 'test_cases_duration.html', test_case_duration_list)
    body += '       tests: ' + create_link('http://' + my_ip_address + ':8080/' + folder_name + '/test_cases_duration.html') + NEW_LINE

if smoke_test:
    nr_of_pass_smoke_test = 0
    nr_of_fail_smoke_test = 0
    nr_of_skip_smoke_test = 0
    
    for x in smoke_test:
        for q in smoke_test[x]:
            if q['status'] == 'PASSED':
                nr_of_pass_smoke_test += 1
            elif q['status'] == 'FAILED':
                nr_of_fail_smoke_test += 1
            elif q['status'] == 'SKIPPED':
                nr_of_skip_smoke_test += 1
            else:
                print('q[status]: ' + q['status'])

    print('nr_of_pass_smoke_test: ' + str(nr_of_pass_smoke_test))
    print('nr_of_fail_smoke_test: ' + str(nr_of_fail_smoke_test))
    print('nr_of_skip_smoke_test: ' + str(nr_of_skip_smoke_test))
    if nr_of_pass_smoke_test + nr_of_fail_smoke_test > 0:
        pass_rate_smoke = nr_of_pass_smoke_test / (nr_of_pass_smoke_test + nr_of_fail_smoke_test) * 100
    else:
        pass_rate_smoke = 0
    body += BOLD + '   Smoke tests (' + str(len(smoke_test)) + ') ' + str(pass_rate_smoke) + '%' + BOLD_RESET + NEW_LINE
    write_test_cases_smoke(path, 'test_cases_smoke.html', smoke_test)
    body += '       tests: ' + create_link('http://' + my_ip_address + ':8080/' + folder_name + '/test_cases_smoke.html') + NEW_LINE

if list_of_test_failed:
    body += BOLD + '   Unique test failures (' + str(len(list_of_test_failed)) +  ')' + BOLD_RESET + NEW_LINE
    write_failures_test_cases(path, 'unique_test_failures.html', list_of_test_failed)
    body += '       tests: ' + create_link('http://' + my_ip_address + ':8080/' + folder_name + '/unique_test_failures.html') + NEW_LINE

if test_case_list:
    body += BOLD + '   Unique tests (' + str(len(test_case_list)) +  ')' + BOLD_RESET + NEW_LINE
    write_all_test_cases(path, 'unique_tests.html', test_case_list)
    body += '       tests: ' + create_link('http://' + my_ip_address + ':8080/' + folder_name + '/unique_tests.html') + NEW_LINE



nr_of_flaky_tests = len(flaky_test)

body += NEW_LINE

body += 'Extract test data from the last: ' + str(show_number_of_builds) + NEW_LINE
body += 'Exclude runs that is aborted!' + NEW_LINE
body += 'Exclude runs that have more than' + str(exclude_run_if_failures) + ' failures (pod down?)' + NEW_LINE
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
