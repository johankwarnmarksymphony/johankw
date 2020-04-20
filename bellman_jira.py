import sys
import requests
import json
import time
import datetime
import humanfriendly
from jira import JIRA, JIRAError


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
    if str(x.fields.status) == 'Done':
        return '  ' + '{:15}'.format(str(x.fields.status)) + ' https://perzoinc.atlassian.net/browse/' + str(x) + ' ' + str(x.fields.summary) + '<br/>'
    elif str(x.fields.status) == 'Open':
        return '  ' + '{:15}'.format(str(x.fields.status)) + ' <a href=\"https://perzoinc.atlassian.net/browse/' + str(x) + '\" /> ' + str(x.fields.summary) + '<br/>'
    else:
        return '  ' + '{:15}'.format(str(x.fields.status)) + ' https://perzoinc.atlassian.net/browse/' + str(x) + ' ' + str(x.fields.summary) + '<br/>'


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
#    data = '<messageML> \
#This is an example of the sort of text that you can fit within the Universal Webhook Integration. Your service can post updates here!<br/>\
#<b>You can also bold me</b>: Or not.<br/>\
#<b>You can submit links as well: </b><a href="https://google.com" /><br/>\
#<i>You can make text render in italic font</i><br/>\
#Labels can also come through: <hash tag="label"/> and you can make tickers appear too: <cash tag="GOOG"/><br/>\
#You can directly mention people using email matching: <mention email="vincent@symphony.com"/><br/>\
#You can send lists too:<br/>\
#<ul><li>item1</li><li>item2</li></ul><br/>\
#You can even send tables:<br/>\
#<table><tr><td>header1</td><td>header2</td></tr><tr><td>info1</td><td>info2</td></tr><tr><td>info1</td><td>info2</td></tr><tr><td>info1</td><td>info2</td></tr></table>\
#</messageML>'

def send_message_to_symphony(subject, body, webhook):
    data = '<messageML><b>' + subject + '</b><br/>' + body + '</messageML>'

    print('data: ' + data)

    r = requests.post(webhook, data=data)

    print('r: ' + str(r))
    print('r.status_code: ' + str(r.status_code))


###
###
###
def send(days, webhook):
    [subject, body_text] = get_new_bugs(jira, 'sda', days)
    
    print('subject: ' + subject)
    print('body_text: ' + body_text)

    send_message_to_symphony(subject, body_text, webhook)


####################################################

day = datetime.datetime.today().weekday()

print('argc: ' + str(len(sys.argv)))
print('argv[1]: ' + sys.argv[1])
print('argv[2]: ' + sys.argv[2])

jira = init_jira(sys.argv[1], sys.argv[2])

if day == 0:
    # Monday
    print('Ask for 72h')
    send(3, sys.argv[3])
elif day == 1 or day == 2 or day == 3 or day == 4:
    print('Ask for 24h')
    send(1, sys.argv[3])
else:
    print('Weekend')

