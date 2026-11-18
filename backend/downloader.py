"""Download implementation is managed by the task worker in main.py.

Keeping this module intentionally free of persistent download directories ensures
that every job writes only to a unique temporary directory and is removed after
the browser receives the MP4 file.
"""
