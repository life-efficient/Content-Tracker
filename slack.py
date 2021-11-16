import sys
import os
from github import Github
from datetime import datetime
from datetime import timedelta
from slack_sdk import WebClient

def check_len(issue, this_week, week_ago):
    if this_week:
        message_time = 'this week'
        query = f'?q=is%3Aissue+is%3Aopen+created%3A%3E{week_ago}+'
    else:
        message_time = 'more than one week ago'
        query = f'?q=is%3Aissue+is%3Aopen+created%3A%3C{week_ago}'
        
    message = ''
    if len(issue) > 1:
        issues_link = '/'.join(issue[0].html_url.split('/')[:-1])
        message += f"    {len(issue)} <{issues_link}{query}|issues> were opened {message_time}\n"
    elif len(issue) == 1:
        issues_link = '/'.join(issue[0].html_url.split('/')[:-1])
        message += f"    Just one <{issues_link}{query}|issue> was opened {message_time}\n"
    elif len(issue) == 0 and not this_week:
        pass
    else:
        message += f'    No issues were opened {message_time}\n'

    return message

def create_messages(current, late, week_ago):
    message = check_len(current, True, week_ago)
    message += check_len(late, False, week_ago)
    return message

def create_messages_pr(prs, repo):
    html = '/'.join(prs[0].html_url.split('/')[:-1])
    if len(prs) > 1:
        message = f'There are {len(prs)} <{html}|PR(s)> in {repo} \n'
    elif len(prs) == 1:
        message = f'Just one <{html}|PR(s)> in {repo}. You can do it guys!\n'
    return message


slack_token = sys.argv[1]
git_token = sys.argv[2]
repo = sys.argv[3]

client = WebClient(slack_token)
g = Github(git_token)
# channel_id = "C02GMMQUQ56"  # Content Operation
channel_id = "C02MBCYLF08" # Test Channel
current = []
late = []
today = datetime.now()
week_ago = datetime.strftime(today - timedelta(days=7), '%Y-%m-%d')
prs = []

for n, issue in enumerate(g.get_user().get_repo(repo).get_issues(state='open')):
    if issue.pull_request:
        prs.append(issue)
        continue
    diff = (today - issue.created_at).days
    if diff > 7:
        late.append(issue)
    else:
        current.append(issue)

# Initialize message with the PRs
message = ''
if len(prs) > 0:
    message += create_messages_pr(prs, repo)

# Check issues without considering PRs
n = len(current) + len(late)

# Update the message with the issues
if n > 1:
    message += f'There are {n} issues in {repo} \n'
    message += create_messages(current, late, week_ago)
elif n == 1:
    message += f'There is just one issue in {repo} \n'
    message += create_messages(current, late, week_ago) 

if len(prs) + n > 0:
    result = client.chat_postMessage(
                        channel=channel_id,
                        text=message)
