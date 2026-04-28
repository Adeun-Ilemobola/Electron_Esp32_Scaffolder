#include "Buzzer.h"

Buzzer::Buzzer(int pin): pin(pin), id("buzzer_" + String(pin))
{
    this->setup(pin);
    
}
void Buzzer::setup(int pin)
{
    this->pin = pin;
    this->state = false;
    pinMode(this->pin, OUTPUT);
    digitalWrite(this->pin, LOW); // Ensure it starts off

    this->serializeSenderInfo(KindMode::REGISTER);
}
void Buzzer::on()
{
    this->state = true;
    digitalWrite(this->pin, HIGH);
}
void Buzzer::off()
{
    this->state = false;
    digitalWrite(this->pin, LOW);
}
void Buzzer::pulse(int durationMs, int maxCount)
{
    for (int i = 0; i < maxCount; i++)
    {
        this->on();
        delay(durationMs);
        this->off();
        delay(durationMs);
    }
}

void Buzzer::serializeSenderInfo(KindMode kind) const
{
    StaticJsonDocument<500> doc;
    doc["kind"] = kindModeToString(kind);
    doc["id"] = this->id;
    doc["moduleType"] = "buzzer";
    JsonObject payloadObj = doc.createNestedObject("payload");
    payloadObj["state"] = this->state;
}


Buzzer::~Buzzer()
{
    

}