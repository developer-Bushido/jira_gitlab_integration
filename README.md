
# Automation Script for Jira and GitLab Integration

This project provides an automated way to fetch issues from Jira and update project configurations in GitLab based on those issues. The application is written in **Python** and runs inside a Docker container using Docker Compose.

## Prerequisites

- **Docker** installed on your machine
- **Docker Compose** installed
- Access to Jira and GitLab APIs with appropriate permissions
- Environment variables set for sensitive information

## Installation and Setup

1. **Create a `.env` file:**

   Create a file named `.env` in the root directory of the project to store your sensitive environment variables.

   ```bash
   JIRA_TOKEN=your_jira_api_token
   JIRA_LOGIN=your_jira_username
   GITLAB_TOKEN=your_gitlab_personal_access_token
   ```

   **Note:** Do not commit this file to version control as it contains sensitive information.

2. **Review and customize the `docker-compose.yml` file (optional):**

   If needed, you can adjust the settings in `docker-compose.yml`. By default, it is set up to build and run the application using the provided `Dockerfile`.

## Usage

### Running the Application

The application integrates Jira and GitLab. It fetches tasks from Jira and uses them to modify project configurations in GitLab.

#### Command:

To build and run the application in detached mode, use:

   ```bash
   docker-compose up --build -d
   ```

This command will:

- Build the Docker image using the `Dockerfile`.
- Start the container as defined in `docker-compose.yml`.
- Run the application inside the container.

#### Stopping the Application:

To stop and remove the running container and network, use:

   ```bash
   docker-compose down
   ```

### Verifying the Application

To check the logs and verify that the application is running correctly:

   ```bash
   docker-compose logs -f
   ```

### Accessing the Container (Optional)

If you need to access the running container for debugging purposes:

   ```bash
   docker-compose exec app bash
   ```

This will open a bash shell inside the container.

## Environment Variables

The application requires the following environment variables to be set, either in the `.env` file or directly in the environment:

- `JIRA_TOKEN`: Your Jira API token.
- `JIRA_LOGIN`: Your Jira username or email address.
- `JIRA_URL`: The base URL of your Jira instance.
- `JIRA_QUERY`: The JQL query to filter issues.
- `GITLAB_TOKEN`: Your GitLab Personal Access Token.
- `GITLAB_URL`: The base URL of your GitLab instance.
- `GITLAB_PROJECT`: The ID of your GitLab project.

These variables are used by the application to authenticate with Jira and GitLab APIs.

## Configuration

### `docker-compose.yml`

The `docker-compose.yml` file defines the service and network configurations.

### `Dockerfile`

The `Dockerfile` defines the environment and dependencies for the application.

## Application Structure

- `main.py`: The main entry point of the application.
- `jira_module.py`: Contains code related to Jira interactions.
- `gitlab_module.py`: Contains code related to GitLab interactions.
- `requirements.txt`: Lists the Python dependencies.
- `Dockerfile`: Defines the Docker image build process.
- `docker-compose.yml`: Defines the Docker Compose services and network.

## Logging

The application uses logging to provide detailed feedback on the execution process, helping you track and debug the workflow. Logs are printed to the console and can be viewed using `docker-compose logs`.

## Troubleshooting

- **Authentication Errors:**

  Ensure that your API tokens and login credentials are correct and have the necessary permissions.

- **Network Issues:**

  If the application cannot connect to Jira or GitLab, ensure that the container has network access. The `docker-compose.yml` file includes a custom network to avoid IP conflicts.

## Additional Notes

- **Security:**

  Be cautious with sensitive information. Do not commit API tokens or credentials to version control.

- **Customizing Environment Variables:**

  You can override any of the default environment variables by modifying the `docker-compose.yml` file or by setting them in the `.env` file.
