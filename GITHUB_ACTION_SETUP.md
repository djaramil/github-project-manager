# GitHub Action Setup Guide

This guide explains how to set up the automated GitHub Action that runs every 15 minutes to check for repositories without projects and create them automatically.

## Overview

The GitHub Action will:
- Run automatically every 15 minutes
- Check all repositories matching the filter (e.g., "final-project")
- Create Projects V2 for repositories that don't have them
- Link projects to their respective repositories
- Can also be triggered manually

## Setup Instructions

### 1. Create a GitHub Repository for This Tool

First, you need to create a repository to host this automation tool:

```bash
# Initialize git repository (if not already done)
cd "/Users/yoda26/Documents/FAU/Mobile-App-Fall-2025/Final Project/create-github-repo-projects"
git init

# Add all files
git add .
git commit -m "Initial commit: GitHub project automation tool"

# Create a new repository on GitHub (via web or CLI)
# Then push to it
git remote add origin https://github.com/YOUR_USERNAME/github-project-manager.git
git branch -M main
git push -u origin main
```

### 2. Create a GitHub Personal Access Token

You need a **separate token** for the GitHub Action (don't reuse your personal token):

1. Go to https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Give it a name: `Project Manager Action Token`
4. Set expiration: Choose based on your needs (recommend: 90 days or No expiration)
5. Select scopes:
   - ✅ `repo` (Full control of repositories)
   - ✅ `read:org` (Read org membership)
   - ✅ `project` (Full control of projects)
6. Click **"Generate token"**
7. **Copy the token immediately** (you won't see it again)

### 3. Add Token as Repository Secret

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Name: `PROJECT_MANAGER_TOKEN`
5. Value: Paste the token you just created
6. Click **"Add secret"**

### 4. Enable GitHub Actions

1. Go to your repository's **Actions** tab
2. If prompted, click **"I understand my workflows, go ahead and enable them"**
3. The workflow should now be visible

### 5. Test the Action

You can test the action manually before waiting for the scheduled run:

1. Go to **Actions** tab
2. Click on **"Auto-Create Repository Projects"** workflow
3. Click **"Run workflow"** dropdown
4. Click the green **"Run workflow"** button
5. Watch the progress in real-time

## How It Works

### Schedule
```yaml
schedule:
  - cron: '*/15 * * * *'  # Every 15 minutes
```

The action runs every 15 minutes using GitHub's cron scheduler. Note:
- GitHub Actions may have a delay of up to 5-10 minutes from the scheduled time
- During high load periods, scheduled workflows may be delayed further

### Manual Trigger
You can also trigger the workflow manually:
- Go to Actions → Auto-Create Repository Projects → Run workflow

### On Push (Testing)
The workflow also runs when you push to the `main` branch, useful for testing changes.

## Monitoring

### View Workflow Runs
1. Go to **Actions** tab in your repository
2. Click on any workflow run to see details
3. Click on the **"create-projects"** job to see logs

### Check for Errors
- Failed runs will appear with a red ❌
- Click on the failed run to see error details
- Error logs are automatically uploaded as artifacts (retained for 7 days)

### Download Error Logs
If a workflow fails:
1. Click on the failed workflow run
2. Scroll down to **Artifacts** section
3. Download **error-logs** if available

## Configuration

You can modify the workflow behavior by editing `.github/workflows/auto-create-projects.yml`:

### Change Schedule
```yaml
schedule:
  - cron: '*/15 * * * *'  # Every 15 minutes
  # - cron: '0 * * * *'   # Every hour
  # - cron: '0 0 * * *'   # Daily at midnight
  # - cron: '0 9 * * 1'   # Every Monday at 9 AM
```

### Change Organization or Filter
Edit the environment variables in the workflow:
```yaml
env:
  ORG_NAME: FAU-Fall2025-iOS-Mobile-App
  REPO_FILTER: final-project
```

Or add them as repository variables:
1. Settings → Secrets and variables → Actions → Variables tab
2. Add `ORG_NAME` and `REPO_FILTER` as variables

## Troubleshooting

### "Error: GITHUB_TOKEN environment variable not set"
- Make sure you added `PROJECT_MANAGER_TOKEN` as a repository secret
- Check the secret name matches exactly in the workflow file

### "Error fetching repositories: 401"
- Your token is invalid or expired
- Generate a new token and update the repository secret

### "Error fetching repositories: 403"
- Your token doesn't have the required scopes
- Make sure the token has `repo`, `read:org`, and `project` scopes

### "GraphQL Errors: INSUFFICIENT_SCOPES"
- The token is missing the `project` scope
- Regenerate the token with all required scopes

### Workflow doesn't run on schedule
- GitHub Actions scheduled workflows may be delayed during high load
- The repository must have had activity in the last 60 days
- Try triggering manually to verify it works

### Rate Limiting
- GitHub API has rate limits (5,000 requests/hour for authenticated requests)
- The script is designed to be efficient, but with many repos, you might hit limits
- If you hit rate limits, consider reducing the frequency (e.g., every 30 minutes)

## Security Best Practices

1. **Use a dedicated token** - Don't use your personal token for automation
2. **Set token expiration** - Regularly rotate tokens (every 90 days recommended)
3. **Minimal permissions** - Only grant the scopes needed
4. **Monitor usage** - Regularly check workflow runs for suspicious activity
5. **Audit logs** - Review GitHub's audit logs periodically

## Disabling the Action

To temporarily disable the action:

### Option 1: Disable the workflow
1. Go to **Actions** tab
2. Click on **"Auto-Create Repository Projects"**
3. Click the **"..."** menu → **"Disable workflow"**

### Option 2: Comment out the schedule
Edit `.github/workflows/auto-create-projects.yml`:
```yaml
# schedule:
#   - cron: '*/15 * * * *'
```

### Option 3: Delete the workflow file
```bash
rm .github/workflows/auto-create-projects.yml
git add .
git commit -m "Disable auto-create projects action"
git push
```

## Cost Considerations

GitHub Actions is free for public repositories with unlimited minutes. For private repositories:
- Free tier: 2,000 minutes/month
- This workflow uses ~1-2 minutes per run
- Running every 15 minutes = 96 runs/day = ~2,880 runs/month
- Estimated usage: ~2,880-5,760 minutes/month

If using a private repository, consider:
- Reducing frequency (every 30 minutes or hourly)
- Using a public repository for this automation
- Upgrading to GitHub Pro/Team for more minutes

## Alternative: GitHub App

For production use, consider creating a GitHub App instead of using a personal access token:
- More secure (fine-grained permissions)
- Better rate limits
- Can be installed organization-wide
- Doesn't count against personal API limits

See: https://docs.github.com/en/apps/creating-github-apps

## Support

If you encounter issues:
1. Check the workflow logs in the Actions tab
2. Review the error messages
3. Verify your token has the correct scopes
4. Test the script locally first
5. Check GitHub's status page: https://www.githubstatus.com/
