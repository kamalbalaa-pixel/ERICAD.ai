import time
import threading
import collections
import mss
import cv2
import numpy as np
import config

class FlightRecorder:
    def __init__(self):
        self.running = False
        self.thread = None
        
        # Short Term: Full FPS
        self.short_maxlen = config.SHORT_MEMORY_SEC * config.FPS
        self.short_buffer = collections.deque(maxlen=self.short_maxlen)
        
        # Long Term: Time Lapse
        self.long_interval = config.FPS * 2 
        long_total_frames = (config.LONG_MEMORY_MIN * 60) // 2
        self.long_buffer = collections.deque(maxlen=long_total_frames)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._record_loop)
        self.thread.start()
        print("Flight Recorder Started...")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def clear_memory(self):
        self.short_buffer.clear()
        self.long_buffer.clear()
        print("Memory Wiped.")

    def _record_loop(self):
        frame_count = 0
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            while self.running:
                start_time = time.time()
                img = np.array(sct.grab(monitor))
                frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                frame = cv2.resize(frame, (1280, 720))
                
                self.short_buffer.append(frame)
                if frame_count % self.long_interval == 0:
                    self.long_buffer.append(frame)
                
                frame_count += 1
                elapsed = time.time() - start_time
                time.sleep(max(0, (1.0/config.FPS) - elapsed))

    # --- NEW: SAVE SNAPSHOT ---
    def save_snapshot(self, filepath):
        """Saves the single most recent frame as an image."""
        if not self.short_buffer:
            return False
        # Get last frame
        frame = self.short_buffer[-1]
        cv2.imwrite(filepath, frame)
        return True

    # --- UPDATED: VARIABLE DURATION ---
    def save_video(self, duration_sec, filepath=config.TEMP_VIDEO_PATH):
        """Saves video of specific length from buffers."""
        
        # Decide which buffer to use
        if duration_sec <= config.SHORT_MEMORY_SEC:
            # Short Buffer (High FPS)
            fps = config.FPS
            frames_needed = duration_sec * fps
            full_source = list(self.short_buffer)
            source = full_source[-frames_needed:]
        else:
            # Long Buffer (Time Lapse)
            fps = 2 
            frames_needed = int(duration_sec / 2) 
            full_source = list(self.long_buffer)
            source = full_source[-frames_needed:]

        if not source: return False

        h, w, _ = source[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(filepath, fourcc, fps, (w, h))

        for frame in source:
            out.write(frame)
        out.release()
        return True