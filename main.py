from pathlib import Path

import cv2

from gesture import GestureWatcher, State
from player import VideoPlayer


VIDEO_PATH = Path(__file__).parent / "assets" / "fish dance.mov"


def draw_debug(frame, state: State, debug: dict) -> None:
    h, _ = frame.shape[:2]
    lines = [
        f"state: {state.name}",
        f"hands: {debug['hands']}  mouth_covered: {debug['mouth_covered']}  waving: {debug['waving']}",
        f"wave reversals: {debug.get('wave_reversals', 0)}",
    ]
    for i, line in enumerate(lines):
        cv2.putText(
            frame, line, (20, h - 20 - i * 28),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (60, 220, 255), 2, cv2.LINE_AA,
        )


def main() -> None:
    if not VIDEO_PATH.exists():
        print(f"Missing video: {VIDEO_PATH}")
        print("Drop your clip at assets/fish dance.mov and rerun.")
        return

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("Could not open webcam")
        return

    watcher = GestureWatcher()
    player = VideoPlayer(VIDEO_PATH)

    try:
        while True:
            ok, frame = cam.read()
            if not ok:
                continue
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            state, debug = watcher.update(rgb)
            draw_debug(frame, state, debug)

            if state is State.DANCING:
                player.play()
                player.tick()
            else:
                player.stop()

            cv2.imshow("KAMERA", frame)
            if cv2.waitKey(1) == 27:  # ESC
                break
    finally:
        player.stop()
        cam.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
