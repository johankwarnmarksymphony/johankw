import sys
import requests
import json
import os
from datetime import datetime
try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup

test_case_list = {}
test_case_build_number_list = {}
sort_test_case_list = []

###
###
###


def usage():
    print('')
    print('  python ' + sys.argv[0] + ' <project name> <branch name>')
    print('')
    print('  python ' + sys.argv[0] +
          ' SFE-Lite Continuous-Integration-Master')
    print('')
    print('  (' + str(sys.argv) + ')')
    print('')

    sys.exit(3)


###
###
###
def get_test_result(url):
    print('get_test_result, url: ' + url)

    r = requests.get(url)

    if r.status_code != 200:
        return

    test_case_name = ''
    for x in r.text.splitlines():
        #print('xxx: ' + x)
        if 'FAILED' in x:
            if '#p1-p1' in test_case_name:
                build_number = x.split('build ')[1].split(':')[0]

                tmp = build_number + ': ' + test_case_name

                print('tmp: ' + tmp)

                if not tmp in test_case_build_number_list:
                    test_case_build_number_list[tmp] = 1

                    print('  ADD')

                    if test_case_name in test_case_list:
                        #print('Found again: ' + test_case_name)
                        #test_case_list[test_case_name]
                        test_case_list[test_case_name] = test_case_list[test_case_name] + 1
                    else:
                        test_case_list[test_case_name] = 1

        if x.startswith('<b>'):
            test_case_name = x[3:].split('</b>')[0]


###
###
###
def html_table_to_json(content, indent=None):
    soup = BeautifulSoup(content, "html.parser")
    rows = soup.find_all("tr")

    headers = {}
    thead = soup.find("thead")
    if thead:
        thead = thead.find_all("th")
        for i in range(len(thead)):
            headers[i] = thead[i].text.strip().lower()
    data = []
    for row in rows:
        cells = row.find_all("td")
        if thead:
            items = {}
            for index in headers:
                items[headers[index]] = cells[index].text
        else:
            items = []
            for index in cells:
                items.append(index.text.strip())
        data.append(items)
    return data


###
###
###
def print_test_case_list():
    for x in test_case_list:
        print('x: ' + x + '  ' + str(test_case_list[x]))

        #if '#p1-p1' in x:
        sort_test_case_list.append(str(test_case_list[x]) + '..' + x)

    print('len(test_case_list): ' + str(len(test_case_list)))

    sort_test_case_list.sort(reverse=True)

    print()
    for x in sort_test_case_list:
        print(x)


###
###
###
def save_test_case_list():
    my_ip_address = '10.245.20.105'
    now = datetime.now()
    folder = 'SFE-Lite-p1-p1/' + now.strftime("%Y-%m-%d-%H-%M")
    path = web_server_path + folder
    filename = 'p1-p1.html'

    # Create directory
    if not os.path.exists(path):
        os.makedirs(path)

    f = open(path + '/' + filename, 'w')

    for x in sort_test_case_list:
        f.write('<p>' + x + '</p><br/>\n')

    f.close()

    return 'http://' + my_ip_address + ':8080/' + folder + '/' + filename

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

###########################################################
###########################################################
###########################################################


number_of_builds = 6
url = 'http://10.245.20.105:8080/CI-E2E-TEST/MASTER-EPOD/'


if len(sys.argv) == 1:
    web_url = ''
    web_server_path = '/Users/johan.kwarnmark/src/web-server/'
    bot = False
elif len(sys.argv) == 3:
    web_url = sys.argv[1]
    web_server_path = sys.argv[2]
    bot = True

if bot:
    NEW_LINE = '<br/>\n'
    BOLD = '<b>'
    BOLD_RESET = '</b>'
else:
    NEW_LINE = '\n'
    BOLD = '\033[1m'
    BOLD_RESET = '\033[39m' + '\u001b[0m'


r = requests.get(url)

if r.status_code != 200:
    print('get_test_status_of_pull_request_attempt, Failed to get data, url: ' + url)

    sys.exit(5)


# Get all directories
data = html_table_to_json(r.text)

dirs = []
for x in data:
    directory = x[3]

    if directory != '../':
        dirs.append(directory)

# Loop over all dirs
for x in dirs:
    print('  all dirs: ' + x)

# Loop over the last x runs
dirs = dirs[-number_of_builds:]

for x in dirs:
    print('  dirs: ' + x)

    get_test_result(url + x + 'unique_tests.html')

# Print result
print_test_case_list()

# Save result page
result_url = save_test_case_list()
print('result_url: ' + result_url)

if len(sort_test_case_list) > 0:
    body = 'Last 7 days we have flaky p1-p1 test: ' + \
        '<a href=\"' + result_url + '\" />' + NEW_LINE

    body += NEW_LINE
    body += BOLD + 'No p1-p1 test should fail on master' + BOLD_RESET + NEW_LINE
else:
    body = 'Awesome! No flaky p1-p1 test the last 7 days on master' + NEW_LINE

print(body)

# Subject
now = datetime.now()
my_date = now.strftime("%Y-%m-%d %H:%M")
subject = 'SFE-Lite P1-P1 test weekly ' + my_date

if bot:
    send_message_to_symphony(subject, body, web_url)
