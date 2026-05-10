import time
from enum import Enum


class BreakerState(Enum):
    CLOSED    = "CLOSED"
    OPEN      = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class LLMBreaker:

    def TripOpen(self):
        self.State = BreakerState.OPEN
        self.LastFailAt = time.time()

    def DoReset(self):
        self.State     = BreakerState.CLOSED
        self.FailCount = 0
        self.PassCount = 0

    def __init__(self, maxFails: int = 3, cooldown: float = 10.0, testCalls: int = 1):
        self.maxFails  = maxFails
        self.cooldown  = cooldown
        self.testCalls = testCalls
        self.State     = BreakerState.CLOSED
        self.FailCount = 0
        self.PassCount = 0
        self.LastFailAt = None

    def CanProceed(self) -> bool:
        match self.State:
            case BreakerState.CLOSED:
                return True
            case BreakerState.OPEN:
                Elapsed = time.time() - self.LastFailAt
                if Elapsed >= self.cooldown:
                    self.State     = BreakerState.HALF_OPEN
                    self.PassCount = 0
                    return True
                return False
            case BreakerState.HALF_OPEN:
                return True
            case _:
                return False

    def LogSuccess(self):
        match self.State:
            case BreakerState.HALF_OPEN:
                self.PassCount += 1
                if self.PassCount >= self.testCalls:
                    self.DoReset()
            case BreakerState.CLOSED:
                self.FailCount = 0

    def LogFailure(self):
        self.FailCount  += 1
        self.LastFailAt  = time.time()
        match self.State:
            case BreakerState.HALF_OPEN:
                self.State = BreakerState.OPEN
            case _:
                if self.FailCount >= self.maxFails:
                    self.TripOpen()

    def FetchStatus(self) -> dict:
        TimeLeft = 0
        if self.LastFailAt and self.State == BreakerState.OPEN:
            TimeLeft = max(0, self.cooldown - (time.time() - self.LastFailAt))
        return {
            "state":     self.State.value,
            "failCount": self.FailCount,
            "maxFails":  self.maxFails,
            "retryIn":   round(TimeLeft, 1),
        }
