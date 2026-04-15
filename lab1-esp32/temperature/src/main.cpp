#include <Arduino.h>

const int sensorPin = 34;

void setup() {
  Serial.begin(115200);
  analogSetPinAttenuation(sensorPin, ADC_11db);
  analogReadResolution(12);                     
}

void loop() {
  int adcValue = analogRead(sensorPin);

  float voltage = adcValue * (3.3 / 4095.0);
  float temperatureC = (voltage - 0.5) * 100.0;

  Serial.print("ADC: ");
  Serial.print(adcValue);
  Serial.print(" | Voltage: ");
  Serial.print(voltage);
  Serial.print(" V | Temp: ");
  Serial.print(temperatureC);
  Serial.println(" °C");

  delay(1000);
}