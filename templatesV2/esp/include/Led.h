#ifndef LED_H
#define LED_H

#pragma once
#include <Arduino.h>
#include "Types.h"

class Led
{
public:
    Led(int pin);
    ~Led();
    void setup(bool shouldRegister = false);
    void toggle();
    bool getState() const;
    bool setState(bool newState);
    void on();
    void off();
    void sendEvent() const;
    String getId() const
    {
        return id;
    }
    void serializeSenderInfo(KindMode kind) const;
    void RESTART();
   
private:
    int pin;
    bool state;
    String id ;
};

#endif