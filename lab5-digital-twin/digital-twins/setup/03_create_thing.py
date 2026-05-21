#!/usr/bin/env python3
"""Create the Ditto Thing from THING_MODEL via Ditto HTTP API."""
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "requests",
# ]
# ///

import json

import requests  # type: ignore[import-not-found]
from requests.auth import HTTPBasicAuth  # type: ignore[import-not-found]

DITTO_BASE = "http://localhost:8080/api/2"
THING_ID = "org.example:pump-001"
DITTO_USER = "ditto"
DITTO_PASSWORD = "ditto"

THING_MODEL = """{
  "thingId": "org.example:pump-001",
  "policyId": "org.example:pump-policy",
  "attributes": {
    "manufacturer": "ACME Pumps Ltd.",
    "serialNumber": "SN-001-2026",
    "installationSite": "Plant A - Bay 5"
  },
  "features": {
    "motor": {
      "type": "pump.motor",
      "properties": {
        "rpm": 0,
        "temperature_C": 20.0,
        "status": "stopped"
      }
    },
    "vibration": {
      "type": "pump.vibration",
      "properties": {
        "x_ms2": 0.0,
        "y_ms2": 0.0,
        "z_ms2": 0.0
      }
    }
  }
}"""


def create_thing_requests():
    url = f"{DITTO_BASE}/things/{THING_ID}"
    print(f"PUT {url} (using HTTP)")
    r = requests.put(
        url,
        json=json.loads(THING_MODEL),
        auth=HTTPBasicAuth(DITTO_USER, DITTO_PASSWORD),
        headers={"Content-Type": "application/json"},
    )
    if r.status_code not in (200, 201, 204):
        print(f"create_thing_requests: HTTP {r.status_code} - {r.text}")
    r.raise_for_status()
    print("Thing created (HTTP).")


def main():
    try:
        create_thing_requests()
    except Exception as e:
        print("Failed to create Thing via HTTP API:", e)
        raise


if __name__ == "__main__":
    main()
