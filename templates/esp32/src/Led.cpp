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

    this->serializeSenderInfo(KindMode::REGISTER);
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

void Led::sendEvent() const
{
    this->serializeSenderInfo(KindMode::STATE);
}

void Led::serializeSenderInfo(KindMode kind) const
{
    StaticJsonDocument<500> doc;
    doc["kind"] = kindModeToString(kind);
    doc["id"] = this->id;
    doc["moduleType"] = "led";
    JsonObject payloadObj = doc.createNestedObject("payload");
    payloadObj["state"] = this->state;
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
        this->sendEvent();
    } else {
        this->off();
        this->sendEvent();

    }
    return this->state;
}