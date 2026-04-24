#include <Arduino.h>
#include <ArduinoJson.h>
#include <map>
#include "Led.h"
#include "Btu.h"
#include "Types.h"
const int LED_PIN = 12; // The built-in LED on most ESP32 boards
bool isLedOn = false;
Btu *button = nullptr; // Assuming the button is connected to pin 0
Led *LED = nullptr;


template <typename T>
void SendEvent(KindMode kind, std::map<String, T> state)
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

void sendLog(const String &message)
{
  StaticJsonDocument<768> doc;
  doc["kind"] = "log";
  doc["id"] = "101";
  doc["moduleType"] ="101";
  JsonObject data = doc.createNestedObject("payload");
  data["message"] = message;
  serializeJson(doc, Serial);
  Serial.println();

}



void setup() {
  Serial.begin(115200);
  button = new Btu(18, true);
  LED  = new Led(LED_PIN);

}




void loop() {

   if (button->isPressed()) {
        Serial.println("Button is pressed!");
        bool currentState = LED->getState() ;
        LED->setState(!currentState);
        delay(200); // Debounce delay

      }

    if (Serial.available()) {
    String incoming = Serial.readStringUntil('\n');

    StaticJsonDocument<768> doc;
    DeserializationError error = deserializeJson(doc, incoming);

    if (!error) {
      const char* cmd = doc[kindModeToString(KindMode::COMMAND)];



      if (strcmp(cmd , "re-register") == 0){
        button->serializeSenderInfo(KindMode::REGISTER);

        sendLog("All item are register");
      }

      }else
    {
      sendLog("JSON parse failed: " + String(error.c_str()));
    }

    }
  }
}