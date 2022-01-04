import sys
import os
from github import Github
from datetime import datetime
from datetime import timedelta
from slack_sdk import WebClient

def check_len(issue_bugs, issue_non_bugs, this_week, week_ago):
    if this_week:
        message_time = 'this week'
        query_non_bug = f'?q=is%3Aopen+is%3Aissue+created%3A%3D%3E{week_ago}+-label%3Abug+'
        query_bug = f'?q=is%3Aopen+is%3Aissue+created%3A%3D%3E{week_ago}+label%3Abug+'
        emoji = ':warning:'
        emoji_bug = ':bug:'
    else:
        message_time = 'more than one week ago'
        query_non_bug = f'?q=is%3Aopen+is%3Aissue+created%3A%3C{week_ago}+-label%3Abug+'
        query_bug = f'?q=is%3Aopen+is%3Aissue+created%3A%3C{week_ago}+label%3Abug+'
        emoji = ':rotating_light:'
        emoji_bug = ':ladybug:'
        
    message = ''
    if len(issue_non_bugs) > 1:
        issues_link = '/'.join(issue_non_bugs[0].html_url.split('/')[:-1])
        message += f"        {emoji} {len(issue_non_bugs)} <{issues_link}{query_non_bug} |non-bug issues> were opened {message_time}\n"
    elif len(issue_non_bugs) == 1:
        issues_link = '/'.join(issue_non_bugs[0].html_url.split('/')[:-1])
        message += f"        {emoji} Just one <{issues_link}{query_non_bug} |non-bug issue> was opened {message_time}. Almost there!\n"
    elif len(issue_non_bugs) == 0 and not this_week:
        pass

    if len(issue_bugs) > 1:
        issues_link = '/'.join(issue_bugs[0].html_url.split('/')[:-1])
        message += f"        {emoji_bug} {len(issue_bugs)} <{issues_link}{query_bug}|bug issues> were opened {message_time}\n"
    elif len(issue_bugs) == 1:
        issues_link = '/'.join(issue_bugs[0].html_url.split('/')[:-1])
        message += f"        {emoji_bug} Just one <{issues_link}{query_bug}|bug issue> was opened {message_time}. Almost there!\n"
    elif len(issue_bugs) == 0 and not this_week:
        pass
    elif len(issue_bugs) == 0 and len(issue_non_bugs) == 0:
        message += f'        :white_check_mark: No issues this week. Bravo!\n'

    return message

def create_messages_issue(current_bugs, current_non_bugs, late_bugs, late_non_bugs, week_ago):
    message = check_len(current_bugs, current_non_bugs, True, week_ago)
    message += check_len(late_bugs, late_non_bugs, False, week_ago)
    return message

def create_messages_pr(prs, repo, n):
    if n > 0:
        new_line = ''
    else:
        new_line = '\n'
    html = '/'.join(prs[0].html_url.split('/')[:-1])
    if len(prs) > 1:
        message = f'*{repo}* has {len(prs)} open <{html}|PR(s)> {new_line}'
    elif len(prs) == 1:
        message = f'*{repo}* has just one open <{html}|PR(s)> {new_line}'
    return message


slack_token = sys.argv[1]
git_token = sys.argv[2]
repo = sys.argv[3]

client = WebClient(slack_token)
g = Github(git_token)
channel_id = "C02GMMQUQ56"  # Content Operation
# channel_id = "C02MBCYLF08" # Test Channel
current_nonbugs = []
current_bugs = []
late_nonbugs = []
late_bugs = []
today = datetime.now()
week_ago = datetime.strftime(today - timedelta(days=7), '%Y-%m-%d')
prs = []

for n, issue in enumerate(g.get_user().get_repo(repo).get_issues(state='open')):
    if issue.pull_request:
        prs.append(issue)
        continue
    diff = (today - issue.created_at).days
    if diff > 7:
        if 'bug' in [label.name for label in issue.labels]:
            late_bugs.append(issue)
        else:
            late_nonbugs.append(issue)
    else:
        if 'bug' in [label.name for label in issue.labels]:
            current_bugs.append(issue)
        else:
            current_nonbugs.append(issue)

# Check issues without considering PRs
n = len(current_nonbugs) + \
    len(current_bugs) + \
    len(late_nonbugs) + \
    len(late_bugs)

# Initialize message with the PRs
message = ''
if len(prs) > 0:
    message += create_messages_pr(prs, repo, n)


# Update the message with the issues
if n > 1:
    if len(prs) > 0:
        message += f'and {n} issues\n'
        message += create_messages_issue(current_bugs, current_nonbugs, late_bugs, late_nonbugs, week_ago)
    else:
        message += f'*{repo}* has {n} issues\n'
        message += create_messages_issue(current_bugs, current_nonbugs, late_bugs, late_nonbugs, week_ago)
elif n == 1:
    if len(prs) > 0:
        message += f'and just one issue\n'
        message += create_messages_issue(current_bugs, current_nonbugs, late_bugs, late_nonbugs, week_ago)
    else:
        message += f'*{repo}* has just one issue \n'
        message += create_messages_issue(current_bugs, current_nonbugs, late_bugs, late_nonbugs, week_ago) 

if len(prs) + n > 0:
    result = client.chat_postMessage(
                        channel=channel_id,
                        text=message)
