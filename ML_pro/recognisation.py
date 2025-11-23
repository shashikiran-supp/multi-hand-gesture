import cv2
import mediapipe as mp
import pyautogui
import time
import math
import subprocess
import sys
import os

from gestures_utils import (
    EMA2D, map_to_screen, is_fist,
    is_pinch_thumb_index, is_pinch_thumb_middle
)

# Disable PyAutoGUI fail-safe
pyautogui.FAILSAFE = False

# Screen size
screen_w, screen_h = pyautogui.size()

# MediaPipe Hands setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

# Gesture modes
modes = ["POINTER", "SCROLL", "VOLUME", "ZOOM", "AIR_DRAW"]
mode_index = 0
mode = modes[mode_index]
last_mode_switch = 0
mode_cooldown = 1.3  # seconds

# States and smoothers
smoother = EMA2D(alpha=0.25)
dragging = False
pinch_start = None
click_cooldown = 0.35
last_click_time = 0
prev_scroll_y = None
initial_volume_y = None
initial_zoom_y = None

# Mode colors for HUD
mode_colors = {
    "POINTER": (255, 255, 255),
    "SCROLL": (0, 255, 255),
    "VOLUME": (0, 200, 255),
    "ZOOM": (0, 165, 255),
    "AIR_DRAW": (180, 255, 180),
}

# Camera capture
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow backend on Windows
air_proc = None

print("🤚 Gesture Controller running... Press ESC to exit.")

# ===================== MAIN LOOP =====================
while True:
    ret, img = cap.read()
    if not ret:
        break

    img = cv2.flip(img, 1)
    frame_h, frame_w, _ = img.shape

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)
    gesture_feedback = ""

    # Detect hands
    if result.multi_hand_landmarks and result.multi_handedness:
        for hand_lms, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
            lm = hand_lms.landmark
            hand_label = handedness.classification[0].label
            mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)

            # ================= LEFT HAND =================
            if hand_label == "Left":
                # Fist -> change mode
                if is_fist(lm):
                    now = time.time()
                    if now - last_mode_switch > mode_cooldown:
                        # If Air Draw is running, close it before switching
                        if mode == "AIR_DRAW" and air_proc and air_proc.poll() is None:
                            air_proc.terminate()

                        # Switch mode
                        mode_index = (mode_index + 1) % len(modes)
                        mode = modes[mode_index]
                        last_mode_switch = now

                        # Reset state
                        prev_scroll_y = None
                        initial_volume_y = None
                        initial_zoom_y = None
                        pinch_start = None

                        # Launch Air Draw
                        if mode == "AIR_DRAW":
                            try:
                                # Release camera before launching Air Draw
                                cap.release()
                                script_path = os.path.join(os.path.dirname(__file__), "air_canvas.py")
                                print("🎨 Launching Air Draw...")
                                air_proc = subprocess.Popen([sys.executable, script_path])
                                gesture_feedback = "Air Draw Launched!"
                            except Exception as e:
                                gesture_feedback = f"Air Draw Failed: {e}"

                # ========== SCROLL MODE ==========
                if mode == "SCROLL":
                    ix, iy = int(lm[8].x * frame_w), int(lm[8].y * frame_h)
                    mx, my = int(lm[12].x * frame_w), int(lm[12].y * frame_h)
                    d = math.hypot(ix - mx, iy - my)
                    if d < 40:
                        cur = (iy + my) // 2
                        if prev_scroll_y is not None:
                            dy = cur - prev_scroll_y
                            if dy > 4:
                                pyautogui.scroll(-60)
                                gesture_feedback = "Scroll Down"
                            elif dy < -4:
                                pyautogui.scroll(60)
                                gesture_feedback = "Scroll Up"
                        prev_scroll_y = cur
                    else:
                        prev_scroll_y = None

                # ========== VOLUME MODE ==========
                elif mode == "VOLUME":
                    cy = int(lm[12].y * frame_h)
                    if initial_volume_y is None:
                        initial_volume_y = cy
                    else:
                        diff = initial_volume_y - cy
                        steps = int(diff / 6)
                        if steps > 0:
                            for _ in range(min(steps, 3)):
                                pyautogui.press("volumeup")
                            gesture_feedback = "Volume Up"
                        elif steps < 0:
                            for _ in range(min(-steps, 3)):
                                pyautogui.press("volumedown")
                            gesture_feedback = "Volume Down"
                        initial_volume_y = cy

                # ========== ZOOM MODE ==========
                elif mode == "ZOOM":
                    cy = int(lm[12].y * frame_h)
                    if initial_zoom_y is None:
                        initial_zoom_y = cy
                    else:
                        diff = initial_zoom_y - cy
                        if diff != 0:
                            pyautogui.keyDown("ctrl")
                            pyautogui.scroll(int(diff * 2))
                            pyautogui.keyUp("ctrl")
                            gesture_feedback = "Zooming"
                            initial_zoom_y = cy

            # ================= RIGHT HAND =================
            elif hand_label == "Right":
                if mode == "POINTER":
                    nx, ny = lm[12].x, lm[12].y
                    sx, sy = map_to_screen(nx, ny, frame_w, frame_h, screen_w, screen_h)
                    sx, sy = smoother.update(sx, sy)
                    pyautogui.moveTo(sx, sy, duration=0)

                    pinch_index = is_pinch_thumb_index(lm, thresh=0.045)
                    pinch_middle = is_pinch_thumb_middle(lm, thresh=0.045)
                    now = time.time()

                    # Left click / drag
                    if pinch_index:
                        if pinch_start is None:
                            pinch_start = now
                        elif (now - pinch_start) > 0.45 and not dragging:
                            pyautogui.mouseDown()
                            dragging = True
                            gesture_feedback = "Dragging..."
                    else:
                        if dragging:
                            pyautogui.mouseUp()
                            dragging = False
                            gesture_feedback = "Dropped"
                        elif pinch_start and (now - pinch_start) <= 0.45:
                            if now - last_click_time > click_cooldown:
                                pyautogui.click()
                                last_click_time = now
                                gesture_feedback = "Left Click"
                        pinch_start = None

                    # Right click
                    if pinch_middle and (now - last_click_time > click_cooldown):
                        pyautogui.click(button="right")
                        last_click_time = now
                        gesture_feedback = "Right Click"

    # If Air Draw closed manually, revert to POINTER mode and reopen camera
    if mode == "AIR_DRAW":
        if air_proc and air_proc.poll() is not None:
            mode_index = 0
            mode = modes[mode_index]
            air_proc = None
            print("🖱 Exited Air Draw — back to POINTER mode.")
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # reopen camera

    # HUD overlay
    color = mode_colors.get(mode, (255, 255, 255))
    cv2.rectangle(img, (10, 10), (450, 120), (0, 0, 0), -1)
    cv2.putText(img, f"Mode: {mode}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.1, color, 3)
    if gesture_feedback:
        cv2.putText(img, gesture_feedback, (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (180, 255, 180), 2)

    # Show video
    cv2.imshow("Gesture Controller", img)

    # ESC key to exit
    if cv2.waitKey(1) & 0xFF == 27:
        if air_proc and air_proc.poll() is None:
            try:
                air_proc.terminate()
            except Exception:
                pass
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
print("👋 Gesture Controller Closed.")
