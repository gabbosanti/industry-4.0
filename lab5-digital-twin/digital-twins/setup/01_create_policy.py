#!/usr/bin/env python3
"""Create Ditto policy for the lab.

This script uses the Ditto admin REST API to create a policy required
by the lab. The Ditto protocol SDK does not expose admin endpoints,
so we manage policies via HTTP.
"""
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "requests",
# ]
# ///

import os
import sys
import requests
from requests.auth import HTTPBasicAuth

POLICY_ID = "org.example:pump-policy"
DITTO_BASE = "http://localhost:8080/api/2"
DITTO_USER = os.getenv("DITTO_USER", "ditto")
DITTO_PASSWORD = os.getenv("DITTO_PASSWORD", "ditto")
DITTO_SUBJECT = os.getenv("DITTO_SUBJECT", f"nginx:{DITTO_USER}")

policy = {
    "policyId": POLICY_ID,
    "entries": {
        "owner": {
            "subjects": {
                DITTO_SUBJECT: {
                    "type": "nginx basic auth user"
                }
            },
            "resources": {
                "thing:/": {
                    "grant": ["READ", "WRITE"],
                    "revoke": []
                },
                "policy:/": {
                    "grant": ["READ", "WRITE"],
                    "revoke": []
                },
                "message:/": {
                    "grant": ["READ", "WRITE"],
                    "revoke": []
                }
            }
        }
    },
}


def policy_exists():
    url = f"{DITTO_BASE}/policies/{POLICY_ID}"
    r = requests.get(url, auth=HTTPBasicAuth(DITTO_USER, DITTO_PASSWORD))
    if r.status_code == 200:
        return True
    print(f"policy_exists: HTTP {r.status_code} - {r.text}")
    return False


def create_policy_requests():
    url = f"{DITTO_BASE}/policies/{POLICY_ID}"
    print(f"PUT {url}")
    r = requests.put(url, json=policy, auth=HTTPBasicAuth(DITTO_USER, DITTO_PASSWORD), headers={"Content-Type": "application/json"})
    if r.status_code in (200, 201, 204):
        print("Policy created (HTTP).")
        return
    # print response body for debugging (common cause: 401/403)
    print(f"create_policy_requests: HTTP {r.status_code} - {r.text}")
    r.raise_for_status()


def main():
    try:
        if policy_exists():
            print(f"Policy {POLICY_ID} already exists; skipping creation.")
            return
        create_policy_requests()
    except Exception as e:
        print("Failed to create policy:", e)
        sys.exit(2)


if __name__ == "__main__":
    main()
