import os
import re
import zipfile
import tempfile
from pathlib import Path

import requests

GITHUB_URL_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(?:\.git)?/?$"
)

def download_github_repo(owner:str,repo:str) ->Path:
    "Downloads a public Github Repo as a zip and extracts it to a temp dir"

    token=os.environ.get("GITHUB_TOKEN")
    headers={'Authorization':f'Bearer {token}'} if token else {}

    # Get the Deafult Branch from the repo
    api_url=f'https://api.github.com/repos/{owner}/{repo}'
    resp=requests.get(api_url,headers=headers,timeout=10)
    if resp.status_code==404:
        raise ValueError(f"Repo '{owner}/{repo}' not found or is private")

    if resp.status_code == 403:
        raise RuntimeError(
            "GitHub API rate limit hit. Set a GITHUB_TOKEN env var "
            "(a basic personal access token) to raise the limit."
        )
    resp.raise_for_status()
    default_branch=resp.json()['default_branch']

    # Download that Zip for that branch
    zip_url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{default_branch}"
    zip_resp = requests.get(zip_url, timeout=30)
    zip_resp.raise_for_status()

    # Extract the Zip file in temp_dir
    temp_dir=Path(tempfile.mkdtemp(prefix=f"{repo}_"))
    zip_path=temp_dir/"repo.zip"
    zip_path.write_bytes(zip_resp.content)

    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(temp_dir)
    zip_path.unlink()

    extracted_dirs = [p for p in temp_dir.iterdir() if p.is_dir()]
    if len(extracted_dirs) != 1:
        raise RuntimeError(f"Unexpected zip contents for {owner}/{repo}")
    return extracted_dirs[0]

def resolve_repo_source(source:str) ->Path:
    """Takes a github repo url or a local folder path and returns a local path to the repo
    contents on disk"""
    url=GITHUB_URL_RE.match(source.strip())
    if url:
        return download_github_repo(url.group('owner'),url.group('repo'))

    local_path=Path(source).expanduser().resolve()
    if not local_path.is_dir():
        raise ValueError(f"{source} is not a valid repo url or directory")
    return local_path