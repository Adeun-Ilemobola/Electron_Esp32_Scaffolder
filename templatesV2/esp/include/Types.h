#pragma once
#include <ArduinoJson.h>
#include <map>
enum class KindMode
{
    REGISTER,
    STATE,
    CMD,
    RESPONSE,
    LOG
};

inline const char *kindModeToString(KindMode kind)
{
    switch (kind)
    {
    case KindMode::REGISTER:
        return "register";
    case KindMode::STATE:
        return "state";
    case KindMode::CMD:
        return "cmd";
    case KindMode::RESPONSE:
        return "response";
    case KindMode::LOG:
        return "log";
    default:
        return "unknown";
    }
}

inline const void sendLog(const String &message)
{
    StaticJsonDocument<768> doc;
    doc["kind"] = "log";
    doc["id"] = "101";
    doc["moduleType"] = "101";
    JsonObject data = doc.createNestedObject("payload");
    data["message"] = "[Esp] " + message;
    serializeJson(doc, Serial);
    Serial.println();
}

template <typename T>
inline const void SendEvent(KindMode kind, std::map<String, T> state)
{
    // Note: Use a larger buffer if you expect many sensors
    StaticJsonDocument<1000> doc;
    doc["kind"] = kindModeToString(kind);

    // Create a nested object for the "data" or "payload"
    JsonObject data = doc.createNestedObject("payload");

    for (const auto &kv : state)
    {
        data[kv.first] = kv.second;
    }

    serializeJson(doc, Serial);
    Serial.println();
}


inline String IdGenerator(int zoneCount = 3, int charCount = 5)
{
    char chars[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*?";
    String id;
    for (int i = 0; i < zoneCount; i++)
    {
        for (int i = 0; i < charCount; i++)
        {
            id += chars[random(0, sizeof(chars) - 1)];
        }
        if (i < zoneCount - 1){
             id += "-";
        }

    }

    return id;
}