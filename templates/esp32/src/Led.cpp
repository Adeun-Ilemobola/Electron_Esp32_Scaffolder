#include "Led.h"
#include <Arduino.h>
#include <ArduinoJson.h>


Led::Led( int pin):pin(pin), state(false), id("led_" + String(pin))
{
    this->setup(pin);
    Serial.println("LED initialized on pin " + String(pin));

}

Led::~Led()
{

}

void Led::setup(int pin)
{
    this->pin = pin;
    this->state = false;
    pinMode(this->pin, OUTPUT);
    digitalWrite(this->pin, LOW); // Ensure it starts off
}

bool Led::getState() const
{
    return this->state;

}

void Led::on()
{
    this->state = true;
    digitalWrite(this->pin, HIGH);


}

void Led::off()
{
    this->state = false;
    digitalWrite(this->pin, LOW);

}

void Led::sendEvent(bool isOn) const
{
     StaticJsonDocument<400> doc;
    doc["event"] = this->id;
    doc["isOn"] = isOn;

    serializeJson(doc, Serial);
    Serial.println();
}

void Led::toggle()
{
    if (this->state) {
        this->off();
    } else {
        this->on();
    }
}

bool Led::setState(bool newState)
{
    if (newState) {
        this->on();
        this->sendEvent(this->state);
    } else {
        this->off();
        this->sendEvent(this->state);

    }
    return this->state;
}