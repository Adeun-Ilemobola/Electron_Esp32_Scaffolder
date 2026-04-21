#include <Arduino.h>
#include <ArduinoJson.h>
#include <map>
#include "Led.h"
#include "Btu.h"
#include "Types.h"
const int LED_PIN = 12; // The built-in LED on most ESP32 boards
bool isLedOn = false;
std::map<String, Led*> leds; // Map to store LED objects by their pin number
Btu *button = nullptr; // Assuming the button is connected to pin 0



template <typename T>
void SendEvent(const char *event, std::map<String, T> state)
{
  // Note: Use a larger buffer if you expect many sensors
  StaticJsonDocument<400> doc;
  doc["event"] = event;

  // Create a nested object for the "data" or "state"
  JsonObject data = doc.createNestedObject("state");

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
  doc["event"] = "log";
  doc["message"] = message;
  serializeJson(doc, Serial);
  Serial.println();
}



void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW); // Ensure it starts off
  button = new Btu(18, true); // Initialize button on pin 18 with pull-up
  leds[String(13)] = new Led(13);
  leds[String(12)] = new Led(12);
  leds[String(14)] = new Led(14);
  leds[String(27)] = new Led(27);
}




void loop() {

   if (button->isPressed()) {
        Serial.println("Button is pressed!");
        bool currentState = leds[String(LED_PIN)]->getState() ;
        leds[String(LED_PIN)]->setState(!currentState);
        delay(200); // Debounce delay
        // Toggle LED state for next press
      }

        // Check if the MacBook sent a message

  if (Serial.available()) {
    String incoming = Serial.readStringUntil('\n');

    StaticJsonDocument<768> doc;
    DeserializationError error = deserializeJson(doc, incoming);

    if (!error) {
      const char* cmd = doc[kindModeToString(KindMode::COMMAND)];
      const char* targetId = doc["id"];
      /*
       {
        "cmd": "led_state",
        "id": "led_12",
        "state": true
       }

      */

      if (strcmp(cmd, "led_state") == 0) {
        for (const  auto& pair : leds) {
        if (pair.second->getId() == String(targetId)) {
          bool newState = doc["state"];
          pair.second->setState(newState);

        }
      }


      }else
    {
      sendLog("JSON parse failed: " + String(error.c_str()));
    }





    }
  }
}