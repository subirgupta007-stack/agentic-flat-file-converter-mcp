import base64
import os
from typing import Dict, Any

import requests
from dotenv import load_dotenv

load_dotenv()


class GitHubClient:
    def __init__(self) -> None:
        self.github_token = os.getenv("GITHUB_TOKEN", "").strip()

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json"
        }

        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"

        return headers

    def read_file(
        self,
        owner: str,
        repo: str,
        file_path: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Reads a file from GitHub using the GitHub Contents API.
        Works for public repos. For private repos, set GITHUB_TOKEN in .env.
        """

        url = (
            f"https://api.github.com/repos/{owner}/{repo}"
            f"/contents/{file_path}?ref={branch}"
        )

        response = requests.get(url, headers=self._headers(), timeout=30)

        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to read GitHub file. "
                f"Status: {response.status_code}, Response: {response.text}"
            )

        payload = response.json()

        if payload.get("encoding") != "base64":
            raise RuntimeError("Unsupported GitHub file encoding.")

        raw_bytes = base64.b64decode(payload["content"])

        return {
            "file_name": payload.get("name"),
            "path": payload.get("path"),
            "size": payload.get("size"),
            "sha": payload.get("sha"),
            "content_bytes": raw_bytes,
        }