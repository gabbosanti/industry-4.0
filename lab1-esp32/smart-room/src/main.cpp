#include <Arduino.h>
#include "Sensors.h"
#include "RoomStateMachine.h"

RoomContext roomCtx;

void setup() {
    Serial.begin(115200);
    initSensors();
    initRoom(roomCtx);
}

void loop() {
    SensorData data = readSensors();
    stepRoom(roomCtx, data);

    Serial.print("State: "); Serial.print(stateName(roomCtx.state));
    Serial.print(" | People: "); Serial.print(roomCtx.peopleCount);
    Serial.print(" | Distance: "); Serial.print(data.distance);
    Serial.print(" | Motion: "); Serial.print(data.motionDetected ? "YES" : "NO");
    Serial.print(" | Light: "); Serial.print(data.lightLevel);
    Serial.print(" | Temperature: "); Serial.println(data.temperature);

    delay(200);
}