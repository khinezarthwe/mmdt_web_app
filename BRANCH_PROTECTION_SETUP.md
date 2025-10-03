# Branch Protection Setup Guide

This guide explains how to set up branch protection rules in GitHub to automatically block merges when tests fail.

## Required GitHub Actions Workflows

The following workflows have been created and will run automatically on PRs:

1. **Test Suite** (`.github/workflows/test.yml`)
   - Runs tests on Python 3.9, 3.10, and 3.11
   - Generates test coverage reports
   - Validates database migrations
   - Checks template validation

2. **Continuous Integration** (`.github/workflows/ci.yml`)
   - Code formatting checks (black, isort)
   - Linting with flake8
   - Django system checks
   - Security checks with safety
   - Test coverage requirements (80% minimum)

3. **Security Scan** (`.github/workflows/security.yml`)
   - Dependency vulnerability scanning
   - Code security analysis with bandit
   - Scheduled weekly security scans

## Setting Up Branch Protection Rules

### Step 1: Navigate to Repository Settings
1. Go to your GitHub repository
2. Click on **Settings** tab
3. Click on **Branches** in the left sidebar

### Step 2: Add Branch Protection Rule
1. Click **Add rule** or **Add branch protection rule**
2. In **Branch name pattern**, enter: `main` (or your primary branch name)

### Step 3: Configure Protection Settings
Enable the following options:

#### ✅ Required Status Checks
- Check **Require status checks to pass before merging**
- Check **Require branches to be up to date before merging**
- In the search box, add these required status checks:
  - `test (3.9)`
  - `test (3.10)` 
  - `test (3.11)`
  - `lint-and-test`
  - `security`

#### ✅ Additional Protection Options
- **Require pull request reviews before merging**
  - Set minimum number of reviewers: `1`
  - Check **Dismiss stale PR approvals when new commits are pushed**
  - Check **Require review from code owners** (if you have a CODEOWNERS file)

- **Restrict pushes that create files**
  - Check **Restrict pushes that create files**

- **Allow force pushes**
  - Leave unchecked (recommended)

- **Allow deletions**
  - Leave unchecked (recommended)

### Step 4: Save the Rule
Click **Create** to save the branch protection rule.

## Optional: Additional Branch Protection

### For `develop` branch (if using GitFlow)
Repeat the same process for the `develop` branch with the same settings.

### For feature branches
You can create a pattern like `feature/*` or `hotfix/*` with similar but less restrictive rules.

## Verification

After setting up branch protection:

1. **Create a test PR** with failing tests
2. **Verify the PR is blocked** from merging
3. **Fix the tests** and verify the PR becomes mergeable
4. **Test with a passing PR** to ensure normal workflow

## Required Status Checks Explained

- **`test (3.9/3.10/3.11)`**: Ensures code works across Python versions
- **`lint-and-test`**: Code quality and formatting checks
- **`security`**: Security vulnerability scanning

## Troubleshooting

### Common Issues:

1. **"Required status checks are pending"**
   - Wait for GitHub Actions to complete
   - Check the Actions tab for workflow status

2. **"Required status checks have not been satisfied"**
   - Fix failing tests or linting issues
   - Push new commits to trigger re-runs

3. **"Branch is not up to date"**
   - Merge or rebase with the target branch
   - This ensures your changes work with the latest code

### Admin Override:
Repository administrators can bypass branch protection rules if needed, but this should be used sparingly and only in emergencies.

## Benefits

With these branch protection rules in place:

- ✅ **No broken code** gets merged to main branch
- ✅ **Consistent code quality** across all contributions
- ✅ **Security vulnerabilities** are caught early
- ✅ **Test coverage** is maintained
- ✅ **Code formatting** is standardized
- ✅ **Multi-version compatibility** is ensured

This setup ensures that only high-quality, tested, and secure code makes it into your main branch.
