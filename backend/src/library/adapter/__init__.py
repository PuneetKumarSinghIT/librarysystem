"""Adapters: concrete implementations of core ports (DB repositories, security, ...).

This is the only outer layer that touches frameworks/drivers. It depends on `core`
(to implement its ports) but nothing depends on it except the composition root (main.py).
"""
