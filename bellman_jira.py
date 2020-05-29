import sys
import requests
import json
import time
import datetime
import humanfriendly
from jira import JIRA, JIRAError

NEW_LINE = '<br/>\n'

###
### Check day, Monday->72, Tuesday-Friday 24 Saturday-Sunday 0
### Call jira to get the list
### Send the list with websocket to Symphony
###
###



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
def init_jira(user, apikey):
    # Connect to JIRA
    server = 'https://perzoinc.atlassian.net'

    options = {
        'server': server
    }

    return JIRA(options, basic_auth=(user, apikey))

###
###
###
def print_ticket(x):
    summary = str(x.fields.summary).replace('\uff0e', '.') .replace('\u2019', '\'')

    return '  ' + '{:15}'.format(str(x.fields.status)) + ' <a href=\"https://perzoinc.atlassian.net/browse/' + str(x) + '\" /> ' + summary + NEW_LINE


###
###
###
def get_new_bugs(jira, jira_project, days):
    jql = 'project = ' + jira_project + ' AND type = Bug AND createdDate >= -' + str(days) + 'd ORDER BY createdDate'

    #print('====> JQL: ' + jql)

    tickets = jira.search_issues(jql, maxResults=None)

    number_of_total = 0
    number_of_done = 0
    number_of_open = 0

    for x in tickets:
        number_of_total += 1

        if str(x.fields.status) == 'Done':
            number_of_done += 1
        elif str(x.fields.status) == 'Open':
            number_of_open += 1

    print('')

    subject = 'New bugs open last ' + str(days) + 'days ' + '(' + str(len(tickets)) + ')' + ' open=' + str(number_of_open) + ' done=' + str(number_of_done) + ' others=' + str(number_of_total - number_of_open - number_of_done)

    body_text = ''
    for x in tickets:
        body_text += print_ticket(x)

    return [subject, body_text]


###
###
###
def get_number_of_tickets(jira, jira_project, jql):
    jql = 'project = ' + jira_project + ' AND ' + jql

    tickets = jira.search_issues(jql, maxResults=None)

    return len(tickets)


###
###
###
def get_bug_stats(jira, jira_project, days):
    number_of_bugs = get_number_of_tickets(jira, jira_project, 'type = Bug and status != done ORDER BY priority DESC')

    number_of_new_bugs = get_number_of_tickets(jira, jira_project, 'type = Bug and createdDate >= -' + str(days)  + 'd ORDER BY priority DESC')

    number_of_done_bugs = get_number_of_tickets(jira, jira_project, 'type = Bug and status CHANGED TO done after -' + str(days) + 'd ORDER BY createdDate')

    text =  '  Total number of bugs: ' + str(number_of_bugs) + NEW_LINE
    text += '  New bugs last ' + str(days) + 'days : ' + str(number_of_new_bugs) + NEW_LINE
    text += '  Done bugs last ' + str(days) + 'days: ' + str(number_of_done_bugs) + NEW_LINE

    return text

###
###
###
def send_message_to_symphony(subject, body, webhook):
    data = '<messageML><b>' + subject + '</b>' + NEW_LINE + body + '</messageML>'

    print('data: ' + data)

    if webhook == '':
        return

    r = requests.post(webhook, data=data)

    print('r: ' + str(r))
    print('r.status_code: ' + str(r.status_code))


###
###
###
def send(days, jira_project, webhook):
    [subject, body_text] = get_new_bugs(jira, jira_project, days)
    
    if days >= 7:
        body_text += '------------------------' + NEW_LINE
        body_text += get_bug_stats(jira, jira_project, days)

    print('subject: ' + subject)
    print('body_text: ' + body_text)

    send_message_to_symphony(subject, body_text, webhook)


####################################################

print('beginning of bellman_jira.py')

day = datetime.datetime.today().weekday()

print('argc: ' + str(len(sys.argv)))
print('argv[1]: ' + sys.argv[1])
print('argv[2]: ' + sys.argv[2])
print('argv[3]: ' + sys.argv[3])

if len(sys.argv) > 4:
    print('argv[4]: ' + sys.argv[4])
    webhook_sda = sys.argv[4]
else:
    webhook_sda = ''

if len(sys.argv) > 5:
    print('argv[5]: ' + sys.argv[5])
    webhook_rtc = sys.argv[5]
else:
    webhook_rtc = ''

jira = init_jira(sys.argv[2], sys.argv[3])

if sys.argv[1] == 'daily':
    if day == 0:
        # Monday
        print('Ask for 72h')
    
        # Send for SDA
        send(3, 'sda', webhook_sda)

        time.sleep(5)

        # Send for RTC
        send(3,  'rtc', webhook_rtc)

    elif day == 1 or day == 2 or day == 3 or day == 4:
        print('Ask for 24h')

        # Send for SDA
        send(1, 'sda', webhook_sda)

        time.sleep(5)

        # Send for RTC
        send(1, 'rtc', webhook_rtc)
    else:
        print('Weekend')
elif sys.argv[1] == 'weekly':
    # Send for SDA
    send(7, 'sda', webhook_sda)

    time.sleep(5)

    # Send for RTC
    send(7,  'rtc', webhook_rtc)
else:
    print('Error sys.argv[1]: ' + sys.argv[1])


