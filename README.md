# git-zap

git-zap is a command line tool for quickly creating detached git worktree checkouts.

## Usage

```bash
git-zap OWNER/REPO /path/to/worktree
```

This command creates a worktree for the specified repository at the given path,
reusing a global store of repository checkouts.
