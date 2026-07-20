# Scuba Dance Tracker

A Python script that watches you through your webcam. Cover your mouth with one hand and wave your other hand back and forth — a video plays in its own window. Stop the gesture and the video closes.

---

## How it works (simple version)

About 30 times per second, the script:

1. **Grabs a frame** from your webcam.
2. **Looks for your face and hands** in that frame.
3. **Checks two things:**
   - Is one hand close to your mouth (covering it)?
   - Is your *other* hand waving back and forth?
4. If both are true for a moment, it **opens a video** and plays it. As soon as either hand stops doing its thing, the video closes.

The code is split into three files, each with one job:

| File | Job |
|---|---|
| `main.py` | Runs the webcam loop, glues everything together |
| `gesture.py` | Figures out if you're covering your mouth and waving |
| `player.py` | Opens/plays/closes the video in its own window |

---

## Technologies used (in plain English)

- **Python** — the language everything is written in.
- **OpenCV (`opencv-python`)** — a computer vision library. It reads frames from your webcam and draws the popup window that plays the video.
- **MediaPipe (`mediapipe`)** — Google's tracking library. Given a webcam frame, it hands back numbered points ("landmarks") for your face and hands — like where your lips are, and where each knuckle and fingertip is. The script only uses a handful of them:
  - A few lip points, to find the center of your mouth.
  - Your hand's wrist and middle fingertip, to tell if a hand is near your mouth, and to measure the waving motion of the other hand.

No machine learning training, no servers, no internet connection needed once installed — everything runs locally on your laptop.

---

## How the "wave" detection works

Waving isn't a single pose — it's *movement*. So instead of checking a single frame, the script watches the last second or so of hand movement and counts how many times it changes direction (left → right → left, etc.). If it flips direction enough times within that window, it counts as a wave.

---

## How to run it

### One-time setup

1. Make sure you have Python 3.9, 3.10, or 3.11 installed (MediaPipe doesn't support newer versions yet). Check with:
   ```
   python3 --version
   ```

2. Open Terminal and go to the project folder:
   ```
   cd "path/to/scuba-dance-tracker"
   ```

3. Create a virtual environment (an isolated sandbox just for this project):
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   ```
   You should see `(.venv)` appear at the start of your terminal prompt.

4. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

5. **Add your video.** Drop your clip into the `assets` folder and name it exactly `fish dance.mov`.

6. **Grant camera permission** to whatever app you're running this from (Terminal, iTerm, VS Code, etc.):
   - System Settings → Privacy & Security → Camera → toggle it on
   - Fully quit and reopen that app afterward

### Every time you want to run it

```
cd "path/to/scuba-dance-tracker"
source .venv/bin/activate
python3 main.py
```

A webcam window titled **KAMERA** pops up. Cover your mouth with one hand and wave the other — the video window should pop up while you keep doing it.

**To quit:** click the webcam window and press **ESC**.

---

## Tuning it if it's too sensitive (or not sensitive enough)

The webcam window shows live debug text at the bottom: whether a hand is covering your mouth, whether waving is detected, and how many direction-changes it's currently counted. Watch those numbers while you do the gesture, then open `gesture.py` and adjust these settings near the top of the file:

```python
mouth_cover_dist: float = 0.09     # how close a hand must be to your mouth to count as "covering"
wave_min_amplitude: float = 0.04    # how big each side-to-side swing must be
wave_min_reversals: int = 2         # how many direction changes are needed to count as waving
grace_seconds: float = 0.15         # how long the gesture must hold before the video starts
```

- If the mouth-cover isn't triggering, try raising `mouth_cover_dist` slightly.
- If waving isn't registering, try lowering `wave_min_amplitude` or `wave_min_reversals`.

---

## Project layout

```
scuba-dance-tracker/
├── main.py              # webcam loop + UI
├── gesture.py             # mouth-cover + wave detection
├── player.py               # video popup window
├── requirements.txt        # Python dependencies
└── assets/
    └── fish dance.mov     # the video that plays (you provide this)
```
