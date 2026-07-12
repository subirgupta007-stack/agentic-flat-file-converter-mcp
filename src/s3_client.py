import os
from typing import Dict, Any

import boto3
from dotenv import load_dotenv

load_dotenv()


class S3Client:
    def __init__(self) -> None:
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.client = boto3.client("s3", region_name=self.region)

    def upload_bytes(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "text/csv"
    ) -> Dict[str, Any]:
        self.client.put_object(
            Bucket=bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

        return {
            "bucket": bucket,
            "key": key,
            "s3_uri": f"s3://{bucket}/{key}",
        }