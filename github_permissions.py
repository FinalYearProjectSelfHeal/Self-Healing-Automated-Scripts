import requests, logging, os
from dotenv import load_dotenv
from notifications import Notification
from osquery_agent import OSQueryAgent

_LOGGER = logging.getLogger(__name__)


class GitHubPermissions(object):
    def __init__(self):
        """Initialisation function"""
        self.notifications = Notification()
        self.repo_owner = "ProjectLead321"
        self.repo_name = "ProjectRepository"

    def get_github_api(self):
        """Get the GitHub API for looking at repositories and its collaborators.
        :return: f-string with GitHub collaborators API"""
        return f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/collaborators/"

    def add_collaborator(self, username, the_token):
        """Add the GitHub username to the list of collaborators of the project GitHub repository.
        :param username: Username to be added to the repository.
        :param the_token: Personal Access Token from GitHub in order to access privileged API call."""
        api = self.get_github_api()

        headers = {
            "Authorization": f"Bearer {the_token}"
        }

        response = requests.put(api + username, headers=headers)
        if response.status_code == 201:
            notify_text = f"We saw your GitHub account was NOT a collaborator for the {self.repo_name} repository and a new request has been sent."
            self.send_notification(notify_text)
            return True
        elif response.status_code == 404:
            print(f"Collaborator {username} or repository {self.repo_name} has not been found")
            _LOGGER.debug(f"Collaborator {username} or repository {self.repo_name} has not been found")
            return False
        elif response.status_code == 422:
            print(f"User {username} is ALREADY a collaborator to the repository {self.repo_owner}")
            _LOGGER.debug(f"User {username} is ALREADY a collaborator to the repository {self.repo_owner}")
            return True
        else:
            print("Error occured during api call", response.status_code)
            _LOGGER.debug("API call did not work - could not add collaborator. Status Code: " + str(response.status_code))
            return False

    def send_notification(self, info_string):
        """Uses Notification object to send notification to client.
        :param info_string: Text to be displayed in the notification pop-up."""
        self.notifications.create_notification_2(info_string, False)


if __name__ == "__main__":
    """Sequence of instructions for GitHub permissions script."""
    # Load environment variables from .env file
    load_dotenv()
    token = os.getenv("GITHUB_RUNNER_TOKEN")
    # Instantiate objects
    permissions = GitHubPermissions()
    agent = OSQueryAgent()
    # Get name of host client machine
    host_machine = agent.get_computer_hostname()
    # Get corresponding username attached to client machine
    github_username = agent.get_github_username(host_machine)
    # Add a GitHub user to repository as a collaborator
    permissions.add_collaborator(github_username, token)