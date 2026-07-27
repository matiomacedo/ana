import inspect

import handlers
from registry import dispatch


def test_handlers_accept_context():
    for fn in (handlers.on_click, handlers.on_close):
        assert list(inspect.signature(fn).parameters) == ["event", "context"]


def test_dispatch_forwards_context():
    assert dispatch("click", "e", {"user": "ana"}) == "click:e by ana"
    assert dispatch("close", "x", {"user": "bo"}) == "close:x by bo"
