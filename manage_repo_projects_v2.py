#!/usr/bin/env python3
"""
GitHub Repository Project Manager (Projects V2)

This script checks repositories in a GitHub organization for associated projects.
If a repository doesn't have a project, it creates one using the new Projects V2 API
and links it to the repository.
"""

import os
import sys
import re
from typing import List, Dict, Optional
from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables
load_dotenv()

# Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
ORG_NAME = os.getenv('ORG_NAME', 'FAU-Fall2025-iOS-Mobile-App')
REPO_FILTER = os.getenv('REPO_FILTER', 'final-project')

# GitHub API base URLs
GITHUB_API_BASE = 'https://api.github.com'
GITHUB_GRAPHQL_URL = 'https://api.github.com/graphql'

# Headers for GitHub API requests
HEADERS = {
    'Accept': 'application/vnd.github+json',
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'X-GitHub-Api-Version': '2022-11-28'
}


def create_session() -> requests.Session:
    """Create a requests session with retry logic."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def graphql_query(session: requests.Session, query: str, variables: Optional[Dict] = None) -> Dict:
    """
    Execute a GraphQL query.
    
    Args:
        session: Requests session object
        query: GraphQL query string
        variables: Optional variables for the query
        
    Returns:
        Response data dictionary
    """
    payload = {'query': query}
    if variables:
        payload['variables'] = variables
    
    response = session.post(GITHUB_GRAPHQL_URL, headers=HEADERS, json=payload)
    
    if response.status_code != 200:
        print(f"GraphQL Error: {response.status_code}")
        print(f"Response: {response.text}")
        return {}
    
    data = response.json()
    
    if 'errors' in data:
        print(f"GraphQL Errors: {data['errors']}")
        return {}
    
    return data.get('data', {})


def get_organization_node_id(session: requests.Session) -> Optional[str]:
    """
    Get the node ID of the organization.
    
    Args:
        session: Requests session object
        
    Returns:
        Organization node ID or None
    """
    query = """
    query($org: String!) {
        organization(login: $org) {
            id
        }
    }
    """
    
    data = graphql_query(session, query, {'org': ORG_NAME})
    
    if data and 'organization' in data:
        return data['organization']['id']
    
    return None


def get_organization_repos(session: requests.Session) -> List[Dict]:
    """
    Fetch all repositories from the organization that match the filter.
    
    Args:
        session: Requests session object
        
    Returns:
        List of repository dictionaries
    """
    repos = []
    page = 1
    per_page = 100
    
    print(f"Fetching repositories from organization: {ORG_NAME}")
    print(f"Filtering for repositories containing: '{REPO_FILTER}'")
    
    while True:
        url = f"{GITHUB_API_BASE}/orgs/{ORG_NAME}/repos"
        params = {
            'per_page': per_page,
            'page': page,
            'sort': 'name',
            'direction': 'asc'
        }
        
        response = session.get(url, headers=HEADERS, params=params)
        
        if response.status_code != 200:
            print(f"Error fetching repositories: {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)
        
        page_repos = response.json()
        
        if not page_repos:
            break
        
        # Filter repos by name
        filtered_repos = [
            repo for repo in page_repos 
            if REPO_FILTER.lower() in repo['name'].lower()
        ]
        repos.extend(filtered_repos)
        
        page += 1
        
        # Check if we've reached the last page
        if len(page_repos) < per_page:
            break
    
    print(f"Found {len(repos)} repositories matching filter\n")
    return repos


def get_repo_projects_v2(session: requests.Session, repo_owner: str, repo_name: str) -> List[Dict]:
    """
    Get all Projects V2 linked to a repository using GraphQL.
    
    Args:
        session: Requests session object
        repo_owner: Owner of the repository
        repo_name: Name of the repository
        
    Returns:
        List of project dictionaries
    """
    query = """
    query($owner: String!, $name: String!) {
        repository(owner: $owner, name: $name) {
            projectsV2(first: 10) {
                nodes {
                    id
                    number
                    title
                    url
                }
            }
        }
    }
    """
    
    data = graphql_query(session, query, {'owner': repo_owner, 'name': repo_name})
    
    if data and 'repository' in data and data['repository']:
        projects = data['repository'].get('projectsV2', {}).get('nodes', [])
        return projects
    
    return []


def extract_github_username(repo_name: str) -> Optional[str]:
    """
    Extract GitHub username from repository name.
    Assumes format like 'final-project-username' or similar patterns.
    
    Args:
        repo_name: Name of the repository
        
    Returns:
        Extracted username or None
    """
    # Remove 'final-project-' prefix if it exists
    pattern = r'final-project-(.+)'
    match = re.search(pattern, repo_name, re.IGNORECASE)
    
    if match:
        return match.group(1)
    
    # If no match, return the repo name as fallback
    return repo_name.replace('final-project-', '').replace('final-project', '').strip('-')


def get_user_node_id(session: requests.Session, username: str) -> Optional[str]:
    """
    Get the node ID of a GitHub user.
    
    Args:
        session: Requests session object
        username: GitHub username
        
    Returns:
        User node ID or None
    """
    query = """
    query($login: String!) {
        user(login: $login) {
            id
        }
    }
    """
    
    data = graphql_query(session, query, {'login': username})
    
    if data and 'user' in data and data['user']:
        return data['user']['id']
    
    return None


def create_project_v2(session: requests.Session, owner_id: str, project_name: str) -> Optional[Dict]:
    """
    Create a new Project V2 using GraphQL.
    
    Args:
        session: Requests session object
        owner_id: Node ID of the project owner (user or organization)
        project_name: Name for the new project
        
    Returns:
        Created project dictionary or None if failed
    """
    mutation = """
    mutation($ownerId: ID!, $title: String!) {
        createProjectV2(input: {ownerId: $ownerId, title: $title}) {
            projectV2 {
                id
                title
                url
                number
            }
        }
    }
    """
    
    data = graphql_query(session, mutation, {'ownerId': owner_id, 'title': project_name})
    
    if data and 'createProjectV2' in data:
        return data['createProjectV2']['projectV2']
    
    return None


def link_project_to_repo(session: requests.Session, project_id: str, repo_id: str) -> bool:
    """
    Link a Project V2 to a repository.
    
    Args:
        session: Requests session object
        project_id: Node ID of the project
        repo_id: Node ID of the repository
        
    Returns:
        True if successful, False otherwise
    """
    mutation = """
    mutation($projectId: ID!, $repositoryId: ID!) {
        linkProjectV2ToRepository(input: {projectId: $projectId, repositoryId: $repositoryId}) {
            repository {
                id
            }
        }
    }
    """
    
    data = graphql_query(session, mutation, {'projectId': project_id, 'repositoryId': repo_id})
    
    return bool(data and 'linkProjectV2ToRepository' in data)


def get_repo_node_id(session: requests.Session, repo_owner: str, repo_name: str) -> Optional[str]:
    """
    Get the node ID of a repository.
    
    Args:
        session: Requests session object
        repo_owner: Owner of the repository
        repo_name: Name of the repository
        
    Returns:
        Repository node ID or None
    """
    query = """
    query($owner: String!, $name: String!) {
        repository(owner: $owner, name: $name) {
            id
        }
    }
    """
    
    data = graphql_query(session, query, {'owner': repo_owner, 'name': repo_name})
    
    if data and 'repository' in data and data['repository']:
        return data['repository']['id']
    
    return None


def add_project_collaborator(session: requests.Session, project_id: str, user_id: str, role: str = "WRITER") -> bool:
    """
    Add a collaborator to a Project V2 with specified role.
    
    Args:
        session: Requests session object
        project_id: Node ID of the project
        user_id: Node ID of the user to add
        role: Role to grant (ADMIN, WRITER, READER, NONE)
        
    Returns:
        True if successful, False otherwise
    """
    mutation = """
    mutation($projectId: ID!, $userId: ID!, $role: ProjectV2Roles!) {
        updateProjectV2Collaborators(input: {projectId: $projectId, collaborators: [{userId: $userId, role: $role}]}) {
            collaborators(first: 1) {
                totalCount
            }
        }
    }
    """
    
    data = graphql_query(session, mutation, {'projectId': project_id, 'userId': user_id, 'role': role})
    
    return bool(data and 'updateProjectV2Collaborators' in data)


def get_project_collaborators(session: requests.Session, project_number: int, org_login: str) -> List[str]:
    """
    Get list of collaborators for a project using REST API.
    Note: Projects V2 don't expose collaborators via GraphQL, so we return empty list
    and always attempt to add the user.
    
    Args:
        session: Requests session object
        project_number: Project number
        org_login: Organization login
        
    Returns:
        Empty list (Projects V2 don't expose collaborators via API)
    """
    # Projects V2 don't have a public API to list collaborators
    # We'll just attempt to add the user and let the API handle duplicates
    return []


def process_repository(session: requests.Session, repo: Dict, org_node_id: str) -> Dict:
    """
    Process a single repository: check for projects and create if needed.
    
    Args:
        session: Requests session object
        repo: Repository dictionary
        org_node_id: Node ID of the organization
        
    Returns:
        Dictionary with processing results
    """
    repo_name = repo['name']
    repo_owner = repo['owner']['login']
    result = {'repo': repo_name, 'status': 'skipped', 'project_url': None, 'username': None}
    
    print(f"Processing: {repo_name}")
    
    # Extract username from repo name
    username = extract_github_username(repo_name)
    
    if not username:
        print(f"  Warning: Could not extract username from {repo_name}")
        username = "user"
    
    # Get user node ID
    user_node_id = get_user_node_id(session, username)
    
    # Check for existing projects
    projects = get_repo_projects_v2(session, repo_owner, repo_name)
    
    if projects:
        print(f"  ✓ Already has {len(projects)} project(s)")
        for project in projects:
            print(f"    - {project['title']}")
            
            # Add user as collaborator (API will handle if already exists)
            if user_node_id:
                print(f"  Ensuring @{username} has write access...")
                if add_project_collaborator(session, project['id'], user_node_id, "WRITER"):
                    print(f"  ✓ User access granted/confirmed!")
                else:
                    print(f"  ⚠ Could not grant access (may already have it)")
        
        result['status'] = 'already_exists'
        return result
    
    # No projects found, create one
    print(f"  ✗ No projects found")
    
    if user_node_id:
        print(f"  Found GitHub user: @{username}")
    else:
        print(f"  Warning: GitHub user @{username} not found, using name anyway")
    
    # Always create project under organization (you can't create projects for other users)
    owner_id = org_node_id
    owner_type = "organization"
    
    # Create project
    project_name = f"@{username} final project"
    print(f"  Creating project: '{project_name}' (owner: {owner_type})")
    
    project = create_project_v2(session, owner_id, project_name)
    
    if project:
        print(f"  ✓ Project created successfully!")
        print(f"    Project URL: {project['url']}")
        result['status'] = 'created'
        result['project_url'] = project['url']
        result['username'] = username
        
        # Link project to repository
        repo_node_id = get_repo_node_id(session, repo_owner, repo_name)
        
        if repo_node_id:
            print(f"  Linking project to repository...")
            if link_project_to_repo(session, project['id'], repo_node_id):
                print(f"  ✓ Project linked to repository!")
            else:
                print(f"  ✗ Failed to link project to repository")
                result['status'] = 'created_not_linked'
        else:
            print(f"  Warning: Could not get repository node ID for linking")
            result['status'] = 'created_not_linked'
        
        # Add user as collaborator with write access
        if user_node_id:
            print(f"  Adding @{username} as collaborator with write access...")
            if add_project_collaborator(session, project['id'], user_node_id, "WRITER"):
                print(f"  ✓ User added as collaborator!")
            else:
                print(f"  ✗ Failed to add user as collaborator")
        else:
            print(f"  ⚠ Skipping collaborator add (user not found)")
    else:
        print(f"  ✗ Failed to create project")
        result['status'] = 'failed'
    
    print()
    return result


def main():
    """Main execution function."""
    print("=" * 70)
    print("GitHub Repository Project Manager (Projects V2)")
    print("=" * 70)
    print()
    
    # Validate configuration
    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN environment variable not set")
        print("Please create a .env file with your GitHub token")
        sys.exit(1)
    
    print(f"Organization: {ORG_NAME}")
    print(f"Filter: {REPO_FILTER}")
    print()
    
    # Create session
    session = create_session()
    
    # Get organization node ID
    print("Getting organization node ID...")
    org_node_id = get_organization_node_id(session)
    
    if not org_node_id:
        print("Error: Could not get organization node ID")
        sys.exit(1)
    
    print(f"Organization node ID: {org_node_id}")
    print()
    
    # Get repositories
    repos = get_organization_repos(session)
    
    if not repos:
        print("No repositories found matching the filter")
        return
    
    # Process each repository
    print("=" * 70)
    print("Processing Repositories")
    print("=" * 70)
    print()
    
    results = []
    for repo in repos:
        result = process_repository(session, repo, org_node_id)
        results.append(result)
    
    # Print summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    
    created = [r for r in results if r['status'] == 'created']
    already_exists = [r for r in results if r['status'] == 'already_exists']
    failed = [r for r in results if r['status'] == 'failed']
    created_not_linked = [r for r in results if r['status'] == 'created_not_linked']
    
    print(f"Total repositories processed: {len(results)}")
    print(f"  ✓ Projects created: {len(created)}")
    print(f"  ✓ Already had projects: {len(already_exists)}")
    if failed:
        print(f"  ✗ Failed to create: {len(failed)}")
    if created_not_linked:
        print(f"  ⚠ Created but not linked: {len(created_not_linked)}")
    print()
    
    if created:
        print("Projects Created:")
        for r in created:
            print(f"  • {r['repo']} → @{r['username']} final project")
            print(f"    {r['project_url']}")
        print()
    
    if failed:
        print("Failed:")
        for r in failed:
            print(f"  • {r['repo']}")
        print()
    
    print("=" * 70)
    print("Processing Complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
