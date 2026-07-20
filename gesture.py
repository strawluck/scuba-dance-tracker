from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto

import mediapipe as mp


WRIST = 0
PALM_CENTER = 9   # middle finger MCP, used as a stand-in for "center of hand"
MIDDLE_TIP = 12

# FaceMesh landmark indices (lips)
UPPER_LIP, LOWER_LIP = 13, 14
MOUTH_LEFT, MOUTH_RIGHT = 61, 291


class State(Enum):
    IDLE = auto()
    ARMED = auto()
    DANCING = auto()


@dataclass
class GestureConfig:
    grace_seconds: float = 0.15       # debounce before DANCING starts
    mouth_cover_dist: float = 0.09     # palm-to-mouth distance (normalized) to count as "covering"
    wave_window_seconds: float = 1.0   # how far back to look for oscillation
    wave_min_amplitude: float = 0.04   # min x-swing (normalized) to count as part of a wave
    wave_min_reversals: int = 2        # direction reversals required inside the window


class _WaveTracker:
    def __init__(self, maxlen: int = 60):
        self._positions: deque[tuple[float, float]] = deque(maxlen=maxlen)
        self.last_reversals = 0

    def push(self, t: float, x: float) -> None:
        self._positions.append((t, x))

    def reset(self) -> None:
        self._positions.clear()
        self.last_reversals = 0

    def is_waving(self, window: float, min_amplitude: float, min_reversals: int) -> bool:
        if not self._positions:
            self.last_reversals = 0
            return False

        now = self._positions[-1][0]
        pts = [(t, x) for t, x in self._positions if now - t <= window]
        if len(pts) < 4:
            self.last_reversals = 0
            return False

        reversals = 0
        direction = 0
        last_extreme = pts[0][1]
        for _, x in pts[1:]:
            delta = x - last_extreme
            if abs(delta) < min_amplitude:
                continue
            new_direction = 1 if delta > 0 else -1
            if direction != 0 and new_direction != direction:
                reversals += 1
            direction = new_direction
            last_extreme = x

        self.last_reversals = reversals
        return reversals >= min_reversals


class GestureWatcher:
    """Watches for: one hand covering the mouth while the other hand waves."""

    def __init__(self, config: GestureConfig | None = None):
        self.cfg = config or GestureConfig()
        self.hands = mp.solutions.hands.Hands(
            max_num_hands=2, min_detection_confidence=0.6, min_tracking_confidence=0.5
        )
        self.mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)
        self.state = State.IDLE
        self._armed_since: float | None = None
        self._wave_tracker = _WaveTracker()

    def _mouth_center(self, lm) -> tuple[float, float]:
        pts = [lm[UPPER_LIP], lm[LOWER_LIP], lm[MOUTH_LEFT], lm[MOUTH_RIGHT]]
        x = sum(p.x for p in pts) / len(pts)
        y = sum(p.y for p in pts) / len(pts)
        return x, y

    def update(self, rgb_frame) -> tuple[State, dict]:
        """Process one frame and return current state + debug info."""
        now = time.time()
        debug = {"hands": 0, "mouth_covered": False, "waving": False}

        hand_result = self.hands.process(rgb_frame)
        face_result = self.mesh.process(rgb_frame)

        if not hand_result.multi_hand_landmarks or not face_result.multi_face_landmarks:
            self._reset_state()
            self._wave_tracker.reset()
            return self.state, debug

        hands_lm = [h.landmark for h in hand_result.multi_hand_landmarks]
        debug["hands"] = len(hands_lm)
        mouth_x, mouth_y = self._mouth_center(face_result.multi_face_landmarks[0].landmark)

        covering_idx = None
        for i, lm in enumerate(hands_lm):
            palm = lm[PALM_CENTER]
            dist = ((palm.x - mouth_x) ** 2 + (palm.y - mouth_y) ** 2) ** 0.5
            if dist < self.cfg.mouth_cover_dist:
                covering_idx = i
                break
        debug["mouth_covered"] = covering_idx is not None

        if covering_idx is None:
            # no hand near the mouth right now, so there's no meaningful
            # "other hand" to track — drop any stale wave history
            self._wave_tracker.reset()
            waving = False
        else:
            if len(hands_lm) >= 2:
                wave_idx = next(i for i in range(len(hands_lm)) if i != covering_idx)
                wrist = hands_lm[wave_idx][WRIST]
                tip = hands_lm[wave_idx][MIDDLE_TIP]
                # track the fingertip's position *relative to the wrist* rather
                # than absolute wrist position — a wag pivoted at the wrist
                # barely moves the wrist itself, but swings the fingertip
                rel_x = tip.x - wrist.x
                self._wave_tracker.push(now, rel_x)
            waving = self._wave_tracker.is_waving(
                self.cfg.wave_window_seconds, self.cfg.wave_min_amplitude, self.cfg.wave_min_reversals
            )
        debug["waving"] = waving
        debug["wave_reversals"] = self._wave_tracker.last_reversals

        triggered = covering_idx is not None and waving

        if self.state is State.DANCING:
            if not triggered:
                self._reset_state()
        else:
            if triggered:
                if self.state is State.IDLE:
                    self.state = State.ARMED
                    self._armed_since = now
                elif self.state is State.ARMED and (now - self._armed_since) >= self.cfg.grace_seconds:
                    self.state = State.DANCING
            else:
                # only reset the state machine here — NOT the wave tracker.
                # waving needs several frames of history to detect a reversal,
                # and "triggered" is false throughout that build-up, so
                # clearing the buffer here would mean it can never accumulate
                # enough history to ever become true.
                self._reset_state()

        return self.state, debug

    def _reset_state(self) -> None:
        self.state = State.IDLE
        self._armed_since = None
