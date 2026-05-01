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

void Buzzer::onCommand(const char *targetId, const char *cmd, JsonDocument &doc)
{
    if (strcmp(targetId, id.c_str()) != 0)
    {
        return;
    }

    bool changed = false;

    if (strcmp(cmd, "on") == 0)
    {
        on();
        changed = true;
    }
    else if (strcmp(cmd, "off") == 0)
    {
        off();
        changed = true;
    }
    else if (strcmp(cmd, "setPulse") == 0)
    {
        int duration = doc["duration"] | 200; // Default to 200ms
        int count = doc["count"] | 5;         // Default to 5 pulses
        pulse(duration, count);
        changed = true;
    }

    if (changed)
    {
        serializeSenderInfo(KindMode::STATE);
    }
}

Buzzer::~Buzzer()
{
    

}