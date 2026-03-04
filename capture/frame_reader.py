"""
FrameReaderThread

Background thread that continuously reads frames from the capture device,
encodes them as JPEG, and stores the latest frame in CaptureManager.
Always serves the most recent frame — no queue.
"""

import threading
import time

from utils.logger import get_logger

logger = get_logger('FrameReader')


class FrameReaderThread(threading.Thread):
    """
    Reads frames from cv2.VideoCapture in a tight loop and writes the
    latest JPEG-encoded frame to CaptureManager._latest_frame under a lock.
    """

    def __init__(self, capture_manager):
        super().__init__(name="FrameReaderThread", daemon=True)
        self._cm = capture_manager
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        import cv2

        logger.info("FrameReaderThread started")
        consecutive_failures = 0

        while not self._stop_event.is_set():
            # Apply pending quality change before reading next frame
            if self._cm._quality_changed.is_set():
                self._cm._apply_quality()
                self._cm._quality_changed.clear()
                logger.info(f"Quality applied: {self._cm.quality}")

            ret, frame = self._cm._cap.read()

            if not ret:
                consecutive_failures += 1
                if consecutive_failures == 5:
                    logger.warning("Capture device returning no frames")
                time.sleep(0.1)
                continue

            consecutive_failures = 0

            # Encode to JPEG at current quality setting
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, self._cm._jpeg_quality]
            ok, buf = cv2.imencode('.jpg', frame, encode_params)
            if not ok:
                continue

            with self._cm._frame_lock:
                self._cm._latest_frame = buf.tobytes()
                self._cm._frame_count += 1

        logger.info("FrameReaderThread stopped")
