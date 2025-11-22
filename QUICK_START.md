# Quick Start: GitHub Action Setup

This is a condensed guide to get the GitHub Action running quickly.

## Step 1: Push This Repository to GitHub

```bash
cd "/Users/yoda26/Documents/FAU/Mobile-App-Fall-2025/Final Project/create-github-repo-projects"

# Initialize git (if not already done)
git init
git add .
git commit -m "Add GitHub project automation"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
git branch -M main
git push -u origin main
```

## Step 2: Create a Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name it: `Project Manager Action Token`
4. Select scopes: `repo`, `read:org`, `project`
5. Generate and **copy the token**

## Step 3: Add Token as Secret

1. Go to your repository → **Settings** → **Secrets and variables** → **Actions**
2. Click "New repository secret"
3. Name: `PROJECT_MANAGER_TOKEN`
4. Value: Paste your token
5. Click "Add secret"

## Step 4: Test It

1. Go to **Actions** tab
2. Click "Auto-Create Repository Projects"
3. Click "Run workflow" → "Run workflow"
4. Watch it run!

## Done!

The action will now run automatically every 15 minutes. Check the Actions tab to monitor runs.

For detailed documentation, see [GITHUB_ACTION_SETUP.md](GITHUB_ACTION_SETUP.md).
