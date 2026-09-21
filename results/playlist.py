class Playlist:
    def __init__(self):
        self._songs = []  # list of (title, duration)
        self._index = 0
    def add_song(self, title, duration_seconds):
        if any(t == title for t, _ in self._songs):
            raise ValueError(f"Song with title '{title}' already exists")
        self._songs.append((title, duration_seconds))
    def remove_song(self, title):
        for i, (t, d) in enumerate(self._songs):
            if t == title:
                del self._songs[i]
                if not self._songs:
                    self._index = 0
                elif i < self._index:
                    self._index -= 1
                elif i == self._index:
                    # current song removed, keep index pointing to next song
                    # if index now out of range, wrap to 0
                    if self._index >= len(self._songs):
                        self._index = 0
                return
        raise KeyError(f"Song with title '{title}' not found")
    def skip_to_next(self):
        if not self._songs:
            raise RuntimeError("Playlist is empty")
        if not self._songs:
            return None
        title, _ = self._songs[self._index]
        self._index = (self._index + 1) % len(self._songs)
        return title
    def total_duration(self):
        return sum(d for _, d in self._songs)