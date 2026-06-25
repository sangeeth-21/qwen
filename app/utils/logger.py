import logging
import sys


def setup_logging(level: str = "WARNING"):
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt))
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.WARNING))
    root.addHandler(handler)
