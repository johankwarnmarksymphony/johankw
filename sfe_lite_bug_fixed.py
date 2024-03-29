import sys
import requests
import json
import time
import datetime
import humanfriendly
from jira import JIRA, JIRAError

NEW_LINE = '<br/>\n'



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
    summary = str(x.fields.summary).replace('\u201d', '"').replace('\u201c', '"').replace(
        '\uff0e', '.') .replace('\u2019', '\'').replace('\'', '').replace('<', '&lt;')

    mention_text = '<mention email=\"' + x.fields.assignee.emailAddress + '\"/>' 

    return '  ' + mention_text + ' <a href=\"https://perzoinc.atlassian.net/browse/' + str(x) + '\" /> ' + summary + NEW_LINE


###
###
###
def get_newely_fixed_bugs(jira, jira_project, minutes):
    jql = 'project = ' + jira_project + ' AND type = bug and status = done and resolution = Fixed and resolutiondate >= -' + str(minutes) + 'm ORDER BY created DESC'

    print('====> JQL: ' + jql)

    tickets = jira.search_issues(jql, maxResults=None)

    print('get_newely_fixed_bugs, number of fixed: ' + str(len(tickets)))
    str_body = ''
    str_fixed_tickets = ''
    for x in tickets:
        str_fixed_tickets += str(x) + ' '
        str_body += print_ticket(x)

    str_body += ':hearts:' + NEW_LINE
    str_body += 'Powered by: JohanKw' + NEW_LINE

    print('str_fixed_tickets: ' + str_fixed_tickets)
    
    return [len(tickets), str_fixed_tickets, str_body]


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
def send_chime(webhook):
    data = '<messageML><chime /></messageML>'



    if webhook == '':
        return

    r = requests.post(webhook, data=data)

    print('r: ' + str(r))
    print('r.status_code: ' + str(r.status_code))


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


####################################################
print('beginning of sfe_lite_bug_fixed.oy')

print('argc: ' + str(len(sys.argv)))

if len(sys.argv) == 5:
    minutes = sys.argv[1]
    jira_user = sys.argv[2]
    jira_apikey = sys.argv[3]
    webhook = sys.argv[4]

    print('  jira_user: ' + jira_user)
elif len(sys.argv) == 4:
    minutes = sys.argv[1]
    jira_user = sys.argv[2]
    jira_apikey = sys.argv[3]
    webhook = ''

    print('  jira_user: ' + jira_user)
else:
    usage()


jira = init_jira(jira_user, jira_apikey)

[number_of_fixed_tickets, str_fixed_tickets, str_body] = get_newely_fixed_bugs(jira, 'c2', minutes)

if number_of_fixed_tickets != 0:
    # Send message
    print('CHIME, ' + str_fixed_tickets)

    subject = str_fixed_tickets
    body = str_body

    send_chime(webhook)
    send_message_to_symphony(subject, body, webhook)


#send(3, 'sda', webhook_sda)
