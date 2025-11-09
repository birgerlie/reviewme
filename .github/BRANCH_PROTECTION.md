# Branch Protection Setup Guide

This guide explains how to set up branch protection for the Review Platform repository to ensure code quality and prevent accidental changes to critical branches.

## Table of Contents

1. [Creating the Develop Branch](#creating-the-develop-branch)
2. [Branch Protection Rules](#branch-protection-rules)
3. [CI/CD Pipeline](#cicd-pipeline)
4. [Required Status Checks](#required-status-checks)
5. [Workflow](#workflow)

---

## Creating the Develop Branch

### Step 1: Create `develop` branch on GitHub

1. Go to your repository on GitHub
2. Click the branch dropdown (currently showing your default branch)
3. Type `develop` in the text box
4. Click "Create branch: develop from claude/review-platform-foundation-011CUwm1aB53x4c7EDwoNo8X"

Alternatively, using GitHub CLI:
```bash
gh api repos/{owner}/{repo}/git/refs \
  -f ref='refs/heads/develop' \
  -f sha='<commit-sha-from-claude-branch>'
```

Or if you have local git access (outside Claude Code):
```bash
git checkout claude/review-platform-foundation-011CUwm1aB53x4c7EDwoNo8X
git checkout -b develop
git push -u origin develop
```

---

## Branch Protection Rules

### For `develop` Branch

Navigate to: **Settings → Branches → Add branch protection rule**

#### Rule Configuration:

**Branch name pattern:** `develop`

**Protect matching branches:**

- ✅ **Require a pull request before merging**
  - ✅ Require approvals: **1** (or more for larger teams)
  - ✅ Dismiss stale pull request approvals when new commits are pushed
  - ✅ Require review from Code Owners (if you create a CODEOWNERS file)
  - ✅ Require approval of the most recent reviewable push

- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging
  - **Add required status checks:**
    - `Run Tests`
    - `Docker Build Test`
    - `All Checks Passed`

- ✅ **Require conversation resolution before merging**
  - All review comments must be resolved before merging

- ✅ **Require signed commits** (optional, for extra security)

- ✅ **Require linear history** (optional, prevents merge commits)

- ✅ **Include administrators**
  - Even admins must follow these rules

- ⚠️ **Do not allow bypassing the above settings**
  - Prevents force pushes and deletions

- ❌ **Allow force pushes** - Keep this DISABLED
- ❌ **Allow deletions** - Keep this DISABLED

### For `main` Branch (Production)

Use the same rules as `develop`, but with stricter requirements:

**Branch name pattern:** `main`

Additional settings:
- ✅ Require approvals: **2** (more reviewers for production)
- ✅ Require deployments to succeed before merging (if you set up environments)
- ✅ Restrict who can push to matching branches (optional)
  - Only allow merge from `develop` branch

---

## CI/CD Pipeline

The repository includes two GitHub Actions workflows:

### 1. CI Workflow (`.github/workflows/ci.yml`)

**Triggers:**
- Pull requests to `develop` or `main`
- Pushes to `develop` or `main`

**Jobs:**

#### `test` - Run All Tests
- Sets up Python 3.11, Poetry, PostgreSQL, Redis
- Runs all 112+ unit tests across 5 services
- Generates coverage reports
- Uploads to Codecov (if configured)
- **Duration:** ~5-7 minutes

#### `lint` - Code Quality Checks
- Black formatting checks
- isort import sorting
- flake8 linting
- mypy type checking
- **Duration:** ~2-3 minutes

#### `docker-build` - Build All Docker Images
- Builds all 5 service Dockerfiles
- Validates Docker builds work
- Uses layer caching for speed
- **Duration:** ~4-6 minutes (parallel)

#### `integration-test` - End-to-End Testing
- Spins up entire stack with Docker Compose
- Health checks all services
- Validates inter-service communication
- **Duration:** ~3-4 minutes

#### `security-scan` - Security Scanning
- Trivy vulnerability scanner
- Uploads results to GitHub Security
- **Duration:** ~2-3 minutes

#### `dependency-check` - Dependency Audit
- Safety check for known vulnerabilities
- Reports security issues
- **Duration:** ~1-2 minutes

#### `status-check` - Final Gate
- Aggregates all job results
- **This is the required status check for branch protection**
- Only passes if critical jobs succeed
- **Duration:** <1 minute

**Total CI Duration:** ~15-20 minutes

### 2. Dependency Update Workflow (`.github/workflows/dependency-update.yml`)

**Triggers:**
- Every Monday at 9 AM UTC (scheduled)
- Manual trigger via GitHub UI

**Purpose:**
- Automatically updates dependencies
- Creates PR to `develop` with changes
- Keeps dependencies current and secure

---

## Required Status Checks

After the first CI run, configure these required status checks in branch protection:

1. Go to **Settings → Branches → Edit rule for `develop`**
2. Under "Require status checks to pass before merging", click "Add checks"
3. Add these checks:
   - `Run Tests`
   - `All Checks Passed`
   - `Docker Build Test` (optional but recommended)

**Important:** Status checks only appear after they've run at least once. You may need to:
1. Create a test PR to `develop`
2. Let the CI run
3. Then add the status checks to branch protection

---

## Workflow

### Branching Strategy

```
main (production, protected)
  ↑
  └── PR (2 approvals) ← develop (protected, 1 approval)
                            ↑
                            ├── PR ← claude/* (AI development)
                            ├── PR ← feature/* (new features)
                            ├── PR ← bugfix/* (bug fixes)
                            ├── PR ← hotfix/* (urgent fixes)
                            └── PR ← deps/* (dependency updates)
```

### Development Workflow

#### 1. Creating a New Feature

```bash
# From develop branch
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/add-analytics-service

# Make changes, commit
git add .
git commit -m "feat: Add Analytics Service"

# Push and create PR
git push -u origin feature/add-analytics-service
```

#### 2. Creating Pull Request

```bash
# Using GitHub CLI
gh pr create \
  --base develop \
  --title "feat: Add Analytics Service" \
  --body "Implements analytics dashboard for merchants..."

# Or via GitHub UI
```

#### 3. PR Review Process

1. **Automated Checks Run**
   - CI workflow starts automatically
   - All tests must pass (112+ tests)
   - Docker builds must succeed
   - Code quality checks run

2. **Code Review**
   - At least 1 reviewer required for `develop`
   - Reviewers check code quality, logic, tests
   - All conversations must be resolved

3. **Merge**
   - Once approved and checks pass, PR can be merged
   - Use "Squash and merge" for clean history
   - Delete branch after merge

#### 4. Releasing to Production

```bash
# Create PR from develop to main
gh pr create \
  --base main \
  --head develop \
  --title "Release v1.0.0" \
  --body "Production release with features X, Y, Z"

# Requires 2 approvals for main
# All CI checks must pass
# Create git tag after merge
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### AI Development Workflow (Claude Code)

When working with Claude Code:

```bash
# Claude creates branches like:
claude/review-platform-foundation-011CUwm1aB53x4c7EDwoNo8X

# Create PR to develop:
gh pr create \
  --base develop \
  --head claude/review-platform-foundation-011CUwm1aB53x4c7EDwoNo8X \
  --title "feat: AI-powered onboarding agent" \
  --body "Implements automated merchant onboarding..."

# After approval and CI passes, merge to develop
# Then delete claude/* branch
```

---

## Code Owners (Optional)

Create a `.github/CODEOWNERS` file to automatically request reviews from specific people/teams:

```
# Global owners
*       @your-username

# Service-specific owners
/services/review_service/     @backend-team
/services/ai_service/         @ai-team @your-username
/services/widget_service/     @frontend-team
/services/email_service/      @backend-team
/services/media_service/      @infrastructure-team

# Infrastructure
/docker-compose*.yml          @devops-team
/.github/workflows/           @devops-team
/Dockerfile.*                 @devops-team

# Documentation
*.md                          @docs-team
```

---

## Secrets Configuration

For CI to work properly, configure these secrets in **Settings → Secrets and variables → Actions**:

### Optional Secrets (for enhanced features):

- `CODECOV_TOKEN` - For coverage reporting
- `ANTHROPIC_API_KEY` - For running AI service integration tests (optional)
- `SLACK_WEBHOOK_URL` - For deployment notifications (optional)

The CI workflow uses test values for required secrets, so it works without configuration.

---

## Monitoring CI/CD

### View Workflow Runs

- Go to **Actions** tab in GitHub
- Click on a workflow run to see details
- Click on individual jobs to see logs
- Download artifacts (coverage reports)

### CI Status Badge

Add to `README.md`:

```markdown
[![CI](https://github.com/{owner}/{repo}/actions/workflows/ci.yml/badge.svg)](https://github.com/{owner}/{repo}/actions/workflows/ci.yml)
```

### Coverage Badge

If using Codecov:

```markdown
[![codecov](https://codecov.io/gh/{owner}/{repo}/branch/develop/graph/badge.svg)](https://codecov.io/gh/{owner}/{repo})
```

---

## Troubleshooting

### CI Failing on First Run

**Problem:** Status checks not appearing in branch protection settings

**Solution:**
1. Create a test PR to `develop`
2. Let CI run at least once
3. Then configure status checks in branch protection

### Tests Failing in CI but Passing Locally

**Problem:** Different environment or dependencies

**Solution:**
```bash
# Use exact CI environment locally
docker run -it python:3.11-slim bash
pip install poetry
poetry install
pytest services/
```

### Docker Build Timeouts

**Problem:** Builds taking too long in CI

**Solution:** Enable layer caching (already configured in workflow)

### Permission Denied on Branch Protection

**Problem:** Can't modify branch protection rules

**Solution:** You need admin access to the repository

---

## Best Practices

1. **Never commit directly to `develop` or `main`**
   - Always use PRs, even for small changes

2. **Keep PRs small and focused**
   - Easier to review
   - Faster CI runs
   - Easier to rollback if needed

3. **Write descriptive commit messages**
   - Follow conventional commits: `feat:`, `fix:`, `docs:`, `chore:`
   - Include ticket numbers if applicable

4. **Add tests for new features**
   - Maintain >90% code coverage
   - Include unit and integration tests

5. **Update documentation**
   - README, DEPLOYMENT.md, API docs
   - Include in the same PR as code changes

6. **Review your own PR first**
   - Check the diff on GitHub
   - Run tests locally
   - Self-review checklist

7. **Respond to review comments promptly**
   - Address feedback
   - Mark conversations as resolved
   - Push fixes to the same PR

8. **Delete branches after merge**
   - Keeps repository clean
   - Enable auto-delete in repository settings

---

## Next Steps

1. ✅ Create `develop` branch
2. ✅ Set up branch protection rules
3. ✅ Create a test PR to trigger CI
4. ✅ Add required status checks
5. ✅ Configure code owners (optional)
6. ✅ Add CI status badges to README
7. ✅ Start using the workflow!

---

**Questions?** Review this guide or check GitHub's [branch protection documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
