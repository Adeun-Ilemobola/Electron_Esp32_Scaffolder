#include "Btu.h"
#include <Arduino.h>
#include <ArduinoJson.h>


Btu::Btu(int pin, bool isPullUp):pin(pin), isPullUp(isPullUp) , id(IdGenerator())
{
    
}

Btu::~Btu()
{


}

void Btu::setup(bool shouldRegister)
{
    if (this->isPullUp) {
        pinMode(this->pin, INPUT_PULLUP);
    } else {
        pinMode(this->pin, INPUT);
    }
    if (shouldRegister)
    {
        this->serializeSenderInfo(KindMode::REGISTER);
    }
}

bool Btu::getState() const
{
   return this->state;
}

void Btu::setState(bool newState) const
{
     if (this->isPullUp) {
         this->state = digitalRead(this->pin) == LOW;
         this->serializeSenderInfo(KindMode::STATE);

    } else {
         this->state = digitalRead(this->pin) == HIGH;
         this->serializeSenderInfo(KindMode::STATE);
    }
}

bool Btu::isPressed() const
{
    this->setState(!this->state);
    return this->getState();
}

void Btu::sendEvent(bool isPressed) const
{
     this->serializeSenderInfo(KindMode::STATE);
}

void Btu::serializeSenderInfo(KindMode kind) const
{
    StaticJsonDocument<400> doc;
    doc["kind"] = kindModeToString(kind);
    doc["id"] = this->id;
    doc["moduleType"] = "button";
    JsonObject payloadObj = doc.createNestedObject("payload");
    payloadObj["isPressed"] = this->state;

    serializeJson(doc, Serial);
    Serial.println();
}
