# Digital Twins Lab (Eclipse Ditto + Mosquitto)

This lab provides a self-contained environment to learn Eclipse Ditto by running a simple
mock IoT device that publishes telemetry over MQTT and observing how Ditto maps that
telemetry into Thing state.

Overview data-flow
- `mock_device/mock_device.py` → MQTT (Mosquitto)
- Ditto Connectivity (connection payload mapper) → Ditto Things (Thing state)
- Ditto UI / `control.desiredProperties.state` → Ditto outgoing mapper → MQTT (Mosquitto) → device command handler

High-level goals
- Demonstrate how to map device payloads into Ditto protocol messages (payload mapper).
- Show how to create administrative resources (Policy, Connection) via Ditto admin API.
- Set a desired control state in Ditto and observe the pump slow down and stop.

Prerequisites
- Docker and Docker Compose installed and working.
- `uv` installed for Python dependency management (see https://uv.link).
- Python 3.10+ recommended for the `.venv` created by `uv`.


## 1. Start the lab services

```bash
cd project
docker-compose up
```

Wait a few seconds for containers to initialize, then verify Ditto is healthy on 
http://localhost:8080

open the ditto explorer ui to inspect the state of the entities on ditto.

## 2. Prepare the Python environment (run once per shell/session)

```bash
# Create/update the project virtual environment and install dependencies
uv sync
source .venv/bin/activate
```

## 3. Create admin resources (Policy and Connection)

These use the Ditto admin REST API. Create them before creating the Thing.

```bash
uv run setup/01_create_policy.py
uv run setup/02_create_mqtt_connection.py
```

## 4. Create the command-ready Thing

Using the REST API we can add a new thing to Ditto. This version includes a dedicated `control` feature so we can change the desired pump state.

```bash
uv run setup/04_create_command_ready_thing.py
```

The model keeps the telemetry features (`motor` and `vibration`) and adds a `control` feature with `desiredProperties.state` for manual or automatic control.

## 5. Setup the updated connection

This updates the connection to handle updates to the desired state as messages to send back to the device.

```bash
uv run setup/05_create_bidirectional_mqtt_connection.py
```

## 6. Run the mock device (in a separate terminal)

```bash
uv run mock_device/mock_device.py
```

The device will start sending telemetry on MQTT, this gets captured by the Ditto connection, mapped and updated on the twin features. It also listens for commands on `devices/pump-001/commands`.

## 7. Inspect the device state on the Ditto UI

Check out the Ditto UI, explore the connection state, the timeline of the device updates etc.

## 8. Send a stop-pump command from Ditto

Open `org.example:pump-001`, select the `control` feature, and edit `desiredProperties.state`.

Set the state to `stopped` to stop the pump, or `running` to start it again.

If the UI offers a JSON editor, the payload should look like this:

```json
{
  "state": "stopped"
}
```

If you prefer the REST API, patch the feature directly at `/api/2/things/org.example:pump-001/features/control/desiredProperties/state`.


Ditto persists the desired-state change, the outgoing mapper turns it into an MQTT command, and the device stops the pump. The telemetry then cools down gradually instead of staying random.

## 8. How would we add an automatic trigger?

Think of where you could add the logic for an automatic trigger.

What would be the place to set this up?

How does ditto supports you? How would the current setup make it hard?


## 9. Inspect the system behavior

Watch the pump telemetry after the command is sent.

The expected sequence is:
- RPM falls to zero.
- Temperature decreases toward ambient.
- Vibration values drop close to zero.
- The `status` field changes from `running` to `stopped`.

Try to temporarily disconnect the device, then reconnect it.

Can you still change the device state while the device is offline?

What happens at reboot? Why?

Is this safe? Should we handle this differently?