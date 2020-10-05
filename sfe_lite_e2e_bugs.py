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

    body_text = '<table>'
    for x in tickets:
        body_text += '<tr>'
        #print('assignee: ' + str(x.fields.assignee))

        #body_text += '  ' + '{:15}'.format(str(x.fields.status)) + '{:25}'.format(str(x.fields.assignee)) + ' <a href=\"https://perzoinc.atlassian.net/browse/' + str(x) + '\" /> ' + x.fields.summary + NEW_LINE
        body_text += '<td>' + str(x.fields.created).split('T')[0] + '</td>'
        body_text += '<td>' + str(x.fields.priority) + '</td>'
        body_text += '<td>' + str(x.fields.status) + '</td>'
        body_text += '<td>' + str(x.fields.assignee) + '</td>'
        body_text += '<td>' + str(x) + '</td>'
        body_text += '<td>' + x.fields.summary + '</td>'
        body_text += '</tr>'
    body_text += '</table>'

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


###
###
###
def create_link(link):
    return '<a href=\"' + link + '\" />'

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

body_text += NEW_LINE
body_text += 'Jira: ' + create_link('https://perzoinc.atlassian.net/issues/?jql=project%20%3D%20c2%20AND%20project%20%3D%20%22C2%22%20and%20labels%20%3D%20%22c2-e2e-test-fail%22%20and%20status%20!%3D%20done%20ORDER%20BY%20created%20DESC') + NEW_LINE

print('subject_text: ' + subject_text)
print('body_text: ' + body_text)





if webhook:
    send_message_to_symphony(subject_text, body_text, webhook)

