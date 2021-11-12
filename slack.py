import sys
import os
from github import Github
from datetime import datetime
from slack_sdk import WebClient

def check_len(issue, this_week):
    if this_week:
        message_time = 'this week'
    else:
        message_time = 'more than one week ago'
        
    message = ''
    if len(issue) > 0:
        issues_link = '/'.join(issue[0].html_url.split('/')[:-1])
        message += f"    {len(issue)} <{issues_link}|issues> were opened {message_time}\n"
    elif len(issue) == 0 and not this_week:
        pass
    else:
        message += f'    No issues were opened {message_time}\n'

    return message

def create_messages(n, repo, current, late):
    message = f'There are {n} issue(s) in {repo} \n'
    message += check_len(current, True)
    message += check_len(late, False)
    return message


slack_token = sys.argv[1]
git_token = sys.argv[2]
repo = sys.argv[3]

client = WebClient(slack_token)
g = Github(git_token)
channel_id = "C02GMMQUQ56"  # Content Operation
# channel_id = "C02MBCYLF08" # Test Channel
current = []
late = []
today = datetime.now()
prs = 0

for n, issue in enumerate(g.get_user().get_repo(repo).get_issues(state='open')):
    if issue.pull_request:
        prs += 1 
        continue
    diff = (today - issue.created_at).days
    if diff > 7:
        late.append(issue)
    else:
        current.append(issue)

n = len(current) + len(late)
if n > 0:
    message = create_messages(n, repo, current, late)
else:
    message = f'No issues found in {repo}'

result = client.chat_postMessage(
                    channel=channel_id,
                    text=message)
