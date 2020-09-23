import sys
import requests
import json
import time
import datetime
import humanfriendly
from jira import JIRA, JIRAError

NEW_LINE   = '<br/>\n'
BOLD       = '<b>'
BOLD_RESET = '</b>'

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
def get_jira(jira, jira_project, jql):
    jql = 'project = ' + jira_project + ' AND ' + jql

    #print('jql: ' + jql)

    tickets = jira.search_issues(jql, maxResults=None)

    subject_text = 'Open E2E testing bugs (' + str(len(tickets)) + ')'

    body_text = ''
    for x in tickets: 
        #print('assignee: ' + str(x.fields.assignee))
        body_text += '  ' + '{:15}'.format(str(x.fields.status)) + '{:15}'.format(str(x.fields.assignee)) + ' <a href=\"https://perzoinc.atlassian.net/browse/' + str(x) + '\" /> ' + x.fields.summary + NEW_LINE

    return [subject_text, body_text]


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


if len(sys.argv) == 4:
    jira_user  = sys.argv[1]
    jira_token = sys.argv[2] 
    webhook    = sys.argv[3]
elif len(sys.argv) == 3:
    jira_user  = sys.argv[1]
    jira_token = sys.argv[2] 
    webhook    = ''
else:
    usage()
    sys.exit(37)

jira = init_jira(jira_user, jira_token)

[subject_text, body_text] = get_jira(jira, 'c2', 'project = \"C2\" and labels = \"c2-e2e-test-fail\" and status != done ORDER BY created DESC')

print('subject_text: ' + subject_text)
print('body_text: ' + body_text)

if webhook:
    send_message_to_symphony(subject_text, body_text, webhook)

