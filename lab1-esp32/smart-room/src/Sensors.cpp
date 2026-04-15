#include "Sensors.h"
#include <Arduino.h>
#include <math.h>

#define TRIG_PIN 18
#define ECHO_PIN 19
#define PIR_PIN 26
#define LED_PIN 5
#define LDR_PIN 35
#define TEMP_PIN 34

// LDR constants
const float GAMMA = 0.7;     
const float RL10 = 50.0;     
const float VCC = 3.3;       
const float R_FIXED = 10000; 

void initSensors() {
    pinMode(TRIG_PIN, OUTPUT);
    pinMode(ECHO_PIN, INPUT);
    pinMode(PIR_PIN, INPUT);
    pinMode(LED_PIN, OUTPUT);

    analogSetPinAttenuation(LDR_PIN, ADC_11db); 
    analogReadResolution(12);
}

SensorData readSensors() {
    SensorData data;

    // Distance sensor
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);
    long duration = pulseIn(ECHO_PIN, HIGH, 30000);
    data.distance = duration * 0.034 / 2.0;

    // PIR
    data.motionDetected = digitalRead(PIR_PIN) == HIGH;

    // LDR
    int ldrADC = analogRead(LDR_PIN);
    float ldrVoltage = ldrADC * (VCC / 4095.0);
    ldrVoltage = VCC - ldrVoltage; 
    float R_LDR = (ldrVoltage > 0.0 && ldrVoltage < VCC) ? R_FIXED * (VCC - ldrVoltage) / ldrVoltage : 100000.0;
    data.lightLevel = pow((RL10 * 1000.0 * pow(10.0, GAMMA)) / R_LDR, 1.0 / GAMMA);

    // Temperature
    int tempADC = analogRead(TEMP_PIN);
    float tempVoltage = tempADC * (VCC / 4095.0);
    data.temperature = (tempVoltage - 0.5) * 100.0;

    return data;
}

void setLed(bool on) {
    digitalWrite(LED_PIN, on ? HIGH : LOW);
}