# ============================================================
#  face_lock.py  —  Threaded DeepFace (no camera lag)
#
#  Install:
#    pip install deepface opencv-python pyserial numpy tf-keras
# ============================================================

import cv2
import serial
import time
import os
import threading
import numpy as np
from deepface import DeepFace

# -------- CONFIG --------
SERIAL_PORT       = "COM8"       # change to your port
BAUD_RATE         = 9600
KNOWN_FACES_DIR   = "known_faces"
FRAMES_TO_CONFIRM = 1         # consecutive matches needed
SCAN_TIMEOUT      = 15           # seconds before DENIED
VERIFY_EVERY_N    = 8            # run DeepFace every 8 frames (smooth camera)
# ------------------------

# ---- Shared state between main thread and verify thread ----
verify_result  = None   # True / False / None(pending)
verify_running = False
verify_lock    = threading.Lock()


def load_known_images(folder):
    images = []
    print(f"[INFO] Loading images from '{folder}'...")
    for f in os.listdir(folder):
        if f.lower().endswith((".jpg", ".jpeg", ".png")):
            path = os.path.join(folder, f)
            images.append(path)
            print(f"  [+] {f}")
    print(f"[INFO] {len(images)} image(s) loaded.\n")
    return images


def verify_thread_fn(frame_copy, known_images):
    """Runs in background thread — sets verify_result when done."""
    global verify_result, verify_running
    matched = False
    for img_path in known_images:
        try:
            result = DeepFace.verify(
                frame_copy,
                img_path,
                model_name="Facenet512",   # more accurate than Facenet
                enforce_detection=False,
                distance_metric="cosine"
            )
            if result.get("verified", False):
                matched = True
                break
        except Exception:
            continue

    with verify_lock:
        verify_result  = matched
        verify_running = False


def run():
    global verify_result, verify_running

    known_images = load_known_images(KNOWN_FACES_DIR)
    if not known_images:
        print("[ERROR] No images in known_faces/ folder. Add photos first.")
        return

    # Connect Arduino
    try:
        arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        print(f"[INFO] Arduino connected on {SERIAL_PORT}\n")
    except Exception as e:
        print(f"[ERROR] Serial: {e}")
        return

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    print("[INFO] Watching for authorised face...\n")

    while True:
        consecutive_matches = 0
        start_time    = time.time()
        decision_sent = False
        frame_count   = 0

        # Reset thread state for new scan cycle
        with verify_lock:
            verify_result  = None
            verify_running = False

        # ---- Main scanning loop ----
        while time.time() - start_time < SCAN_TIMEOUT:
            ret, frame = cap.read()
            if not ret:
                continue

            frame_count += 1

            # ✅ KEY FIX: only launch verify every N frames
            #    AND only if no verify is currently running
            with verify_lock:
                can_launch = (not verify_running) and \
                             (frame_count % VERIFY_EVERY_N == 0)

            if can_launch:
                # Send a small copy to the thread (don't share the live frame)
                small = cv2.resize(frame, (320, 240))
                with verify_lock:
                    verify_running = True
                    verify_result  = None
                t = threading.Thread(
                    target=verify_thread_fn,
                    args=(small.copy(), known_images),
                    daemon=True
                )
                t.start()

            # Read latest result (non-blocking)
            with verify_lock:
                latest = verify_result

            if latest is True:
                consecutive_matches += 1
                verify_result = None        # consume result
            elif latest is False:
                consecutive_matches = max(0, consecutive_matches - 1)
                verify_result = None

            # ---- Draw UI on camera window ----
            elapsed  = time.time() - start_time
            progress = int((consecutive_matches / FRAMES_TO_CONFIRM) * 200)
            progress = min(progress, 200)

            # Progress bar
            cv2.rectangle(frame, (20, 10), (220, 30), (50, 50, 50), -1)
            cv2.rectangle(frame, (20, 10), (20 + progress, 30), (0, 255, 100), -1)
            cv2.putText(frame,
                        f"Verifying {consecutive_matches}/{FRAMES_TO_CONFIRM}",
                        (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (255, 255, 255), 2)

            # Timeout countdown
            remaining = max(0, SCAN_TIMEOUT - elapsed)
            cv2.putText(frame, f"Time: {remaining:.1f}s",
                        (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (200, 200, 200), 1)

            # Processing indicator
            with verify_lock:
                running_now = verify_running
            if running_now:
                cv2.putText(frame, "Analysing...", (20, 130),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 1)

            cv2.imshow("Face Lock", frame)
            cv2.waitKey(1)

            # ✅ GRANTED
            if consecutive_matches >= FRAMES_TO_CONFIRM:
                print("[MATCH] Face verified! Sending F to Arduino.")
                arduino.write(b'F')
                decision_sent = True

                # Green overlay for 2 seconds
                for _ in range(40):
                    ret2, f2 = cap.read()
                    if ret2:
                        overlay = f2.copy()
                        cv2.rectangle(overlay, (0,0), (640,480), (0,180,0), -1)
                        cv2.addWeighted(overlay, 0.35, f2, 0.65, 0, f2)
                        cv2.putText(f2, "FACE VERIFIED", (90, 240),
                                    cv2.FONT_HERSHEY_DUPLEX, 1.6,
                                    (255, 255, 255), 3)
                        cv2.imshow("Face Lock", f2)
                    cv2.waitKey(50)
                break

        # ❌ DENIED
        if not decision_sent:
            print("[DENIED] Timeout. Sending D to Arduino.")
            arduino.write(b'D')

            for _ in range(30):
                ret2, f2 = cap.read()
                if ret2:
                    overlay = f2.copy()
                    cv2.rectangle(overlay, (0,0), (640,480), (0,0,180), -1)
                    cv2.addWeighted(overlay, 0.35, f2, 0.65, 0, f2)
                    cv2.putText(f2, "ACCESS DENIED", (80, 240),
                                cv2.FONT_HERSHEY_DUPLEX, 1.6,
                                (255, 255, 255), 3)
                    cv2.imshow("Face Lock", f2)
                cv2.waitKey(50)

        # Wait for Arduino to finish RFID+PIN cycle
        print("[INFO] Waiting 7 sec for Arduino cycle...\n")
        time.sleep(7)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n[INFO] Stopped.")
        cv2.destroyAllWindows()