#include <Arduino.h>
#include <math.h>

const int LDR_PIN = 34;      // ADC pin connected to junction
const float GAMMA = 0.7;     // Wokwi photoresistor exponent
const float RL10 = 50.0;     // LDR resistance at 10 lux (kΩ)
const float VCC = 3.3;       // supply voltage
const float R_FIXED = 10000; // series resistor (10 kΩ)


bool checkZero(float voltage) {
    if (voltage <= 0.0 || voltage >= VCC) {
        Serial.println("Too dark or too bright to measure accurately");
        return true;
    } else {
        return false;
    }
}

void setup() {
    Serial.begin(115200);
    analogSetPinAttenuation(LDR_PIN, ADC_11db); // 0–3.3V range
    analogReadResolution(12);                   // 12-bit ADC
}

void loop() {
    int adcValue = analogRead(LDR_PIN);
    float voltage = adcValue * (VCC / 4095.0);

    voltage = VCC - voltage; // invert voltage, now increases with light

    if(checkZero(voltage)){
        delay(1000);
        return;
    }

    //compute resistance and derive lux
    float R_LDR = R_FIXED * (VCC - voltage) / voltage;
    float lux = pow((RL10 * 1000.0 * pow(10.0, GAMMA)) / R_LDR, (1.0 / GAMMA));

    // Output readings
    Serial.print("ADC: "); Serial.print(adcValue);
    Serial.print(" | Voltage: "); Serial.print(voltage, 3); Serial.print(" V");
    Serial.print(" | R_LDR: "); Serial.print(R_LDR, 0); Serial.print(" Ω");
    Serial.print(" | Lux: "); Serial.println(lux, 1);

    delay(1000);
}