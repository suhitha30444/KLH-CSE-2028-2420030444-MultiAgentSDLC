# Traceability Report — run `e1c5480d`

**Final status:** done

**Retries spent:** spec_approval=0/3, test_review=1/5
*(1 Coder/Tester/Reviewer attempt(s) were rejected before this final one — see the criteria below for the ACCEPTED attempt only; earlier attempts' specific failures aren't retained by this report, only their count.)*

**Requirement:** Write a Playlist class with add_song(title, duration_seconds), remove_song(title), skip_to_next(), and total_duration(). add_song should raise a ValueError if a song with that title is already in the playlist. remove_song should raise a KeyError if the title isn’t in the playlist. skip_to_next() should return the title of the next song in the order songs were added, and wrap back around to the first song after reaching the last one. Calling skip_to_next() on an empty playlist should raise a RuntimeError. If the currently playing song is removed, the next call to skip_to_next() should still return the next remaining song without erroring. total_duration() should return the sum of all song durations, or 0 for an empty playlist.

Each section below follows ONE acceptance criterion end to end: the task(s) meant to satisfy it, the code that resulted, the real test executed against it, and the Reviewer's verdict.

## AC1: add_song adds a new song and total_duration reflects the added duration

**Task(s):**
- `T2` — Implement add_song method with duplicate title check, adding song, and updating total duration

**Code:**
*(no code artifact's task_id matched this criterion's task(s) exactly — showing every file the Coder produced this run, since the test result below confirms which one actually satisfies it)*

`playlist.py`:
```python
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
```

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — Test passed, confirming add_song adds a new song and updates total_duration.

## AC2: add_song raises ValueError when adding a song with a title that already exists

**Task(s):**
- `T2` — Implement add_song method with duplicate title check, adding song, and updating total duration

**Code:**
*(no code artifact's task_id matched this criterion's task(s) exactly — showing every file the Coder produced this run, since the test result below confirms which one actually satisfies it)*

`playlist.py`:
```python
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
```

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — Test passed, confirming add_song raises ValueError for duplicate title.

## AC3: remove_song removes an existing song and total_duration updates accordingly

**Task(s):**
- `T3` — Implement remove_song method with removal logic, updating total duration, raising KeyError, and handling removal of currently playing song

**Code:**
*(no code artifact's task_id matched this criterion's task(s) exactly — showing every file the Coder produced this run, since the test result below confirms which one actually satisfies it)*

`playlist.py`:
```python
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
```

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — Test passed, confirming remove_song removes a song and updates total_duration.

## AC4: remove_song raises KeyError when the title is not present

**Task(s):**
- `T3` — Implement remove_song method with removal logic, updating total duration, raising KeyError, and handling removal of currently playing song

**Code:**
*(no code artifact's task_id matched this criterion's task(s) exactly — showing every file the Coder produced this run, since the test result below confirms which one actually satisfies it)*

`playlist.py`:
```python
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
```

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — Test passed, confirming remove_song raises KeyError when title not present.

## AC5: skip_to_next returns the title of the next song in insertion order and wraps to the first after the last

**Task(s):**
- `T4` — Implement skip_to_next method that returns next song title, wraps around, raises RuntimeError on empty, and works correctly after current song removal

**Code:**
*(no code artifact's task_id matched this criterion's task(s) exactly — showing every file the Coder produced this run, since the test result below confirms which one actually satisfies it)*

`playlist.py`:
```python
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
```

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — Test passed, confirming skip_to_next returns next title in order and wraps correctly.

## AC6: skip_to_next raises RuntimeError when called on an empty playlist

**Task(s):**
- `T4` — Implement skip_to_next method that returns next song title, wraps around, raises RuntimeError on empty, and works correctly after current song removal

**Code:**
*(no code artifact's task_id matched this criterion's task(s) exactly — showing every file the Coder produced this run, since the test result below confirms which one actually satisfies it)*

`playlist.py`:
```python
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
```

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — Test passed, confirming skip_to_next raises RuntimeError on empty playlist.

## AC7: After the currently playing song is removed, the next call to skip_to_next returns the next remaining song without error

**Task(s):**
- `T3` — Implement remove_song method with removal logic, updating total duration, raising KeyError, and handling removal of currently playing song
- `T4` — Implement skip_to_next method that returns next song title, wraps around, raises RuntimeError on empty, and works correctly after current song removal

**Code:**
*(no code artifact's task_id matched this criterion's task(s) exactly — showing every file the Coder produced this run, since the test result below confirms which one actually satisfies it)*

`playlist.py`:
```python
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
```

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — Test passed, confirming skip_to_next works after current song removal.

## AC8: total_duration returns the sum of all song durations, or 0 for an empty playlist

**Task(s):**
- `T5` — Implement total_duration method returning sum of durations or 0 when playlist is empty

**Code:**
*(no code artifact's task_id matched this criterion's task(s) exactly — showing every file the Coder produced this run, since the test result below confirms which one actually satisfies it)*

`playlist.py`:
```python
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
```

**Test result:**
- **PASS** — PASS (real sandboxed execution, exit 0).

**Review verdict:**
- **APPROVED** — Test passed, confirming total_duration returns sum of durations or 0 for empty playlist.

