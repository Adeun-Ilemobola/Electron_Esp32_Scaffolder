#ifndef LED_H
#define LED_H

#pragma once
#include <Arduino.h>

class Led
{
public:
    Led(int pin);
    ~Led();
    void setup(int pin);
    void toggle();
    bool getState() const;
    bool setState(bool newState);
    void on();
    void off();
    void sendEvent(bool isOn) const;
    String getId() const
    {
        return id;
    }

private:
    int pin;
    bool state;
    String id ;
};

#endif