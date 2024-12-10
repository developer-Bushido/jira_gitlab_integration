import argparse
import logging
import os
from gitlab_module import GitLabManager
from jira_module import JiraManager


def main():
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Automate task management between Jira and GitLab.')
    
    # Required arguments
    parser.add_argument('-jt', '--jira_token', default=os.environ.get('JIRA_TOKEN'), help='JIRA access token')
    parser.add_argument('-jl', '--jira_login', default=os.environ.get('JIRA_LOGIN'), help='JIRA login')
    parser.add_argument('-ju', '--jira_url', default=os.environ.get('JIRA_URL'), help='JIRA base URL')
    parser.add_argument('-jj', '--jira_jql', default=os.environ.get('JIRA_QUERY'), help='JIRA query filter')
    parser.add_argument('-gt', '--gitlab_token', default=os.environ.get('GITLAB_TOKEN'), help='GitLab access token')
    parser.add_argument('-gu', '--gitlab_url', default=os.environ.get('GITLAB_URL'), help='GitLab base URL')
    parser.add_argument('-gp', '--gitlab_project', default=os.environ.get('GITLAB_PROJECT'), help='GitLab project ID')
    
    # Parse arguments
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Initialize JiraManager with provided arguments
    jira_manager = JiraManager(
        url=args.jira_url,
        login=args.jira_login,
        token=args.jira_token,
        jql=args.jira_jql
    )
    
    # Fetch and filter issues from Jira
    tasks = jira_manager.process_issues()

    # Check if tasks are available
    if not tasks:
        logging.info("No tasks found to process from Jira.")
        return

    # Initialize GitLabManager with the tasks from Jira
    gitlab_manager = GitLabManager(
        url=args.gitlab_url,
        token=args.gitlab_token,
        project_id=args.gitlab_project,
        tasks=tasks
    )

    # Process tasks through GitLab workflow
    gitlab_manager.process_tasks()


if __name__ == '__main__':
    main()