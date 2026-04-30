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

void deleteAll()
{
  if (button != nullptr)
  {
    delete button;
    button = nullptr;
  }
  if (LED != nullptr)
  {
    delete LED;
    LED = nullptr;
  }
}

void setup()
{
  Serial.begin(115200);
  button = new Btu(18, true);
  LED = new Led(LED_PIN);
}

void loop()
{

  if (button->isPressed())
  {
    Serial.println("Button is pressed!");
    bool currentState = LED->getState();
    LED->setState(!currentState);
    delay(200); // Debounce delay
  }

  if (Serial.available())
  {
    String incoming = Serial.readStringUntil('\n');

    StaticJsonDocument<800> doc;
    DeserializationError error = deserializeJson(doc, incoming);

    if (!error)
    {
      const char *cmd = doc[kindModeToString(KindMode::CMD)] | "";
      sendLog("Received command: " + String(cmd));
      if (cmd[0] == '\0'){return;}
      const char *id = doc["id"] | " ";

      if (strcmp(cmd, "re-register") == 0)
      {
        deleteAll();
        setup();
        sendLog("All item are register");
      }
    }
    else
    {
      sendLog("JSON parse failed: " + String(error.c_str()));
    }
  }
}
