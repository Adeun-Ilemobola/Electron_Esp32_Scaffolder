#ifndef BTU_H
#define BTU_H

#pragma once
#include <Arduino.h>
#include "Types.h"
class Btu
{
public:
    Btu( int pin  , bool isPullUp = false);
    ~Btu();
    bool getState() const;
    void setState(bool newState) const;
    bool isPressed() const;
    void sendEvent(bool isPressed) const;
   String getId() const { return id; }
   void serializeSenderInfo(KindMode kind) const;


private:
    int pin;
    bool isPullUp;
    mutable bool state = false;
    String id ;

    void setup(int pin, bool isPullUp);

};

#endif