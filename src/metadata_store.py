import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

import boto3
from dotenv import load_dotenv

load_dotenv()


class MetadataStore:
    def __init__(self) -> None:
        self.table_name = os.getenv("DYNAMODB_TABLE", "").strip()
        self.region = os.getenv("AWS_REGION", "us-east-1")

        self.dynamodb = boto3.resource("dynamodb", region_name=self.region)

    def save_job(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        if not self.table_name:
            return {
                "saved": False,
                "reason": "DYNAMODB_TABLE not configured"
            }

        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        item = {
            "job_id": job_id,
            "created_at": now,
            **metadata,
        }

        table = self.dynamodb.Table(self.table_name)
        table.put_item(Item=item)

        return {
            "saved": True,
            "job_id": job_id,
            "table": self.table_name,
        }