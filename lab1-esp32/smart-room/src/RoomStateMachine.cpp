#include "RoomStateMachine.h"
#include <Arduino.h>

void initRoom(RoomContext &ctx) {
    ctx.state = IDLE;
    ctx.peopleCount = 0;
    ctx.distIndex = 0;
    for(int i = 0; i < 5; i++) ctx.lastDistances[i] = 200;
    ctx.graceStart = 0;

    ctx.lastEntryTime = 0;
    ctx.lastExitTime = 0;
    ctx.debounceMs = 1000; // 1 second debounce
}

bool isApproaching(RoomContext &ctx, float newDist) {
    int decreasing = 0;
    for(int i = 1; i < 5; i++) if(ctx.lastDistances[i] < ctx.lastDistances[i - 1]) decreasing++;
    return decreasing >= 3;
}

bool isLeaving(RoomContext &ctx, float newDist) {
    int increasing = 0;
    for(int i = 1; i < 5; i++) if(ctx.lastDistances[i] > ctx.lastDistances[i - 1]) increasing++;
    return increasing >= 3;
}

void controlLight(float lux) {
    if(lux < 500.0) {
        setLed(true);
    } else {
        setLed(false);
    }
}

void updateDistances(RoomContext &ctx, float newDist) {
    ctx.lastDistances[ctx.distIndex] = newDist;
    ctx.distIndex = (ctx.distIndex + 1) % 5;
}

// Centralized debounce function
bool canTrigger(unsigned long &lastTime, unsigned long now, unsigned long debounceMs) {
    if (now - lastTime > debounceMs) {
        lastTime = now;
        return true;
    }
    return false;
}

void stepRoom(RoomContext &ctx, SensorData &data) {
    unsigned long now = millis();
    updateDistances(ctx, data.distance);

    switch(ctx.state) {
        case IDLE:
            setLed(false);
            if(isApproaching(ctx, data.distance) && data.motionDetected) {
                ctx.state = APPROACHING;
            }
            break;

        case APPROACHING:
            if(isApproaching(ctx, data.distance) && data.motionDetected) {
                if(canTrigger(ctx.lastEntryTime, now, ctx.debounceMs)) {
                    ctx.peopleCount++;
                }
                ctx.state = OCCUPIED;
            } else if(!data.motionDetected) {
                ctx.state = IDLE;
            }
            break;

        case OCCUPIED:
            controlLight(data.lightLevel);

            if(!data.motionDetected) ctx.state = STATIONARY;

            if(isApproaching(ctx, data.distance) && data.motionDetected) {
                if(canTrigger(ctx.lastEntryTime, now, ctx.debounceMs)) {
                    ctx.peopleCount++;
                }
            }

            if(isLeaving(ctx, data.distance)) {
                if(canTrigger(ctx.lastExitTime, now, ctx.debounceMs)) {
                    ctx.peopleCount--;
                    if(ctx.peopleCount <= 0) {
                        ctx.peopleCount = 0;
                        ctx.state = GRACE_PERIOD;
                        ctx.graceStart = now;
                    }
                }
            }
            break;

        case STATIONARY:
            controlLight(data.lightLevel);
            if(data.motionDetected) ctx.state = OCCUPIED;
            break;

        case GRACE_PERIOD:
            if(isApproaching(ctx, data.distance) && data.motionDetected) {
                ctx.state = APPROACHING;
            }
            // Keep light in last state
            if((now - ctx.graceStart) > 5000) ctx.state = IDLE;
            break;
    }
}

const char* stateName(RoomState state) {
    switch(state) {
        case IDLE: return "IDLE";
        case APPROACHING: return "APPROACHING";
        case OCCUPIED: return "OCCUPIED";
        case STATIONARY: return "STATIONARY";
        case GRACE_PERIOD: return "GRACE_PERIOD";
        default: return "UNKNOWN";
    }
}