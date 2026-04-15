#pragma once
#include "Sensors.h"

enum RoomState {
    IDLE,
    APPROACHING,
    OCCUPIED,
    STATIONARY,
    EXITING,
    GRACE_PERIOD
};

struct RoomContext {
    RoomState state;
    int peopleCount;
    float lastDistances[5];
    int distIndex;
    unsigned long graceStart;
    unsigned long lastEntryTime;
    unsigned long lastExitTime;
    unsigned long debounceMs;
};

void initRoom(RoomContext &ctx);
void stepRoom(RoomContext &ctx, SensorData &data);
const char* stateName(RoomState state);