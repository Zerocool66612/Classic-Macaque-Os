#!/usr/bin/env bash
# Publish only to a new, empty GitHub repository. Never force-push.
set -euo pipefail
cd -- "$(dirname -- "$0")"
repo_url=${1:-}
if [[ ! "$repo_url" =~ ^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(\.git)?/?$ ]]; then
  echo 'Usage: bash publish-github.sh https://github.com/YOUR-NAME/macaque-classic.git' >&2
  exit 1
fi
if ! command -v git >/dev/null; then echo 'Install Git first.' >&2; exit 1; fi
# Authentication is handled by your own Git credential helper or GitHub CLI.
remote_refs=$(git ls-remote "$repo_url")
if [[ -n "$remote_refs" ]]; then echo 'Repository is not empty. Stopping to preserve its existing history.' >&2; exit 1; fi
if [[ ! -d .git ]]; then git init --initial-branch=main; fi
if [[ -z "$(git config user.name || true)" || -z "$(git config user.email || true)" ]]; then
 echo 'Configure your Git author name/email first, then run this script again.' >&2
 exit 1
fi
if git remote get-url origin >/dev/null 2>&1; then
 if [[ "$(git remote get-url origin)" != "$repo_url" ]]; then echo 'The existing origin is different. Stopping without changing it.' >&2; exit 1; fi
else
 git remote add origin "$repo_url"
fi
git add --all
if ! git diff --cached --quiet; then git commit -m 'Macaque Classic 0.22 preview: desktop polish and window animations'; fi
git push --set-upstream origin HEAD:main
printf '\nPublished source to %s\n' "$repo_url"
