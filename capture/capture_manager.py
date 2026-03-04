"""
CaptureManager

Manages the USB capture device lifecycle and exposes the latest JPEG frame
to HTTP streaming consumers.

Threading model:
  - FrameReaderThread (background): reads frames, encodes JPEG, stores in _latest_frame
  - HTTP async generators: call get_latest_frame() at up to 30fps
  - Quality changes: set via set_quality(); FrameReaderThread applies on next iteration
"""

import threading
import time

from utils.logger import get_logger

logger = get_logger('CaptureManager')

QUALITY_PRESETS = {
    'low':    {'width': 640,  'height': 360,  'jpeg_quality': 40},
    'medium': {'width': 1280, 'height': 720,  'jpeg_quality': 65},
    'high':   {'width': 1920, 'height': 1080, 'jpeg_quality': 85},
}


class CaptureManager:
    """
    Owns the cv2.VideoCapture instance and FrameReaderThread.

    Call start() once during app startup; the thread runs until stop() is called.
    Consumers call get_latest_frame() to get the most recent JPEG bytes (or None
    if no frame has been captured yet).
    """

    def __init__(self, device_index: int = 0, quality: str = 'medium'):
        self._device_index = device_index
        self._quality = quality
        self._jpeg_quality = QUALITY_PRESETS[quality]['jpeg_quality']

        self._cap = None
        self._latest_frame: bytes | None = None
        self._frame_lock = threading.Lock()
        self._quality_changed = threading.Event()

        self._reader_thread = None
        self._start_time = time.time()

        # FPS tracking
        self._frame_count = 0
        self._fps_window_start = time.time()
        self._fps_actual = 0.0

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> bool:
        """Open capture device and start frame reader thread."""
        import cv2
        from capture.frame_reader import FrameReaderThread

        self._cap = cv2.VideoCapture(self._device_index, cv2.CAP_V4L2)
        if not self._cap.isOpened():
            logger.warning(
                f"Capture device {self._device_index} could not be opened. "
                "Stream will show unavailable until device is connected."
            )
            return False

        self._apply_quality()
        self._reader_thread = FrameReaderThread(self)
        self._reader_thread.start()
        logger.info(f"Capture device {self._device_index} opened successfully at {self.resolution}")
        return True

    def stop(self):
        """Stop frame reader thread and release capture device."""
        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.stop()
            self._reader_thread.join(timeout=3.0)
            logger.info("FrameReaderThread joined")

        if self._cap:
            self._cap.release()
            self._cap = None
            logger.info("Capture device released")

    # ── Frame access ──────────────────────────────────────────────────────────

    def get_latest_frame(self) -> bytes | None:
        """Return the latest JPEG-encoded frame, or None if not yet available."""
        with self._frame_lock:
            return self._latest_frame

    # ── Quality control ───────────────────────────────────────────────────────

    def set_quality(self, quality: str):
        """
        Request a quality change. FrameReaderThread applies it before the next frame.

        Args:
            quality: One of 'low', 'medium', 'high'

        Raises:
            ValueError: If quality is not a known preset
        """
        if quality not in QUALITY_PRESETS:
            raise ValueError(f"Unknown quality preset '{quality}'. Must be one of: {list(QUALITY_PRESETS)}")
        self._quality = quality
        self._jpeg_quality = QUALITY_PRESETS[quality]['jpeg_quality']
        self._quality_changed.set()

    def _apply_quality(self):
        """Apply current quality preset to the capture device (call from reader thread)."""
        import cv2
        preset = QUALITY_PRESETS[self._quality]
        if self._cap and self._cap.isOpened():
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, preset['width'])
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, preset['height'])

    # ── Metrics ───────────────────────────────────────────────────────────────

    def get_fps_actual(self) -> float:
        """Compute and return the current capture framerate."""
        now = time.time()
        elapsed = now - self._fps_window_start
        if elapsed >= 1.0:
            self._fps_actual = self._frame_count / elapsed
            self._frame_count = 0
            self._fps_window_start = now
        return round(self._fps_actual, 1)

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def device_index(self) -> int:
        return self._device_index

    @property
    def quality(self) -> str:
        return self._quality

    @property
    def device_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    @property
    def uptime(self) -> float:
        return time.time() - self._start_time

    @property
    def resolution(self) -> str:
        p = QUALITY_PRESETS[self._quality]
        return f"{p['width']}x{p['height']}"

    @property
    def jpeg_quality(self) -> int:
        return self._jpeg_quality
