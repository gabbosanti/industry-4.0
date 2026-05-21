#!/usr/bin/env python3
"""Create a Ditto MQTT connection for telemetry in and desired-state out.

The connection keeps the telemetry flow and adds a target so changing the
control feature desiredProperties in Ditto is translated into an MQTT command.
"""
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "requests",
# ]
# ///

import os
import sys

import requests  # type: ignore[import-not-found]
from requests.auth import HTTPBasicAuth  # type: ignore[import-not-found]

DITTO_BASE = os.getenv("DITTO_BASE_URL", "http://localhost:8081/api/2")
DITTO_USER = os.getenv("DITTO_USER", "devops")
DITTO_PASSWORD = os.getenv("DITTO_PASSWORD", "foobar")
CONNECTION_URL = f"{DITTO_BASE}/connections"

JS_MAPPER = r"""/* JavaScript mapper: receives MQTT telemetry and desired-state changes. */
function parsePayload(headers, textPayload, bytePayload, contentType) {
  var payloadText = textPayload;

  if (!payloadText && bytePayload) {
    payloadText = Ditto.arrayBufferToString(bytePayload);
  }

  if (!payloadText) {
    return null;
  }

  try {
    return JSON.parse(payloadText);
  } catch (e) {
    return null;
  }
}

function mapToDittoProtocolMsg(headers, textPayload, bytePayload, contentType) {
  var payload = parsePayload(headers, textPayload, bytePayload, contentType);

  if (!payload) {
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
        "rpm": payload.rpm,
        "temperature_C": payload.temperature_C,
        "status": payload.status
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
        "x_ms2": payload.x_ms2,
        "y_ms2": payload.y_ms2,
        "z_ms2": payload.z_ms2
      }
    ),
    Ditto.buildDittoProtocolMsg(
      "org.example",
      "pump-001",
      "things",
      "twin",
      "commands",
      "modify",
      "/features/control/properties",
      {"content-type": "application/json"},
      {
        "state": payload.status,
        "supportedStates": ["running", "stopped"]
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

function extractDesiredState(path, value) {
  if (!value || typeof value !== "object") {
    return null;
  }

  if (path === "/features/control/desiredProperties/state" && value.state !== undefined) {
    return value.state;
  }

  if (path === "/features/control/desiredProperties" || path === "/features/control") {
    if (value.desiredProperties && value.desiredProperties.state !== undefined) {
      return value.desiredProperties.state;
    }

    if (value.feature && value.feature.desiredProperties && value.feature.desiredProperties.state !== undefined) {
      return value.feature.desiredProperties.state;
    }
  }

  if (value.feature && value.featureId === "control") {
    if (value.feature.desiredProperties && value.feature.desiredProperties.state !== undefined) {
      return value.feature.desiredProperties.state;
    }
  }

  return null;
}

function mapFromDittoProtocolMsg(namespace, name, group, channel, criterion, action, path, dittoHeaders, value, status, extra) {
  if (criterion !== "events") {
    return null;
  }

  var desiredState = extractDesiredState(path, value);

  if (!desiredState) {
    return null;
  }

  var command = desiredState === "running" ? "start-pump" : "stop-pump";

  var payload = {
    "thingId": namespace + ":" + name,
    "command": command,
    "desiredState": desiredState
  };

  return Ditto.buildExternalMsg(
  {
    "content-type": "application/json",
    "mqtt.retain": "true",
    "mqtt.qos": "1"
  },
  JSON.stringify(payload),
  null,
  "application/json"
);
}

function mapFromDittoProtocolMsgWrapper(dittoProtocolMsg) {
  var topic = dittoProtocolMsg.topic;
  var splitTopic = topic.split("/");
  var namespace = splitTopic[0];
  var name = splitTopic[1];
  var group = splitTopic[2];

  var channel;
  var criterion;
  var action;
  if (splitTopic.length >= 6) {
    channel = splitTopic[3];
    criterion = splitTopic[4];
    action = splitTopic[5];
  } else {
    channel = "none";
    criterion = splitTopic[3];
    action = splitTopic[4];
  }

  return mapFromDittoProtocolMsg(
    namespace,
    name,
    group,
    channel,
    criterion,
    action,
    dittoProtocolMsg.path,
    dittoProtocolMsg.headers,
    dittoProtocolMsg.value,
    dittoProtocolMsg.status,
    dittoProtocolMsg.extra
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
                "enabled": False,
            },
            "enforcement": {
                "input": "{{ source:address }}",
                "filters": ["devices/pump-001/telemetry"],
            },
            "payloadMapping": ["javascript"],
        }
    ],
    "targets": [
        {
        "address": "devices/{{ thing:name }}/commands",
        "topics": ["_/_/things/twin/events"],
        "qos": 1,
            "authorizationContext": ["nginx:ditto"],
            "payloadMapping": ["javascript"],
        }
    ],
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
        create_connection_requests()
    except Exception as e:
        print("Failed to create connection:", e)
        sys.exit(2)


if __name__ == "__main__":
    main()