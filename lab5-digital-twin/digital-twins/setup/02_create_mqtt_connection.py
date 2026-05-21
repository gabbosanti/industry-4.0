#!/usr/bin/env python3
"""Create Ditto MQTT connection with JavaScript payload mapper.

Connections are administrative resources. The Ditto protocol SDK does not
manage connections, so this script uses the Ditto admin REST API.
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

DITTO_BASE = os.getenv("DITTO_BASE_URL", "http://localhost:8081/api/2")
DITTO_USER = os.getenv("DITTO_USER", "devops")
DITTO_PASSWORD = os.getenv("DITTO_PASSWORD", "foobar")
CONNECTION_URL = f"{DITTO_BASE}/connections"

JS_MAPPER = r"""/* JavaScript mapper: receives MQTT payload and returns Ditto protocol messages. */
function mapToDittoProtocolMsg(headers, textPayload, bytePayload, contentType) {
  var payloadText = textPayload;

  if (!payloadText && bytePayload) {
    payloadText = Ditto.arrayBufferToString(bytePayload);
  }

  if (!payloadText) {
    return null;
  }

  var p;
  try {
    p = JSON.parse(payloadText);
  } catch (e) {
    return null;
  }

  return [
    Ditto.buildDittoProtocolMsg(
      "org.example",
      "pump-001",
      "things",
      "twin",
      "commands",
      "modify",
      "/features/motor/properties",
      {"content-type": "application/json"},
      {
        "rpm": p.rpm,
        "temperature_C": p.temperature_C,
        "status": p.status
      }
    ),
    Ditto.buildDittoProtocolMsg(
      "org.example",
      "pump-001",
      "things",
      "twin",
      "commands",
      "modify",
      "/features/vibration/properties",
      {"content-type": "application/json"},
      {
        "x_ms2": p.x_ms2,
        "y_ms2": p.y_ms2,
        "z_ms2": p.z_ms2
      }
    )
  ];
}

function mapToDittoProtocolMsgWrapper(externalMsg) {
  return mapToDittoProtocolMsg(
    externalMsg.headers,
    externalMsg.textPayload,
    externalMsg.bytePayload,
    externalMsg.contentType
  );
}
"""

connection = {
  "name": "org-example:pump-mqtt-conn",
    "connectionType": "mqtt",
    "connectionStatus": "open",
    "uri": "tcp://mosquitto:1883",
    "sources": [
        {
            "addresses": ["devices/pump-001/telemetry"],
            "authorizationContext": ["nginx:ditto"],
            "consumerCount": 1,
          "qos": 0,
            "replyTarget": {
                "enabled": False
            },
            "enforcement": {
                "input": "{{ source:address }}",
                "filters": ["devices/pump-001/telemetry"],
            },
            "payloadMapping": ["javascript"],
        }
    ],
    "targets": [],
    "mappingDefinitions": {
        "javascript": {
            "mappingEngine": "JavaScript",
            "options": {
                "incomingScript": JS_MAPPER,
                "outgoingScript": JS_MAPPER,
            },
        }
    },
}


def connection_exists(conn_id: str) -> bool:
    url = f"{CONNECTION_URL}/{conn_id}"
    r = requests.get(url, auth=HTTPBasicAuth(DITTO_USER, DITTO_PASSWORD))
    return r.status_code == 200


def create_connection_requests():
    url = f"{CONNECTION_URL}/{connection['name']}"
    print(f"PUT {url}")
    r = requests.put(
        url,
        json=connection,
        auth=HTTPBasicAuth(DITTO_USER, DITTO_PASSWORD),
        headers={"Content-Type": "application/json"},
    )
    if r.status_code not in (200, 201, 204):
        print(f"create_connection_requests: HTTP {r.status_code} - {r.text}")
    r.raise_for_status()
    print("Connection created (HTTP).")


def main():
    try:
        # conn_id = connection["name"]
        # if connection_exists(conn_id):
        #     print(f"Connection {conn_id} already exists; skipping creation.")
        #     return
        create_connection_requests()
    except Exception as e:
        print("Failed to create connection:", e)
        sys.exit(2)


if __name__ == "__main__":
    main()
