---
name: optee-patch-applier
description: Apply OPTEE community code updates to local fork as patches, with automated build verification after each patch. Use when the user needs to sync their local OPTEE repository with upstream community code, merge upstream commits, or apply patch files while ensuring each change compiles successfully. This skill handles cherry-picking commits, detecting conflicts, running builds, and analyzing compilation errors for OPTEE projects.
---

# OPTEE Patch Applier

This skill helps you apply OPTEE community code updates to your local repository with build verification after each patch.

## When to Use This Skill

Use this skill when:
- Applying upstream OPTEE community commits to your local fork
- Syncing your local OPTEE repository with the latest community code
- Applying patch files to OPTEE codebase
- Merging OPTEE updates while ensuring compilation succeeds
- Need to identify which upstream commit breaks your local build

## Workflow Overview

The core workflow is:
1. **Setup** - Gather repository paths, build commands, and commit range
2. **Branch** - Create a working branch from your current state
3. **Apply** - Cherry-pick each commit from upstream
4. **Verify** - Run build after each successful commit application
5. **Handle Errors** - Analyze failures and propose solutions
6. **Continue** - Only proceed to next commit after current one succeeds

## Step 1: Initial Setup

Before starting, collect the following information from the user:

**Required Information:**
- `REPO_PATH`: Path to local OPTEE repository
- `UPSTREAM_URL`: URL to OPTEE community repository (default: https://github.com/OP-TEE/optee_os.git)
- `START_COMMIT`: Starting commit hash, tag, or branch (e.g., `4.5.0`, `abc123...`)
- `END_COMMIT`: Ending commit hash, tag, or branch (e.g., `4.6.0`, `def456...`, or `master`)
- `BUILD_COMMAND`: The full command to compile (e.g., `make PLATFORM=vexpress PLATFORM_FLAVOR=qemu_virt`)

**Optional Information:**
- `BRANCH_NAME`: Name for the working branch (default: `cherry-pick-{timestamp}`)
- `COMPONENT`: Which OPTEE component to build (`optee_os`, `optee_client`, etc.)

Ask the user for these values if not provided. Confirm before proceeding.

## Step 2: Environment Validation

Before starting the patch application:

1. **Verify repository state:**
   ```bash
   cd $REPO_PATH
   git status --porcelain
   ```
   - If there are uncommitted changes, ask the user if they want to stash or commit them first

2. **Fetch upstream commits:**
   ```bash
   git fetch $UPSTREAM_URL
   ```

3. **Get commit list:**
   ```bash
   git log --oneline $START_COMMIT..$END_COMMIT --reverse
   ```
   - Show the user how many commits will be applied
   - Ask for confirmation before proceeding

## Step 3: Create Working Branch

Create a new branch for the cherry-pick operation:

```bash
cd $REPO_PATH
git checkout -b $BRANCH_NAME
```

Record the starting point for potential rollback:
- Save `HEAD` commit hash before starting
- Create a log file at `~/.optee-patch-log-{timestamp}.txt`

## Step 4: Cherry-Pick Loop

For each commit in the range (in chronological order):

### 4.1 Apply the Commit

```bash
git cherry-pick $COMMIT_HASH
```

### 4.2 Check Result

**If cherry-pick succeeds:**
- Proceed to build verification (Step 4.3)

**If cherry-pick fails with conflicts:**
1. Show the conflicting files:
   ```bash
   git status
   ```
2. Show the conflict markers:
   ```bash
   git diff
   ```
3. **PAUSE and inform the user:**
   - List all conflicting files
   - Show a snippet of each conflict
   - Ask the user how to proceed:
     - Abort this cherry-pick (`git cherry-pick --abort`)
     - Skip this commit (`git cherry-pick --skip`)
     - Resolve conflicts manually (user will resolve, then you continue)
4. **DO NOT:**
   - Automatically resolve conflicts
   - Modify the commit content or message
   - Apply the same commit twice

### 4.3 Build Verification

After successful cherry-pick, run the build:

```bash
cd $REPO_PATH
$BUILD_COMMAND
```

**Capture build output:**
- Save stdout and stderr to a temporary log file
- Show the last 50 lines of output to the user

**If build succeeds:**
- Mark commit as applied successfully
- Continue to next commit

**If build fails:**
1. **PAUSE and analyze:**
   - Identify the error type (compilation error, linker error, missing dependency, etc.)
   - Extract relevant error messages
   - Show the error context (affected file, line number, error message)
2. **Propose solutions:**
   - Suggest specific code changes to fix the issue
   - Reference the OPTEE documentation if relevant
   - Show before/after code snippets for proposed fixes
3. **Wait for user decision:**
   - Apply the proposed fix
   - Skip this commit
   - Abort the entire process
   - User will fix manually
4. **DO NOT:**
   - Proceed to next commit without resolution
   - Add redundant code or unnecessary includes
   - Modify the upstream commit

## Step 5: Logging and Progress Tracking

Maintain a log file throughout the process:

**Log format:**
```
OPTEE Patch Application Log
Started: {timestamp}
Repository: {REPO_PATH}
Commit Range: {START_COMMIT}..{END_COMMIT}
Build Command: {BUILD_COMMAND}

[APPLIED] {commit_hash} - {commit_message}
[FAILED_CONFLICT] {commit_hash} - {commit_message}
[FAILED_BUILD] {commit_hash} - {commit_message}
  Error: {error_summary}
[SKIPPED] {commit_hash} - {commit_message}
```

After each commit, update the log and show progress:
- `Applied: X/Y commits (Z failed, S skipped)`
- `Current commit: {hash} - {message}`

## Step 6: Completion

When all commits are processed:

1. **Show summary:**
   - Total commits processed
   - Successfully applied and built
   - Failed (conflicts + build errors)
   - Skipped

2. **Provide next steps:**
   - If all succeeded: "All commits applied successfully. You can merge this branch."
   - If some failed: "Review the failed commits and decide whether to fix or skip them."

3. **Save the log:**
   - Copy log file to `$REPO_PATH/optee-patch-log-{timestamp}.txt`

## Error Categories and Analysis

When build fails, categorize the error:

| Error Type | Description | Common Solutions |
|------------|-------------|------------------|
| **Compilation Error** | Syntax error, undefined reference | Update code for new API, add missing includes |
| **Linker Error** | Undefined symbol during linking | Check for removed functions, update linker scripts |
| **Configuration Error** | Missing platform/config | Update platform configuration files |
| **Dependency Error** | Missing external library | Update build dependencies |

## OPTEE Build System Notes

OPTEE has multiple components that may need separate builds:

- **optee_os**: `make PLATFORM=... PLATFORM_FLAVOR=...`
- **optee_client**: `make`
- **optee_test**: `make -f Makefile.test`

The build command should specify the platform and flavor explicitly:
```bash
# Example for QEMU
make PLATFORM=vexpress PLATFORM_FLAVOR=qemu_virt

# Example for specific hardware
make PLATFORM=imx PLATFORM_FLAVOR=mx6qsabrelite
```

## Important Principles

**DO:**
- Work on a separate branch
- Apply commits in chronological order
- Build after each successful commit
- Pause on errors and wait for user input
- Log everything for later review
- Respect commit messages and authorship

**DON'T:**
- Apply the same commit multiple times
- Modify upstream commit content
- Modify commit messages or metadata
- Add unnecessary code or workarounds
- Proceed to next commit with unresolved errors
- Assume what the user wants - always ask

## Troubleshooting

**"Upstream repository not found"**
- Check the remote URL with `git remote -v`
- Add the upstream remote: `git remote add upstream https://github.com/OP-TEE/optee_os.git`

**"Build takes too long"**
- Consider incremental builds: `make -j$(nproc)`
- Ask user if they want to skip full build for certain commits

**"Too many conflicts"**
- Suggest rebasing against the target base first
- Consider starting from a closer common ancestor

## Example Session

```
User: Apply OPTEE 4.6.0 commits to my repo

Claude: I'll help you apply OPTEE community updates. I need:
- Repository path: /home/user/optee_os
- Build command: make PLATFORM=vexpress PLATFORM_FLAVOR=qemu_virt
- Start: 4.5.0
- End: 4.6.0

[...creates branch, applies commits...]

Claude: Commit abc1234 applied. Building...
[...build output...]
Build succeeded! (1/15)

Claude: Commit def5678 applied. Building...
[...build error...]
Build failed in core/arch/arm/mm/tee_pager.c:123:
error: 'tee_pager_add_area' undefined

This function was renamed in commit xyz. Would you like me to:
1. Update the call to use the new API
2. Skip this commit
3. Abort

User: 1

Claude: I'll update the call. Changing:
  tee_pager_add_area(...)
To:
  tee_pager_add_area_area(...)

Building again... Success! (2/15)
```
