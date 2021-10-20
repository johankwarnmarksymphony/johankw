import sys
import requests
import json
from datetime import datetime

NEW_LINE = '<br/>\n'
BOLD = '<b>'
BOLD_RESET = '</b>'

###
###
###
def usage():
    print('')
    print('  python ' + sys.argv[0] + ' <domoClientId> <domoClientSecret>')
    print('')
    print('  (' + str(sys.argv) + ')')
    print('')

    sys.exit(3)


###
###
###
def create_link(link):
    return '<a href=\"' + link + '\" />'


###
###
###
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
def domoAuthenticate(domoAuthURL, domoClientId, domoClientSecret):
    r = requests.get(domoAuthURL, auth=(domoClientId, domoClientSecret))

    print('domoAuthenticate, r.text: ' + r.text)

    access_token = json.loads(r.text)["access_token"]

    print('domoAuthenticate, access_token: ' + access_token)

    return access_token
   

###
###
###
def queryDataSet(data_id, sql, access_token):
    url = "https://api.domo.com/v1/datasets/query/execute/" + data_id

    payload = {
        'sql': sql
    }

    headers = {
        'Content-Type': "application/json",
        'Authorization': "Bearer " + access_token
    }

    retryCount = 0
    got_result = False

    while retryCount < 5 and got_result == False:
        response = requests.request("POST", url, json=payload, headers=headers)

        print('response.status_code: ' + str(response.status_code))

        output = json.loads(response.text)

        if 'rows' not in output:
            print('queryDataSet: rows not in output')
            print('queryDataSet: rows not in output')
            print('queryDataSet: Retry Count - {str(retryCount)}')
            print('{str(response.status_code)} - {response.text}')

            if 'error' in output and output['error'] == 'invalid_token':
                print('queryDataSet: Try to reauthenticate')
                print('queryDataSet: Try to reauthenticate')
                #domoSession = domoAuthenticate()

                headers = {
                    'Content-Type': "application/json",
                    'Authorization': "Bearer " + access_token
                }

            retryCount = retryCount + 1
        else:
            got_result = True

    if got_result:
        return output
    else:
        raise Exception('queryDataSet: Fail to get results')


###
###
###
def get_procent(number, total):
    #print('   number: ' + str(number))
    #print('   total : ' + str(total))
    
    #print(' qq ' + '{:2.1f}'.format((number/total)*100) + '%' )

    return '{:2.1f}'.format((number/total)*100) + '%'

#################################################

if len(sys.argv) == 3:
    web_url = ''
elif len(sys.argv) == 4:
    web_url = sys.argv[3]


else:
    usage()

domoClientId = sys.argv[1]

domoClientSecret = sys.argv[2]

access_token = domoAuthenticate('https://api.domo.com/oauth/token?grant_type=client_credentials&scope=data', domoClientId, domoClientSecret)

result = queryDataSet(
    'd300618b-61be-4239-a3e2-2a4b1f0a4a59',
    'SELECT * FROM table ',
    access_token)


print('result: ' + json.dumps(result, indent=2))


rows = result['rows']

application = {}
application['SDA']     = 0
application['Paragon'] = 0
application['Other']   = 0

sda_version = {}
sda_version['14.x'] = 0
sda_version['9.x'] = 0
sda_version['6.x'] = 0
sda_version['3.x'] = 0

for x in rows:
    # print('x: ' + str(x))

    application_name    = x[0].split(' | ')[0]
    number_of_times = x[1]

    #print('application_name: (' + application_name + ')')
    # print('number_of_times: ' + str(number_of_times))

    if number_of_times > 75:
        if application_name == 'SDA':
            application['SDA'] += number_of_times

            application_version =  x[0].split(' | ')[1]

        
            print('application_name   : (' + application_name + ')')
            print('number_of_times    : ' + str(number_of_times))
            print('application_version: (' + application_version + ')')

            if application_version.startswith('3.'):
                sda_version['3.x'] += number_of_times
            elif application_version.startswith('6.'):
                sda_version['6.x'] += number_of_times
            elif application_version.startswith('9.'):
                sda_version['9.x'] += number_of_times
            elif application_version.startswith('14.'):
                sda_version['14.x'] += number_of_times

        elif application_name == 'Paragon':
            application['Paragon'] += number_of_times
        elif application_name == 'Other':
            application['Other'] += number_of_times
        else:
            print('Application name is strange: ' + application_name)

            #sys.exit(5)




total = application['SDA'] + application['Paragon'] + application['Other']


body = ''

now = datetime.now()
my_date = now.strftime("%Y-%m-%d %H:%M")

print('my_date: ' + my_date)

subject = 'SDA adoption  ' + my_date
body += BOLD + '   SDA    : ' + get_procent(application['SDA'], total) + BOLD_RESET + '  (' + str(application['SDA']) + ')' + NEW_LINE
body += '   Paragon: ' + get_procent(application['Paragon'], total) + '  (' + str(application['Paragon']) + ')' + NEW_LINE
body += '   Other  : ' + get_procent(application['Other'], total) + '  (' + str(application['Other']) + ')' + NEW_LINE
body += '-----------------------' + NEW_LINE


total = sda_version['3.x'] + sda_version['6.x'] + sda_version['9.x']

body += '   SDA 3.x : ' + get_procent(sda_version['3.x'], total) + '  (' + str(sda_version['3.x']) + ')' + NEW_LINE
body += '   SDA 6.x : ' + get_procent(sda_version['6.x'], total) + '  (' + str(sda_version['6.x']) + ')' + NEW_LINE
body += BOLD + '   SDA 9.x : ' + get_procent(sda_version['9.x'], total) + BOLD_RESET + '  (' + str(sda_version['9.x']) + ')' + NEW_LINE
body += '   SDA 14.x : ' + get_procent(sda_version['14.x'], total) + '  (' + str(sda_version['14.x']) + ')' + NEW_LINE

body += '-----------------------' + NEW_LINE


body += '   Domo: ' + create_link('https://symphony.domo.com/page/132442628/kpis/details/536445014') + NEW_LINE

print('body: ' + body)

send_message_to_symphony(subject, body, web_url)
