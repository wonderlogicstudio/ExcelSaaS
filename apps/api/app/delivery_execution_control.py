"""Per-request cancellation propagates to the owned calculation child only."""

from __future__ import annotations

import threading
from contextlib import contextmanager
from contextvars import ContextVar

from .delivery_inputs import reject

CURRENT: ContextVar = ContextVar("delivery_execution", default=None)


class ExecutionControl:
    def __init__(self):
        self.cancelled = threading.Event()
        self.finished = threading.Event()
        self.lock = threading.Lock()
        self.process = None

    def check(self):
        if self.cancelled.is_set():
            reject(
                "EXECUTION_CANCELLED",
                "실행을 중지했습니다. 임시 파일 정리 후 취소가 완료됩니다.",
                409,
            )

    def cancel(self):
        self.cancelled.set()
        with self.lock:
            if self.process is not None and self.process.poll() is None:
                self.process.kill()

    def bind(self, process):
        with self.lock:
            self.process = process
            if self.cancelled.is_set() and process.poll() is None:
                process.kill()


@contextmanager
def execution_scope(control):
    token = CURRENT.set(control)
    try:
        yield
    finally:
        CURRENT.reset(token)


@contextmanager
def controlled_process(process):
    control = CURRENT.get()
    if control:
        control.bind(process)
    try:
        yield
    finally:
        if control:
            with control.lock:
                control.process = None


def check_cancelled():
    control = CURRENT.get()
    if control:
        control.check()
