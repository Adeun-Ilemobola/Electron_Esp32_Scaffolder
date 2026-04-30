#ifndef BUZZER_H
#define BUZZER_H

#pragma once
#include <Arduino.h>
#include "Types.h"


class Buzzer
{
public:
    Buzzer(int pin);
    void setup(bool shouldRegister = false);
    ~Buzzer();
    void on();
    void off();
    void pulse(int durationMs=200 , int maxCount = 5);
    void serializeSenderInfo(KindMode kind) const;
    String getId() const{ return id; }
    void RESTART();

private:
    int pin;
    bool state = false;
    String id;

};

#endif