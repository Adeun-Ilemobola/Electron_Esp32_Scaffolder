#include "Led.h"
#include <Arduino.h>
#include <ArduinoJson.h>

Led::Led(int pin) : pin(pin), state(false), id(IdGenerator())
{

    this->setup(true);
    Serial.println("LED initialized on pin " + String(pin));
}

Led::~Led()
{
}

void Led::setup(bool shouldRegister)
{

    pinMode(this->pin, OUTPUT);
    digitalWrite(this->pin, LOW); // Ensure it starts off
    if (shouldRegister)
    {
        serializeSenderInfo(KindMode::REGISTER);
    }
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

void Led::RESTART()
{
    Serial.println("Restarting LED module...");
    state = false;
    setup(false);
}

void Led::toggle()
{
    if (this->state)
    {
        this->off();
    }
    else
    {
        this->on();
    }
}

bool Led::setState(bool newState)
{
    if (newState == this->state)
    {
        // No change needed
        return this->state;
    }
    if (newState)
    {
        this->on();
        this->sendEvent();
    }
    else
    {
        this->off();
        this->sendEvent();
    }
    return this->state;
}