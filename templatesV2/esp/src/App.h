#pragma once

#include <Arduino.h>
#include <ArduinoJson.h>
#include "Led.h"
#include "Btu.h"
#include "Types.h"

class App
{
private:
    struct Pin
    {
        static constexpr int LED_PIN = 12;
        static constexpr int BUTTON_PIN = 18;
    };

    Btu button = Btu(Pin::BUTTON_PIN, true);
    Led led = Led(Pin::LED_PIN);

public:
    void setup()
    {
        Serial.begin(115200);

        led.setup(true);
        button.setup(true);
    }

    void loop()
    {
        if (button.isPressed())
        {
            Serial.println("Button is pressed!");

            bool currentState = led.getState();
            led.setState(!currentState);

            delay(200);
        }

        if (Serial.available())
        {
            String incoming = Serial.readStringUntil('\n');

            StaticJsonDocument<2000> doc;
            DeserializationError error = deserializeJson(doc, incoming);

            if (!error)
            {
                const char *cmd = doc[kindModeToString(KindMode::CMD)] | "";

                sendLog("Received command: " + String(cmd));

                if (cmd[0] == '\0')
                {
                    return;
                }

                if (strcmp(cmd, "re-register") == 0)
                {
                    setup();
                    sendLog("All items are registered");
                }
            }
            else
            {
                sendLog("JSON parse failed: " + String(error.c_str()));
            }
        }
    }
};