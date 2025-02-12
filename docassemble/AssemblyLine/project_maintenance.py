# before using, pip install PyGithub
import requests
import json
from typing import List, Optional
from github import Github, UnknownObjectException, Organization
from github.Issue import Issue
from github.Project import Project
from github.Repository import Repository
import argparse
import urllib.parse


from typing import List


def get_package_names(server_name: str) -> List[str]:
    """
    Fetches the JSON file from the given Docassemble server and extracts package names.

    Args:
        server_name (str): Name or IP address of the Docassemble server.

    Returns:
        List[str]: List of package names.
    """
    url = f"https://{server_name}/list?json=1"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        data = response.json()

        # Extract package names
        package_names = [
            interview["package"] for interview in data.get("interviews", [])
        ]
        return package_names

    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return []


def add_tag_to_repos(
    token: str, org_name: str, repo_names: List[str], tag: str
) -> None:
    """
    Adds a specific tag to each repository in the given list.

    Args:
        token (str): GitHub Personal Access Token (PAT) with appropriate permissions.
        org_name (str): Name of the GitHub organization.
        repo_names (List[str]): List of repository names to which the tag will be added.
        tag (str): The tag to be added to the repositories.

    This function iterates through each repository in the provided list, fetching the
    current topics (tags) of the repository. If the specified tag is not already present,
    it adds the tag to the repository. The function includes error handling to catch and
    print any errors that occur while processing each repository.

    Example usage:
        personal_access_token = "YOUR_PERSONAL_ACCESS_TOKEN"
        organization_name = "YourOrgName"
        repositories = ["repo1", "repo2", "repo3"]
        tag_to_add = "your-tag"

        add_tag_to_repos(personal_access_token, organization_name, repositories, tag_to_add)
    """
    # Initialize GitHub
    g = Github(token)

    # Get the organization
    org = g.get_organization(org_name)

    # Iterate through the repositories and add the tag
    for repo_name in repo_names:
        try:
            repo = org.get_repo(repo_name)
            current_topics = repo.get_topics()
            if tag not in current_topics:
                current_topics.append(tag)
                repo.replace_topics(current_topics)
            print(f"Added tag '{tag}' to {repo_name}")
        except Exception as e:
            print(f"Error processing {repo_name}: {e}")


def process_packages_and_add_tag(
    server_name: str, token: str, org_name: str, tag: str
) -> None:
    """
    Fetches package names from a Docassemble server, transforms them into repository names,
    and adds a specified tag to each repository.

    Args:
        server_name (str): Name or IP address of the Docassemble server.
        token (str): GitHub Personal Access Token.
        org_name (str): Name of the GitHub organization.
        tag (str): Tag to be added to each repository.
    """
    package_names = get_package_names(server_name)
    repo_names = [name.replace(".", "-") for name in package_names]

    add_tag_to_repos(token, org_name, repo_names, tag)


def get_project_by_name(token: str, org_name: str, project_name: str) -> Optional[dict]:
    """
    Finds a GitHub Next-Generation project by its name within an organization using GraphQL API.

    Args:
        token (str): GitHub Personal Access Token.
        org_name (str): Name of the GitHub organization.
        project_name (str): Name of the GitHub project.

    Returns:
        dict: The GitHub project object, or None if not found.
    """
    query = """
    query($orgName: String!) {
      organization(login: $orgName) {
        projectsV2(first: 10) {
          nodes {
            id
            title
            url
            number
          }
        }
      }
    }
    """

    variables = {"orgName": org_name}

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    response = requests.post(
        "https://api.github.com/graphql",
        headers=headers,
        json={"query": query, "variables": variables},
    )

    if response.status_code == 200:
        response_json = response.json()
        if "errors" in response_json:
            print("Error in GraphQL query:", response_json["errors"])
            return None
        projects = response_json["data"]["organization"]["projectsV2"]["nodes"]
        for project in projects:
            if project["title"] == project_name:
                return project
        return None
    else:
        print("GraphQL query failed with status code:", response.status_code)
        print("Response:", response.text)
        return None


def get_repos_by_topic(token: str, org_name: str, topic: str) -> List[Repository]:
    """
    Fetches repositories in an organization that have a specific topic.

    Args:
        token (str): GitHub Personal Access Token.
        org_name (str): Name of the GitHub organization.
        topic (str): The GitHub topic to filter repositories by.

    Returns:
        List[Repository]: A list of repository objects that have the specified topic.
    """
    g = Github(token)
    org = g.get_organization(org_name)
    repos_with_topic = []

    for repo in org.get_repos():
        if topic in repo.get_topics():
            repos_with_topic.append(repo)

    return repos_with_topic


def add_issues_and_create_cards(
    token: str,
    org_name: str,
    project_name: str,
    topic: str,
    issue_title: str,
    issue_body: str,
) -> None:
    """
    Adds an issue to each repository with a specific topic and creates a card for each issue in a Next-Generation GitHub project.

    Args:
        token (str): GitHub Personal Access Token.
        org_name (str): Name of the GitHub organization.
        project_name (str): Name of the GitHub project.
        topic (str): The GitHub topic to filter repositories by.
        issue_title (str): Title of the issue.
        issue_body (str): Body of the issue.
    """
    # Step 1: Create issues in the repositories

    repos = get_repos_by_topic(token, org_name, topic)
    issues = {}

    for repo in repos:
        try:
            issue = repo.create_issue(title=issue_title, body=issue_body)
            issues[repo.name] = issue
        except Exception as e:
            print(f"Error adding issue to {repo.name}: {e}")

    # Step 2: Add cards to the Next-Generation Project
    project = get_project_by_name(
        token, org_name, project_name
    )  # This function should return the project's node ID
    if project:
        project_id = project["id"]

        for _, issue in issues.items():
            node_id = issue.url.split("/")[
                -1
            ]  # since graphql node_id isn't exposed in PyGithub try to extract from known format of the URL
            add_issue_to_project(token, project_id, node_id)
    else:
        print(f"Project '{project_name}' not found.")


def find_issues_by_title(
    token: str, org_name: str, repo_names: List[str], issue_title: str
) -> List[str]:
    """
    Finds issues in a list of repositories with a specific title.

    Args:
        token (str): GitHub Personal Access Token.
        org_name (str): Name of the GitHub organization.
        repo_names (list): List of repository names.
        issue_title (str): Title of the issue to be found.

    Returns:
        list: A list of issue node IDs.
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    issue_node_ids = []

    for repo_name in repo_names:
        search_query = f'repo:{repo_name} type:issue in:title "{issue_title}"'
        encoded_query = urllib.parse.quote_plus(search_query)
        search_url = f"https://api.github.com/search/issues?q={encoded_query}"

        try:
            response = requests.get(search_url, headers=headers)
            if response.status_code == 200:
                issues = response.json().get("items", [])
                for issue in issues:
                    issue_node_ids.append(issue["node_id"])
            else:
                print(
                    f"Failed to search in repository '{repo_name}': {response.status_code} {response.text}"
                )

        except Exception as e:
            print(f"Error processing repository '{repo_name}': {e}")

    return issue_node_ids


def add_issue_to_project(token: str, project_id: str, issue_node_id: str) -> None:
    """
    Adds an issue to a Next-Generation GitHub project.

    Args:
        token (str): GitHub Personal Access Token.
        project_id (str): Node ID of the GitHub project.
        issue_node_id (str): Node ID of the GitHub issue.
    """
    # GraphQL mutation to add an issue to the project
    mutation = """
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
        item {
          id
        }
      }
    }
    """

    # Variables for the mutation
    variables = {"projectId": project_id, "contentId": issue_node_id}

    # Set up the request headers
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Make the POST request to the GraphQL API
    response = requests.post(
        "https://api.github.com/graphql",
        headers=headers,
        json={"query": mutation, "variables": variables},
    )

    if response.status_code != 200:
        print("Failed to add issue to project: {}".format(response.text))


def link_issue_title_to_project(
    token: str, org_name: str, project_name: str, topic: str, issue_title: str
) -> None:
    """
    Links issues with a specific title in repositories with a certain topic to a Next-Generation project.

    Args:
        token (str): GitHub Personal Access Token.
        org_name (str): Name of the GitHub organization.
        project_name (str): Name of the GitHub project.
        topic (str): The GitHub topic to filter repositories by.
        issue_title (str): Title of the issue to link.
    """
    # Step 1: Find repositories by topic
    repo_objects = get_repos_by_topic(token, org_name, topic)
    repo_names = [repo.full_name for repo in repo_objects]

    # Step 2: Find issues by title in these repositories
    issue_node_ids = find_issues_by_title(token, org_name, repo_names, issue_title)

    # Step 3: Get the project's node ID
    project = get_project_by_name(token, org_name, project_name)
    if project:
        project_id = project["id"]

        # Step 4: Link the issues to the project
        for issue_node_id in issue_node_ids:
            add_issue_to_project(token, project_id, issue_node_id)
    else:
        print(f"Project '{project_name}' not found.")


def main() -> None:
    """
    Main function to run the specified project maintenance command.
    """
    parser = argparse.ArgumentParser(
        description="Run specified function with arguments."
    )
    subparsers = parser.add_subparsers(dest="command")

    # Parser for get_package_names
    parser_get_pkgs = subparsers.add_parser(
        "get_package_names", help="Get package names from server"
    )
    parser_get_pkgs.add_argument("server_name", type=str, help="Server name")

    # Parser for add_tag_to_repos
    parser_add_tag = subparsers.add_parser("add_tag_to_repos", help="Add tag to repos")
    parser_add_tag.add_argument("token", type=str, help="GitHub token")
    parser_add_tag.add_argument("org_name", type=str, help="Organization name")
    parser_add_tag.add_argument("repo_names", nargs="+", help="List of repo names")
    parser_add_tag.add_argument("tag", type=str, help="Tag to add")

    # Parser for process_packages_and_add_tag
    parser_proc_pkgs = subparsers.add_parser(
        "process_packages_and_add_tag", help="Process packages and add tag"
    )
    parser_proc_pkgs.add_argument("server_name", type=str, help="Server name")
    parser_proc_pkgs.add_argument("token", type=str, help="GitHub token")
    parser_proc_pkgs.add_argument("org_name", type=str, help="Organization name")
    parser_proc_pkgs.add_argument("tag", type=str, help="Tag to add")

    # Parser for add_issues_and_create_cards
    parser_add_issues = subparsers.add_parser(
        "add_issues_and_create_cards", help="Add issues and create cards"
    )
    parser_add_issues.add_argument("token", type=str, help="GitHub token")
    parser_add_issues.add_argument("org_name", type=str, help="Organization name")
    parser_add_issues.add_argument("project_name", type=str, help="Project name")
    parser_add_issues.add_argument("topic", type=str, help="GitHub topic")
    parser_add_issues.add_argument("issue_title", type=str, help="Issue title")
    parser_add_issues.add_argument("issue_body", type=str, help="Issue body")

    # Parser for link_issues link_issue_title_to_project
    link_parser = subparsers.add_parser(
        "link_issues",
        help="Link issues with a specific title to a Next-Generation project",
    )
    link_parser.add_argument("token", type=str, help="GitHub Personal Access Token")
    link_parser.add_argument(
        "org_name", type=str, help="Name of the GitHub organization"
    )
    link_parser.add_argument(
        "project_name", type=str, help="Name of the GitHub project"
    )
    link_parser.add_argument(
        "topic", type=str, help="GitHub topic to filter repositories by"
    )
    link_parser.add_argument("issue_title", type=str, help="Title of the issue to link")

    args = parser.parse_args()

    if args.command == "get_package_names":
        packages = get_package_names(args.server_name)
        print(packages)

    elif args.command == "add_tag_to_repos":
        add_tag_to_repos(args.token, args.org_name, args.repo_names, args.tag)

    elif args.command == "process_packages_and_add_tag":
        process_packages_and_add_tag(
            args.server_name, args.token, args.org_name, args.tag
        )

    elif args.command == "add_issues_and_create_cards":
        add_issues_and_create_cards(
            args.token,
            args.org_name,
            args.project_name,
            args.topic,
            args.issue_title,
            args.issue_body,
        )
    elif args.command == "link_issues":
        link_issue_title_to_project(
            args.token, args.org_name, args.project_name, args.topic, args.issue_title
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
