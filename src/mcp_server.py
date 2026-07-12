import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from github_client import GitHubClient
from converter import inspect_flat_file, convert_flat_file_bytes_to_windows_csv
from s3_client import S3Client
from metadata_store import MetadataStore

load_dotenv()

mcp = FastMCP("agentic-flat-file-converter")

github_client = GitHubClient()
s3_client = S3Client()
metadata_store = MetadataStore()


@mcp.tool()
def inspect_github_flat_file(
    owner: str,
    repo: str,
    file_path: str,
    branch: str = "main"
) -> Dict[str, Any]:
    """
    Inspect a flat file from GitHub and detect encoding, delimiter, line count,
    and likely column consistency.
    """

    github_file = github_client.read_file(
        owner=owner,
        repo=repo,
        file_path=file_path,
        branch=branch,
    )

    inspection = inspect_flat_file(github_file["content_bytes"])

    return {
        "source": "github",
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "file_path": file_path,
        "file_name": github_file["file_name"],
        "size": github_file["size"],
        "sha": github_file["sha"],
        "inspection": inspection,
    }


@mcp.tool()
def convert_github_flat_file_to_s3_csv(
    owner: str,
    repo: str,
    file_path: str,
    output_bucket: str,
    output_key: str,
    branch: str = "main",
    delimiter: str | None = None
) -> Dict[str, Any]:
    """
    Read a flat file from GitHub, convert it to a Windows-friendly CSV,
    upload the converted CSV to S3, and optionally save job metadata to DynamoDB.
    """

    github_file = github_client.read_file(
        owner=owner,
        repo=repo,
        file_path=file_path,
        branch=branch,
    )

    conversion = convert_flat_file_bytes_to_windows_csv(
        github_file["content_bytes"],
        delimiter=delimiter,
    )

    upload_result = s3_client.upload_bytes(
        bucket=output_bucket,
        key=output_key,
        data=conversion["csv_bytes"],
        content_type="text/csv",
    )

    metadata = {
        "source_type": "github",
        "source_owner": owner,
        "source_repo": repo,
        "source_branch": branch,
        "source_file_path": file_path,
        "source_sha": github_file["sha"],
        "output_bucket": output_bucket,
        "output_key": output_key,
        "output_s3_uri": upload_result["s3_uri"],
        "row_count": conversion["row_count"],
        "delimiter_used": conversion["delimiter_used"],
        "input_encoding": conversion["input_encoding"],
        "min_columns": conversion["min_columns"],
        "max_columns": conversion["max_columns"],
        "status": "COMPLETED",
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }

    metadata_result = metadata_store.save_job(metadata)

    return {
        "status": "COMPLETED",
        "message": "GitHub flat file converted to Windows-friendly CSV and uploaded to S3.",
        "source_file": {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "file_path": file_path,
            "sha": github_file["sha"],
        },
        "output": upload_result,
        "conversion_summary": {
            "row_count": conversion["row_count"],
            "delimiter_used": conversion["delimiter_used"],
            "input_encoding": conversion["input_encoding"],
            "min_columns": conversion["min_columns"],
            "max_columns": conversion["max_columns"],
        },
        "metadata": metadata_result,
    }


@mcp.tool()
def health_check() -> Dict[str, str]:
    """
    Simple health check tool for Claude to verify the MCP server is running file converter.
    """

    return {
        "status": "OK",
        "server": "agentic-flat-file-converter",
    }


if __name__ == "__main__":
    mcp.run()