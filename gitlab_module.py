import argparse
import gitlab
import json
import re
import logging
import difflib
import base64


class GitLabManager:
    def __init__(self, url, token, project_id, tasks):
        """Initializes the GitLabManager with the necessary configuration."""
        try:
            self.gl = gitlab.Gitlab(url=url, private_token=token)
            self.gl.auth()
            logging.info("Successfully connected to GitLab.")
        except gitlab.exceptions.GitlabAuthenticationError as e:
            logging.error(f"GitLab authentication failed: {e}")
            self.gl = None
            self.project = None
            return
        except Exception as e:
            logging.error(f"An error occurred while connecting to GitLab: {e}")
            self.gl = None
            self.project = None
            return

        try:
            self.project = self.gl.projects.get(project_id)
            logging.info(f"Accessed GitLab project: {self.project.name}")
        except gitlab.exceptions.GitlabGetError as e:
            logging.error(f"Failed to get GitLab project: {e}")
            self.project = None
        except Exception as e:
            logging.error(f"An error occurred while accessing the GitLab project: {e}")
            self.project = None

        self.tasks = tasks

    def create_branch(self, branch_name, ref_branch='master'):
        """Creates a new branch from the specified reference branch. If the branch exists, reset it to ref_branch."""
        try:
            branch = self.project.branches.get(branch_name)
            # Delete and recreate the branch from ref_branch
            branch.delete()
            logging.info(f"Branch '{branch_name}' deleted.")
        except gitlab.exceptions.GitlabGetError:
            # Branch does not exist, proceed to create it
            pass

        # Create the branch from ref_branch
        self.project.branches.create({'branch': branch_name, 'ref': ref_branch})
        logging.info(f"Branch '{branch_name}' successfully created from '{ref_branch}'.")

    def get_file_content(self, file_path, branch_name):
        """Retrieves the content of the specified file from the project."""
        try:
            file = self.project.files.get(file_path=file_path, ref=branch_name)
            content = base64.b64decode(file.content).decode('utf-8')
            logging.info(f"Retrieved file '{file_path}' from branch '{branch_name}'.")
            return content
        except gitlab.exceptions.GitlabGetError as e:
            logging.error(f"Failed to retrieve file: {e}")
            return None
        except Exception as e:
            logging.error(f"Error retrieving file: {e}")
            return None

    def modify_project(self, content, project_keyword, cpu, ram):
        """Modifies the cores and ram values for a project without altering the whitespace around the equal sign."""
        if project_keyword == 'ml':
            project_keyword = 'machinelearning'

        project_pattern = rf'(?ms)(name\s*=\s*"[^"]*{project_keyword}[^"]*".*?cores(\s*)=(\s*)(\d+).*?ram(\s*)=(\s*)(\d+))'

        def update_cores_ram(match):
            original_block = match.group(1)
            cores_before_equals = match.group(2)  # Capture whitespace before cores' equal sign
            cores_after_equals = match.group(3)   # Capture whitespace after cores' equal sign
            current_cores = int(match.group(4))

            ram_before_equals = match.group(5)    # Capture whitespace before ram's equal sign
            ram_after_equals = match.group(6)     # Capture whitespace after ram's equal sign
            current_ram = int(match.group(7))

            new_cores = current_cores + int(cpu)
            new_ram = current_ram + int(ram)

            # Replace only the numbers, preserving whitespace around equal signs
            modified_block = re.sub(
                r'cores(\s*)=(\s*)\d+', 
                f"cores{cores_before_equals}={cores_after_equals}{new_cores}", 
                original_block
            )
            modified_block = re.sub(
                r'ram(\s*)=(\s*)\d+', 
                f"ram{ram_before_equals}={ram_after_equals}{new_ram}", 
                modified_block
            )

            logging.info(f"Modified project matching '{project_keyword}' with CPU +{cpu} and RAM +{ram}.")
            return modified_block

        modified_content = re.sub(project_pattern, update_cores_ram, content)
        if modified_content == content:
            logging.warning(f"No matching project found or modified for keyword '{project_keyword}'.")
        return modified_content

    def commit_changes(self, file_path, original_content, modified_content, branch_name, commit_message):
        """Commits the modified content back to the specified branch."""
        try:
            # Ensure content is properly formatted as a string
            if not isinstance(modified_content, str):
                modified_content = str(modified_content)
            modified_content = modified_content.encode('utf-8').decode('utf-8')

            logging.info(f"Committing to branch '{branch_name}' with file path '{file_path}' with message: '{commit_message}'")

            # Log differences between original and modified content
            diff = difflib.unified_diff(
                original_content.splitlines(),
                modified_content.splitlines(),
                fromfile='original',
                tofile='modified',
                lineterm=''
            )
            diff_text = '\n'.join(diff)
            logging.info(f"Differences between original and modified content:\n{diff_text}")

            # Use the pre-initialized commit message
            self.project.commits.create({
                'branch': branch_name,
                'commit_message': commit_message,
                'actions': [
                    {
                        'action': 'update',
                        'file_path': file_path,
                        'content': modified_content
                    }
                ]
            })
            logging.info(f"Changes committed to branch '{branch_name}'.")

        except gitlab.exceptions.GitlabCreateError as e:
            logging.error(f"Failed to commit changes: {e} - This may be due to custom hooks or branch protection rules.")
        except TypeError as e:
            logging.error(f"TypeError occurred: {e} - Ensure all commit parameters match GitLab API requirements.")
        except Exception as e:
            logging.error(f"An error occurred while committing the changes: {e} ({type(e)})")

    def create_merge_request(self, branch_name, commit_message):
        """Creates or updates a merge request with the correct title."""
        try:
            existing_mrs = self.project.mergerequests.list(
                source_branch=branch_name, target_branch='master', state='opened'
            )

            if existing_mrs:
                existing_mr = existing_mrs[0]
                if existing_mr.title != commit_message:
                    logging.info(
                        f"Updating MR title from '{existing_mr.title}' to '{commit_message}'."
                    )
                    existing_mr.title = commit_message
                    existing_mr.save()
                else:
                    logging.info(f"Merge Request with title '{commit_message}' already exists.")
            else:
                mr = self.project.mergerequests.create({
                    'source_branch': branch_name,
                    'target_branch': 'master',
                    'title': commit_message
                })
                logging.info(f"Merge Request created: {mr.web_url}")

        except gitlab.exceptions.GitlabCreateError as e:
            logging.error(f"Failed to create or update Merge Request: {e}")
        except Exception as e:
            logging.error(f"Error creating or updating Merge Request: {e}")

    def load_tasks(self):
        """Loads task data from the provided list."""
        try:
            self.task_keys = sorted([task['key'] for task in self.tasks])
            logging.info(f"Loaded tasks: {self.tasks}")
            return self.tasks
        except Exception as e:
            logging.error(f"Failed to load tasks: {e}")
            return []

    def process_tasks(self):
        """Processes each task: creates a branch, modifies files, commits changes, and creates a merge request."""
        if self.project is None:
            logging.error("GitLab project is not initialized. Exiting process_tasks.")
            return

        for task in self.tasks:
            branch_name = f"quotas_auto_{task['key']}"

            # Create or reset the branch from 'master'
            self.create_branch(branch_name, 'master')

            project_file_path = f"{task['openstack']}/admin/projects.tf"
            commit_message = f"chore: Update quotas for {task['key']}"

            # Get the content from the branch
            original_content = self.get_file_content(project_file_path, branch_name)
            if original_content is None:
                continue

            modified_content = self.modify_project(
                original_content,
                task['project'],
                task['cpu'],
                task['ram']
            )

            if modified_content == original_content:
                logging.info(f"No changes made to '{project_file_path}' for task '{task['key']}'.")
                continue

            # Commit changes to the task-specific branch
            self.commit_changes(
                file_path=project_file_path,
                original_content=original_content,
                modified_content=modified_content,
                branch_name=branch_name,
                commit_message=commit_message
            )

            # Create a merge request to 'master'
            self.create_merge_request(branch_name, commit_message)


def main():
    parser = argparse.ArgumentParser(
        description='Modify CPU and RAM in GitLab project configuration based on input data.'
    )
    parser.add_argument('-gu', '--url', required=True, help='GitLab URL (e.g., https://gitlab.com)')
    parser.add_argument('-gt', '--token', required=True, help='GitLab personal access token')
    parser.add_argument(
        '-gp', '--project_id', required=True,
        help='GitLab project ID or full path (e.g., namespace/project)'
    )
    parser.add_argument('-gd', '--data', required=True, help='Path to JSON file with task data')

    args = parser.parse_args()

    with open(args.data, 'r') as file:
        tasks = json.load(file)

    manager = GitLabManager(args.url, args.token, args.project_id, tasks)
    manager.process_tasks()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()