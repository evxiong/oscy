"""
Script for revalidating cache in Next.js frontend.

Usage:
    python -m src.oscy.revalidate <tag> [--local]

    <tag> is the Next.js cache tag to revalidate

    -l, --local
        revalidate cache tag in local Next.js instance running at
        `localhost:3000`; if not present, default to production instance

Example:
    python -m src.oscy.revalidate version --local
"""

import argparse
import hashlib
import hmac
import json
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv(override=True)


def generate_signature(timestamp: str, body_text: str) -> str:
    REVALIDATION_SECRET = os.environ["REVALIDATION_SECRET"]

    key = REVALIDATION_SECRET.encode("utf-8")
    message = f"{timestamp}.{body_text}".encode("utf-8")

    signature = hmac.new(key, message, hashlib.sha256).hexdigest()
    return signature


def revalidate(tag: str, local: bool = False):
    base_url = "http://localhost:3000" if local else "https://oscy.evanxiong.com"
    url = f"{base_url}/api/revalidate"

    timestamp = str(int(time.time()))
    body = {"tag": tag}
    body_text = json.dumps(body, separators=(",", ":"))

    signature = generate_signature(timestamp, body_text)

    headers = {
        "Content-Type": "application/json",
        "x-timestamp": timestamp,
        "x-signature": signature,
    }

    response = requests.post(url, headers=headers, data=body_text, timeout=5)

    if not response.ok:
        raise RuntimeError(
            f"Revalidation failed ({response.status_code}): {response.text}"
        )

    return response.json()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("tag")
    parser.add_argument("-l", "--local", action="store_true")

    args = parser.parse_args()

    revalidate(args.tag, args.local)
