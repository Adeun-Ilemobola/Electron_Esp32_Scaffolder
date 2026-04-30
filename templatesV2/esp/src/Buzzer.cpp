#include "Buzzer.h"

Buzzer::Buzzer(int pin): pin(pin), id(IdGenerator()), state(false)
{
   
    
}
void Buzzer::setup(bool shouldRegister)
{
    pinMode(this->pin, OUTPUT);
    digitalWrite(this->pin, LOW); // Ensure it starts off

    if (shouldRegister)
    {
        this->serializeSenderInfo(KindMode::REGISTER);
    }
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
    serializeJson(doc, Serial);
    Serial.println();
}

void Buzzer::RESTART()
{
    Serial.println("Restarting Buzzer module...");
    state = false;
    setup();
}

Buzzer::~Buzzer()
{
    

}