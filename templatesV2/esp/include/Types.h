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
enum class RfidMode
{
    SCAN,
    WRITE
};
inline const char *rfidModeToString(RfidMode mode)
{
    switch (mode)
    {
    case RfidMode::SCAN:
        return "scan";
    case RfidMode::WRITE:
        return "write";
    default:
        return "unknown";
    }
}

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
    data["message"] = message;
    serializeJson(doc, Serial);
    Serial.println();
}

template <typename T>
inline const void SendEvent( std::map<String, T> state)
{
    // Note: Use a larger buffer if you expect many sensors
    StaticJsonDocument<2000> doc;
    doc["kind"] = kindModeToString(KindMode::RESPONSE);

    // Create a nested object for the "data" or "payload"
    JsonObject data = doc.createNestedObject("payload");

    for (const auto &kv : state)
    {
        data[kv.first] = kv.second;
    }

    serializeJson(doc, Serial);
    Serial.println();
}
