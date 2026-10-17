#!/usr/bin/env python3
"""
deploy_to_github.py
Automated 1-Click Code & File Deployer for JEE 2028 Study Tracker.
Pushes all project code, configurations, study data, and chapter PDFs directly
to your GitHub repository using the GitHub API (no git installation required).
Streamlit Community Cloud automatically rebuilds your website upon receiving the commit.
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.error

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SECRETS_FILE = os.path.join(PROJECT_ROOT, ".streamlit", "secrets.toml")

TRACKED_FILES = [
    "app.py",
    "data_manager.py",
    "analytics.py",
    "requirements.txt",
    "study_data.json",
    ".gitignore",
    ".streamlit/config.toml",
]

def load_secrets():
    token = ""
    repo = ""
    branch = "main"
    if os.path.exists(SECRETS_FILE):
        try:
            with open(SECRETS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GITHUB_TOKEN"):
                        token = line.split("=", 1)[1].strip().strip('"\'')
                    elif line.startswith("GITHUB_REPO"):
                        repo = line.split("=", 1)[1].strip().strip('"\'')
                    elif line.startswith("GITHUB_BRANCH"):
                        branch = line.split("=", 1)[1].strip().strip('"\'')
        except Exception:
            pass
    return token, repo, branch

def save_secrets(token, repo, branch="main"):
    os.makedirs(os.path.dirname(SECRETS_FILE), exist_ok=True)
    content = f'GITHUB_TOKEN = "{token}"\nGITHUB_REPO = "{repo}"\nGITHUB_BRANCH = "{branch}"\n'
    with open(SECRETS_FILE, "w", encoding="utf-8") as f:
        f.write(content)

def get_file_sha(owner, repo_name, file_path, token, branch="main"):
    """Fetches existing file SHA from GitHub if file exists."""
    url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{file_path}?ref={branch}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "JEE-Deployer"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("sha")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise

def upload_file_to_github(owner, repo_name, file_rel_path, token, branch="main"):
    """Uploads or updates a file on GitHub using the Contents API."""
    abs_path = os.path.join(PROJECT_ROOT, file_rel_path)
    if not os.path.exists(abs_path):
        return False, "File not found locally"

    with open(abs_path, "rb") as f:
        content_bytes = f.read()

    b64_content = base64.b64encode(content_bytes).decode("utf-8")
    existing_sha = get_file_sha(owner, repo_name, file_rel_path, token, branch)

    payload = {
        "message": f"Auto-deploy update: {file_rel_path}",
        "content": b64_content,
        "branch": branch
    }
    if existing_sha:
        payload["sha"] = existing_sha

    url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{file_rel_path}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "JEE-Deployer"
        },
        method="PUT"
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return True, "OK"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print("🚀 JEE 2028 Study Tracker — Automated Website Deployer")
    print("=" * 60)

    token, repo_full, branch = load_secrets()

    if not token:
        print("\n[?] Enter your GitHub Personal Access Token (classic, with 'repo' scope):")
        token = input("Token: ").strip()

    if not repo_full:
        print("\n[?] Enter your GitHub repository name in format 'Username/Repo' (e.g. rachit/jee-study-tracker):")
        repo_full = input("Repository: ").strip()

    if not token or not repo_full or "/" not in repo_full:
        print("\n❌ Invalid Token or Repository format. Exiting.")
        sys.exit(1)

    owner, repo_name = repo_full.split("/", 1)
    save_secrets(token, repo_full, branch)

    print(f"\n📦 Deploying to: https://github.com/{owner}/{repo_name} (branch: {branch})")
    print("-" * 60)

    # Gather files to deploy
    files_to_upload = list(TRACKED_FILES)
    res_dir = os.path.join(PROJECT_ROOT, "chapter_resources")
    if os.path.exists(res_dir):
        for fname in os.listdir(res_dir):
            fpath = os.path.join(res_dir, fname)
            if os.path.isfile(fpath) and not fname.startswith("."):
                files_to_upload.append(f"chapter_resources/{fname}")

    success_count = 0
    fail_count = 0

    for f_rel in files_to_upload:
        sys.stdout.write(f"  Uploading {f_rel:35s} ... ")
        sys.stdout.flush()
        ok, msg = upload_file_to_github(owner, repo_name, f_rel, token, branch)
        if ok:
            print("✅ OK")
            success_count += 1
        else:
            print(f"❌ Failed: {msg}")
            fail_count += 1

    print("-" * 60)
    if fail_count == 0:
        print(f"\n🎉 Successfully deployed all {success_count} files to GitHub!")
        print("⚡ Streamlit Community Cloud will automatically rebuild your live website within 30 seconds.")
    else:
        print(f"\n⚠️ Deployment finished with {success_count} uploaded, {fail_count} failed.")

if __name__ == "__main__":
    main()

