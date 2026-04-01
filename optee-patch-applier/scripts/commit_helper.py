#!/usr/bin/env python3
"""
Helper script for OPTEE patch application workflow.
Provides utilities for commit listing, log formatting, and error parsing.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path
import json
import re


def run_git_command(repo_path, args):
    """Run a git command and return the output."""
    result = subprocess.run(
        ["git"] + args,
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def get_commit_list(repo_path, start_ref, end_ref, reverse=True):
    """
    Get list of commits between start_ref and end_ref.

    Returns:
        List of dicts with 'hash', 'subject', 'author', 'date'
    """
    direction = "--reverse" if reverse else ""
    _, output, _ = run_git_command(
        repo_path,
        ["log", f"{start_ref}..{end_ref}", direction,
         "--format=%H|%s|%an|%ad", "--date=iso"]
    )

    commits = []
    for line in output.strip().split('\n'):
        if line:
            parts = line.split('|')
            if len(parts) == 4:
                commits.append({
                    'hash': parts[0],
                    'subject': parts[1],
                    'author': parts[2],
                    'date': parts[3]
                })

    return commits


def get_remote_url(repo_path, remote_name="origin"):
    """Get the URL of a git remote."""
    code, output, _ = run_git_command(repo_path, ["remote", "get-url", remote_name])
    if code == 0:
        return output.strip()
    return None


def get_repo_status(repo_path):
    """Get repository status - check for uncommitted changes."""
    code, output, _ = run_git_command(repo_path, ["status", "--porcelain"])
    return output.strip()


def get_current_branch(repo_path):
    """Get current branch name."""
    code, output, _ = run_git_command(repo_path, ["branch", "--show-current"])
    if code == 0:
        return output.strip()
    return None


def get_current_head(repo_path):
    """Get current HEAD commit hash."""
    code, output, _ = run_git_command(repo_path, ["rev-parse", "HEAD"])
    if code == 0:
        return output.strip()
    return None


def format_log_entry(status, commit_hash, message, details=""):
    """Format a log entry for the patch application log."""
    timestamp = datetime.now().isoformat()
    entry = f"[{status}] {commit_hash[:8]} - {message}"
    if details:
        entry += f"\n  Details: {details}"
    return entry


def parse_build_errors(log_file):
    """
    Parse build log for common error patterns.

    Returns:
        List of error dicts with 'file', 'line', 'message', 'context'
    """
    errors = []

    # Common error patterns
    patterns = [
        # GCC compilation errors
        r'([^:]+):(\d+):\d*:\s*error:\s*(.+)',
        # Linker errors
        r'undefined reference to [`\'](.+)[`\'"]',
        # Make errors
        r'make:\s*\*\*\s*\[(.+)\]',
    ]

    try:
        with open(log_file, 'r') as f:
            content = f.read()

        for pattern in patterns:
            for match in re.finditer(pattern, content):
                if match.group(0):  # Not empty
                    errors.append({
                        'raw': match.group(0),
                        'groups': match.groups()
                    })
    except FileNotFoundError:
        pass

    return errors


class PatchLogger:
    """Logger for tracking patch application progress."""

    def __init__(self, repo_path, start_ref, end_ref, build_command):
        self.repo_path = repo_path
        self.start_ref = start_ref
        self.end_ref = end_ref
        self.build_command = build_command
        self.entries = []
        self.start_time = datetime.now()

    def log(self, status, commit_hash, message, details=""):
        """Add a log entry."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'commit': commit_hash,
            'message': message,
            'details': details
        }
        self.entries.append(entry)

    def summary(self):
        """Get summary statistics."""
        stats = {
            'total': len(self.entries),
            'applied': len([e for e in self.entries if e['status'] == 'APPLIED']),
            'conflict': len([e for e in self.entries if e['status'] == 'FAILED_CONFLICT']),
            'build': len([e for e in self.entries if e['status'] == 'FAILED_BUILD']),
            'skipped': len([e for e in self.entries if e['status'] == 'SKIPPED']),
        }
        return stats

    def save(self, output_file):
        """Save log to file."""
        with open(output_file, 'w') as f:
            f.write(f"OPTEE Patch Application Log\n")
            f.write(f"Started: {self.start_time.isoformat()}\n")
            f.write(f"Repository: {self.repo_path}\n")
            f.write(f"Commit Range: {self.start_ref}..{self.end_ref}\n")
            f.write(f"Build Command: {self.build_command}\n")
            f.write(f"\n{'='*60}\n\n")

            for entry in self.entries:
                f.write(f"[{entry['status']}] {entry['commit'][:8]} - {entry['message']}\n")
                if entry['details']:
                    f.write(f"  Details: {entry['details']}\n")

            stats = self.summary()
            f.write(f"\n{'='*60}\n")
            f.write(f"Summary:\n")
            f.write(f"  Total: {stats['total']}\n")
            f.write(f"  Applied: {stats['applied']}\n")
            f.write(f"  Conflicts: {stats['conflict']}\n")
            f.write(f"  Build failures: {stats['build']}\n")
            f.write(f"  Skipped: {stats['skipped']}\n")


def main():
    """CLI interface for common operations."""
    if len(sys.argv) < 2:
        print("Usage: commit_helper.py <command> [args...]")
        print("Commands:")
        print("  list-commits <repo> <start> <end>")
        print("  check-status <repo>")
        print("  parse-errors <log-file>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list-commits" and len(sys.argv) == 5:
        repo, start, end = sys.argv[2], sys.argv[3], sys.argv[4]
        commits = get_commit_list(repo, start, end)
        print(f"Found {len(commits)} commits:")
        for i, c in enumerate(commits, 1):
            print(f"{i:3d}. {c['hash'][:8]} - {c['subject']}")

    elif command == "check-status" and len(sys.argv) == 3:
        repo = sys.argv[2]
        status = get_repo_status(repo)
        branch = get_current_branch(repo)
        head = get_current_head(repo)

        print(f"Repository: {repo}")
        print(f"Branch: {branch}")
        print(f"HEAD: {head}")
        print(f"Status: {'Clean' if not status else 'Dirty'}")
        if status:
            print(f"Changed files:\n{status}")

    elif command == "parse-errors" and len(sys.argv) == 3:
        log_file = sys.argv[2]
        errors = parse_build_errors(log_file)
        print(f"Found {len(errors)} errors:")
        for e in errors:
            print(f"  - {e['raw']}")

    else:
        print(f"Unknown or incomplete command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
