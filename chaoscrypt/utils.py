"""Small shared helpers: seeding, JSON IO, timing."""
from __future__ import annotations

import json
import os
import random
import time
from contextlib import contextmanager
from pathlib import Path

import numpy as np


def set_seed(seed: int = 1234) -> None:
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    except Exception:
        pass


def ensure_dir(path: str | os.PathLike) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_json(obj, path: str | os.PathLike) -> None:
    ensure_dir(Path(path).parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, default=str)


def load_json(path: str | os.PathLike):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path: str | os.PathLike) -> dict:
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@contextmanager
def timer(label: str = "elapsed"):
    t0 = time.time()
    yield
    print(f"[{label}] {time.time() - t0:.2f}s")
