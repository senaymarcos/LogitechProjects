from queue import Queue
from pynput import mouse, keyboard


class EventsListener:
    def __init__(self):
        self._events_queue = Queue()

        # ...or, in a non-blocking fashion:
        self._event_listener = mouse.Listener(on_move=self._on_move,
                                              on_click=self._on_click,
                                              on_scroll=self._on_scroll)

        self._kbd_event_listener = keyboard.Listener(on_press=self._on_press)
        self._event_listener.start()   # thread
        self._kbd_event_listener.start()

    @property
    def events_queue(self) -> Queue:
        return self._events_queue

    def stop(self):
        self._event_listener.stop()

    def _on_move(self, x, y):
        pass

    def _on_click(self, x, y, button, pressed):
        pressed = 'pressed' if pressed else 'released'
        event = f'{button.name}_{pressed}'
        print(event)
        self._events_queue.put(event)

    def _on_scroll(self, x, y, dx, dy):
        event = f'wheel_{"down" if dy < 0 else "up"}'
        self._events_queue.put(event)
        print(event)

    def _on_press(self, key):
        pass
