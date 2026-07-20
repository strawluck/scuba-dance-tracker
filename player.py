from __future__ import annotations

import time
from pathlib import Path

import cv2


class VideoPlayer:
    """Plays a local video clip in its own popup cv2 window, advancing by real
    elapsed time (not by webcam frame count) so playback speed stays correct
    regardless of webcam FPS."""

    def __init__(self, video_path: Path, window_name: str = "FISH DANCE", play_speed: float = 1.0):
        self.video_path = video_path
        self.window_name = window_name
        self.play_speed = play_speed

        self.cap = cv2.VideoCapture(str(video_path))
        if not self.cap.isOpened():
            raise FileNotFoundError(f"Could not open video: {video_path}")

        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        self._playing = False
        self._start_time: float | None = None
        self._last_frame_idx = -1

    @property
    def is_playing(self) -> bool:
        return self._playing

    def play(self) -> None:
        if self._playing:
            return
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self._start_time = time.time()
        self._last_frame_idx = -1
        self._playing = True
        cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)

    def stop(self) -> None:
        if not self._playing:
            return
        self._playing = False
        cv2.destroyWindow(self.window_name)

    def tick(self) -> None:
        """Call once per main-loop iteration while playing to advance/draw the frame."""
        if not self._playing:
            return

        elapsed = (time.time() - self._start_time) * self.play_speed
        frame_idx = int(elapsed * self.fps)

        if frame_idx >= self.frame_count:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self._start_time = time.time()
            frame_idx = 0

        if frame_idx != self._last_frame_idx:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ok, frame = self.cap.read()
            if ok:
                cv2.imshow(self.window_name, frame)
                self._last_frame_idx = frame_idx
