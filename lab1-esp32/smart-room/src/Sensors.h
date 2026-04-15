#pragma once
#include <Arduino.h>

struct SensorData {
    float distance;
    bool motionDetected;
    int lightLevel;
    int temperature; // potentiometer simulating temp
};

void initSensors();
SensorData readSensors();
void setLed(bool on);