"""Lightweight keyboard logger for SentiGuard.

Records completed lines to `keystrokes.txt` so sentiment analysis can read
typed text while avoiding per-keystroke disk writes.
"""

from __future__ import annotations

import threading
from typing import List


try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except Exception:
    PYNPUT_AVAILABLE = False
    keyboard = None  # type: ignore[assignment]


class _DummyListener:
    def start(self):
        return self

    def stop(self):
        return None


class _LineBufferLogger:
    def __init__(self):
        self._buffer: List[str] = []
        self._lock = threading.Lock()

    def _flush(self):
        text = "".join(self._buffer).strip()
        self._buffer.clear()
        if not text:
            return

        with open("keystrokes.txt", "a", encoding="utf-8") as file_handle:
            file_handle.write(text + "\n")

    def on_press(self, key):
        try:
            if key == keyboard.Key.enter:
                with self._lock:
                    self._flush()
                return

            if key == keyboard.Key.backspace:
                with self._lock:
                    if self._buffer:
                        self._buffer.pop()
                return

            if key == keyboard.Key.space:
                with self._lock:
                    self._buffer.append(" ")
                return

            char = getattr(key, "char", None)
            if char:
                with self._lock:
                    self._buffer.append(char)
        except Exception:
            pass

    def on_release(self, key):
        return None


def start_keylogger():
    """Start capturing typed lines and return a listener with a stop method."""
    if not PYNPUT_AVAILABLE:
        return _DummyListener()

    logger = _LineBufferLogger()
    listener = keyboard.Listener(on_press=logger.on_press, on_release=logger.on_release)
    listener.start()
    return listener