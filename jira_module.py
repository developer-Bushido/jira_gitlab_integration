import argparse
import logging
import json
from jira import JIRA, JIRAError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class JiraManager:
    def __init__(self, url, login, token, jql):
        """
        Initializes the JiraManager with the provided Jira connection details and JQL query.

        :param url: Jira instance URL.
        :param login: User email associated with Jira.
        :param token: API token for access.
        :param jql: JQL query for fetching issues.
        """
        self.url = url
        self.login = login
        self.token = token
        self.jql = jql
        self.jira = None

    def connect_to_jira(self):
        """
        Establishes a connection to Jira.
        """
        try:
            self.jira = JIRA(server=self.url, basic_auth=(self.login, self.token))
            logging.info("Successfully connected to Jira.")
        except JIRAError as e:
            logging.error(f"Failed to connect to Jira: {e}")
            raise

    def fetch_issues_by_jql(self):
        """
        Fetches issues based on the JQL query.

        :return: List of issues.
        """
        try:
            start_at = 0
            max_results = 50
            all_issues = []

            while True:
                issues = self.jira.search_issues(self.jql, startAt=start_at, maxResults=max_results)
                if not issues:
                    break

                all_issues.extend(issues)
                start_at += max_results

            logging.info(f"Found {len(all_issues)} issues for query: {self.jql}.")
            return all_issues
        except JIRAError as e:
            logging.error(f"Error executing JQL query: {e}")
            raise

    def filter_issues(self, issues):
        """
        Filters issues to include only those without comments and description.

        :param issues: List of issues from Jira.
        :return: Filtered list of issue objects.
        """
        filtered_issues = []

        for issue in issues:
            try:
                fields = issue.raw['fields']
                description = fields.get('description')
                comments = issue.fields.comment.total
                openstack_value = fields.get('customfield_13627', {}).get('value', None)
                cpu_value = fields.get('customfield_13637', None)
                ram_value = fields.get('customfield_13638', None)
                projects_affected = fields.get('customfield_13614', [{}])[0].get('value', 'Not specified').split(' ')[0].strip().lower()

                if not description and comments == 0:
                    filtered_issues.append({
                        'key': issue.key,
                        'openstack': openstack_value.split()[0] if isinstance(openstack_value, str) else 'Not specified',
                        'cpu': cpu_value,
                        'ram': ram_value * 1024 if isinstance(ram_value, float) else None,
                        'project': projects_affected
                    })
            except Exception as e:
                logging.error(f"Error processing issue {issue.key}: {e}")
                continue

        return filtered_issues

    def process_issues(self):
        """
        Main process to fetch and filter issues.
        """
        self.connect_to_jira()
        issues = self.fetch_issues_by_jql()
        filtered_issues = self.filter_issues(issues)
        logging.info("Filtered Issues:")
        logging.info(json.dumps(filtered_issues, indent=4, ensure_ascii=False))
        return filtered_issues


def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Fetch issues from Jira using JQL query.')
    parser.add_argument('-ju', '--url', required=True, help='Jira instance URL')
    parser.add_argument('-jt', '--token', required=True, help='Jira API token')
    parser.add_argument('-jl', '--login', required=True, help='Jira user email')
    parser.add_argument('-jj', '--jql', required=True, help='JQL query')

    args = parser.parse_args()

    # Create JiraManager instance and process issues
    jira_manager = JiraManager(args.url, args.login, args.token, args.jql)
    jira_manager.process_issues()


if __name__ == '__main__':
    main()
