#include <Arduino.h>

const int pirPin = 27;  // PIR output (through voltage divider)
const int ledPin = 14;   // LED

void setup() {
  Serial.begin(115200);
  pinMode(pirPin, INPUT);
  pinMode(ledPin, OUTPUT);
}

void loop() {
  int motion = digitalRead(pirPin);

  if (motion == HIGH) {
    Serial.println("Motion detected!");
  } else {
    Serial.println("No motion");
  }

  digitalWrite(ledPin, motion);

  delay(200);
}