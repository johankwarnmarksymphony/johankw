import sys
import requests
import json
from datetime import datetime, timedelta

NEW_LINE = '<br/>\n'
BOLD = '<b>'
BOLD_RESET = '</b>'

###
###
###
def usage():
    print('')
    print('  python ' + sys.argv[0] + ' <webhook url>')
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
def get_yesterday():
    d = datetime.now() - timedelta(days=1)
    my_date = d.strftime("%Y%m%d%H00")

    print('get_yesterday, my_date: ' + my_date)

    return my_date

#################################################

print('qqqqqq')

if len(sys.argv) == 1:
    web_url = ''
elif len(sys.argv) == 2:
    web_url = sys.argv[1]
else:
    usage()

print('wwwww')

yesterday = get_yesterday()

print('yesterday: ' + yesterday)

now = datetime.now()
my_date = now.strftime("%Y-%m-%d %H:%M")

print('https://github.com/SymphonyOSF/SFE-Lite/commits?since=' + yesterday)
body = ''


subject = 'SFE-Lite changes ' + my_date

body += '  ' + create_link('https://github.com/SymphonyOSF/SFE-Lite/commits?since=' + yesterday) + NEW_LINE

print('body: ' + body)

send_message_to_symphony(subject, body, web_url)

