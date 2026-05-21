#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "paho-mqtt",
# ]
# ///

import json
import random
import time
from datetime import datetime
import os
import sys
import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = "devices/pump-001/telemetry"
COMMAND_TOPIC = "devices/pump-001/commands"
PUBLISH_INTERVAL = 1  # seconds
AMBIENT_TEMPERATURE_C = 28.0
RUNNING_TARGET_RPM = 2900

device_state = {
    "running": True,
    "rpm": 1200,
    "temperature_C": 38.0,
    "x_ms2": 0.18,
    "y_ms2": 0.21,
    "z_ms2": 0.17,
    "last_command": "start-pump",
}

client = mqtt.Client()
connected = False

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_connected():
    global connected

    while not connected:
        try:
            print(f"[{timestamp()}] Reconnecting to MQTT broker at {BROKER}:{PORT}...")
            client.reconnect()
            time.sleep(1)
            if connected:
                return
        except Exception as exc:
            print(f"[{timestamp()}] Reconnect failed: {exc}")
            time.sleep(5)


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def update_running_state():
    if device_state["running"]:
        device_state["rpm"] = clamp(
            device_state["rpm"] + random.randint(120, 220),
            0,
            RUNNING_TARGET_RPM,
        )
        device_state["temperature_C"] = round(
            clamp(
                device_state["temperature_C"] + random.uniform(0.45, 0.95),
                AMBIENT_TEMPERATURE_C,
                96.0,
            ),
            1,
        )
        vibration_base = 0.08 + (device_state["rpm"] / RUNNING_TARGET_RPM) * 0.9
        vibration_spread = 0.08
    else:
        device_state["rpm"] = clamp(
            device_state["rpm"] - random.randint(350, 650),
            0,
            RUNNING_TARGET_RPM,
        )
        device_state["temperature_C"] = round(
            clamp(
                device_state["temperature_C"] - random.uniform(0.55, 1.15),
                AMBIENT_TEMPERATURE_C,
                96.0,
            ),
            1,
        )
        vibration_base = 0.01 if device_state["rpm"] == 0 else 0.05
        vibration_spread = 0.02

    if device_state["running"] and device_state["rpm"] >= RUNNING_TARGET_RPM:
        device_state["rpm"] = RUNNING_TARGET_RPM

    device_state["x_ms2"] = round(clamp(random.uniform(vibration_base - vibration_spread, vibration_base + vibration_spread), 0.0, 2.2), 2)
    device_state["y_ms2"] = round(clamp(random.uniform(vibration_base - vibration_spread, vibration_base + vibration_spread), 0.0, 2.2), 2)
    device_state["z_ms2"] = round(clamp(random.uniform(vibration_base - vibration_spread, vibration_base + vibration_spread), 0.0, 2.2), 2)


def apply_command(command_payload):
    command = None
    if isinstance(command_payload, dict):
        command = command_payload.get("command") or command_payload.get("action") or command_payload.get("messageSubject")
        if command_payload.get("state") == "running":
            command = "start-pump"
        elif command_payload.get("state") == "stopped":
            command = "stop-pump"
    elif isinstance(command_payload, str):
        command = command_payload.strip()

    if command in {"stop-pump", "stop", "halt"}:
        device_state["running"] = False
        device_state["last_command"] = "stop-pump"
        print(f"[{timestamp()}] Received stop command on {COMMAND_TOPIC}; slowing down pump")
    elif command in {"start-pump", "start", "run"}:
        device_state["running"] = True
        device_state["last_command"] = "start-pump"
        print(f"[{timestamp()}] Received start command on {COMMAND_TOPIC}; ramping pump up")
    elif command is not None:
        print(f"[{timestamp()}] Ignoring unsupported command payload: {command_payload}")


def on_message(client, userdata, msg):
    payload_text = msg.payload.decode("utf-8", errors="replace") if msg.payload else ""

    try:
        payload = json.loads(payload_text) if payload_text else {}
    except json.JSONDecodeError:
        payload = payload_text

    apply_command(payload)

def publish_loop():
    global connected

    try:
        while True:
            if not connected:
                ensure_connected()

            update_running_state()

            status = "running" if device_state["rpm"] > 0 else "stopped"

            payload = {
                "rpm": device_state["rpm"],
                "temperature_C": device_state["temperature_C"],
                "status": status,
                "x_ms2": device_state["x_ms2"],
                "y_ms2": device_state["y_ms2"],
                "z_ms2": device_state["z_ms2"],
            }

            result = client.publish(TOPIC, json.dumps(payload))
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                print(f"[{timestamp()}] Publish failed with code {result.rc}; will reconnect")
                connected = False
                ensure_connected()
                continue

            print(
                f"[{timestamp()}] Published → status={status}, rpm={device_state['rpm']}, "
                f"temp={device_state['temperature_C']}°C, vib=({device_state['x_ms2']}, "
                f"{device_state['y_ms2']}, {device_state['z_ms2']})"
            )
            time.sleep(PUBLISH_INTERVAL)
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received, disconnecting...")
        client.disconnect()
        sys.exit(0)

def on_connect(client, userdata, flags, rc):
    global connected

    if rc == 0:
        connected = True
        print(f"[{timestamp()}] Connected to MQTT broker at {BROKER}:{PORT}")
        client.subscribe(COMMAND_TOPIC)
        print(f"[{timestamp()}] Listening for commands on {COMMAND_TOPIC}")
    else:
        connected = False
        print(f"[{timestamp()}] Connection failed with code {rc}")


def on_disconnect(client, userdata, rc):
    global connected

    connected = False
    print(f"[{timestamp()}] Disconnected from MQTT broker with code {rc}")

if __name__ == "__main__":
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()
    publish_loop()
