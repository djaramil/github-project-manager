# GitHub Repository Project Manager

This tool automatically checks GitHub repositories in an organization for associated projects and creates them if they don't exist.

## Features

- Fetches all repositories from a GitHub organization
- Filters repositories by name (e.g., "final-project")
- Checks if each repository has an associated project (Projects V2)
- Creates a project named "@username final project" if one doesn't exist
- Automatically extracts GitHub username from repository name
- Links projects to their respective repositories
- Provides detailed progress output
- **Can run as a GitHub Action every 15 minutes** (see [GITHUB_ACTION_SETUP.md](GITHUB_ACTION_SETUP.md))

## Prerequisites

- Python 3.7 or higher
- GitHub Personal Access Token (Classic) with the following scopes:
  - `repo` (Full control of repositories)
  - `read:org` (Read org and team membership)
  - `project` (Full control of projects - **REQUIRED** for Projects V2)

## Setup

1. **Clone or navigate to this directory**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a GitHub Personal Access Token (Classic)**
   - Go to https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - Give it a descriptive name (e.g., "Repo Project Manager")
   - Select the following scopes:
     - ✓ `repo` (all sub-scopes)
     - ✓ `read:org` - For reading organization repositories
     - ✓ `project` (all sub-scopes) - **Required for Projects V2**
   - Click "Generate token"
   - **Copy the token immediately** (you won't be able to see it again)

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your GitHub token:
   ```
   GITHUB_TOKEN=ghp_your_actual_token_here
   ORG_NAME=FAU-Fall2025-iOS-Mobile-App
   REPO_FILTER=final-project
   ```

## Usage

### Manual Execution

Run the script locally:
```bash
python manage_repo_projects_v2.py
```

### Automated Execution (GitHub Action)

For automated execution every 15 minutes, see the detailed setup guide: [GITHUB_ACTION_SETUP.md](GITHUB_ACTION_SETUP.md)

The script will:
1. Fetch all repositories from the organization that contain "final-project" in their name
2. Check each repository for existing projects
3. If no project exists:
   - Extract the GitHub username from the repository name
   - Create a new project named "@username final project"
   - Grant write access (inherited from repository permissions)

## Output Example

```
======================================================================
GitHub Repository Project Manager
======================================================================

Organization: FAU-Fall2025-iOS-Mobile-App
Filter: final-project

Fetching repositories from organization: FAU-Fall2025-iOS-Mobile-App
Filtering for repositories containing: 'final-project'
Found 25 repositories matching filter

======================================================================
Processing Repositories
======================================================================

Processing: final-project-johndoe
  ✗ No projects found
  Found GitHub user: @johndoe
  Creating project: '@johndoe final project'
  ✓ Project created successfully!
    Project URL: https://github.com/FAU-Fall2025-iOS-Mobile-App/final-project-johndoe/projects/1
    Note: Project permissions are inherited from repository access

Processing: final-project-janedoe
  ✓ Already has 1 project(s)
    - @janedoe final project

======================================================================
Processing Complete!
======================================================================
```

## Configuration

You can customize the behavior by editing the `.env` file:

- `GITHUB_TOKEN`: Your GitHub Personal Access Token (required)
- `ORG_NAME`: The GitHub organization to scan (default: FAU-Fall2025-iOS-Mobile-App)
- `REPO_FILTER`: String to filter repository names (default: final-project)

## Troubleshooting

### "Error: GITHUB_TOKEN environment variable not set"
Make sure you've created a `.env` file with your GitHub token.

### "Error fetching repositories: 401"
Your GitHub token is invalid or has expired. Generate a new one.

### "Error fetching repositories: 403"
Your GitHub token doesn't have the required permissions. Make sure it has `repo`, `read:org`, and `project` scopes.

### "GraphQL Errors: INSUFFICIENT_SCOPES"
Your token is missing the `project` scope. Regenerate your token with all required scopes.

### "Warning: GitHub user @username not found"
The script couldn't find a GitHub user matching the extracted username. The project will still be created with the extracted name.

## Notes

- Project permissions are inherited from repository access settings
- The script uses GitHub's **Projects V2** (GraphQL API)
- Projects are created at the organization level and linked to repositories
- Repository naming convention should be `final-project-username` for best results
- The script includes retry logic for API rate limiting
- For automated execution, see [GITHUB_ACTION_SETUP.md](GITHUB_ACTION_SETUP.md)

## Security

- Never commit your `.env` file or expose your GitHub token
- The `.gitignore` file is configured to exclude `.env` files
- Tokens should be treated as passwords and kept secure

## License

This tool is provided as-is for educational purposes.
