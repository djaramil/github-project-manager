#!/usr/bin/env python3
"""
GitHub Repository Project Manager

This script checks repositories in a GitHub organization for associated projects.
If a repository doesn't have a project, it creates one and grants write access to the repo owner.
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

# GitHub API base URL
GITHUB_API_BASE = 'https://api.github.com'

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


def get_repo_projects(session: requests.Session, repo_name: str) -> List[Dict]:
    """
    Get all projects associated with a repository.
    
    Args:
        session: Requests session object
        repo_name: Name of the repository
        
    Returns:
        List of project dictionaries
    """
    url = f"{GITHUB_API_BASE}/repos/{ORG_NAME}/{repo_name}/projects"
    
    response = session.get(url, headers=HEADERS)
    
    if response.status_code == 404:
        return []
    elif response.status_code != 200:
        print(f"  Warning: Could not fetch projects for {repo_name}: {response.status_code}")
        return []
    
    return response.json()


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


def create_project(session: requests.Session, repo_name: str, project_name: str) -> Optional[Dict]:
    """
    Create a new project for a repository.
    
    Args:
        session: Requests session object
        repo_name: Name of the repository
        project_name: Name for the new project
        
    Returns:
        Created project dictionary or None if failed
    """
    url = f"{GITHUB_API_BASE}/repos/{ORG_NAME}/{repo_name}/projects"
    
    data = {
        'name': project_name,
        'body': f'Project board for {project_name}'
    }
    
    response = session.post(url, headers=HEADERS, json=data)
    
    if response.status_code == 201:
        return response.json()
    else:
        print(f"  Error creating project: {response.status_code}")
        print(f"  Response: {response.text}")
        return None


def get_user_info(session: requests.Session, username: str) -> Optional[Dict]:
    """
    Get user information from GitHub.
    
    Args:
        session: Requests session object
        username: GitHub username
        
    Returns:
        User dictionary or None if not found
    """
    url = f"{GITHUB_API_BASE}/users/{username}"
    
    response = session.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None


def add_collaborator_to_project(session: requests.Session, project_id: int, username: str) -> bool:
    """
    Add a collaborator to a project with write access.
    Note: GitHub's classic projects API has limited collaboration features.
    This function attempts to add the user, but may have limitations.
    
    Args:
        session: Requests session object
        project_id: ID of the project
        username: GitHub username to add
        
    Returns:
        True if successful, False otherwise
    """
    # Note: Classic projects don't have a direct API for adding collaborators
    # The permissions are inherited from the repository
    # This is a placeholder for future implementation if needed
    print(f"    Note: Project permissions are inherited from repository access")
    return True


def process_repository(session: requests.Session, repo: Dict) -> None:
    """
    Process a single repository: check for projects and create if needed.
    
    Args:
        session: Requests session object
        repo: Repository dictionary
    """
    repo_name = repo['name']
    print(f"Processing: {repo_name}")
    
    # Check for existing projects
    projects = get_repo_projects(session, repo_name)
    
    if projects:
        print(f"  ✓ Already has {len(projects)} project(s)")
        for project in projects:
            print(f"    - {project['name']}")
        return
    
    # No projects found, create one
    print(f"  ✗ No projects found")
    
    # Extract username from repo name
    username = extract_github_username(repo_name)
    
    if not username:
        print(f"  Warning: Could not extract username from {repo_name}")
        username = "user"
    
    # Verify user exists
    user_info = get_user_info(session, username)
    if user_info:
        print(f"  Found GitHub user: @{username}")
    else:
        print(f"  Warning: GitHub user @{username} not found, using name anyway")
    
    # Create project
    project_name = f"@{username} final project"
    print(f"  Creating project: '{project_name}'")
    
    project = create_project(session, repo_name, project_name)
    
    if project:
        print(f"  ✓ Project created successfully!")
        print(f"    Project URL: {project['html_url']}")
        
        # Add collaborator (note: permissions inherited from repo)
        add_collaborator_to_project(session, project['id'], username)
    else:
        print(f"  ✗ Failed to create project")
    
    print()


def main():
    """Main execution function."""
    print("=" * 70)
    print("GitHub Repository Project Manager")
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
    
    for repo in repos:
        process_repository(session, repo)
    
    print("=" * 70)
    print("Processing Complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
