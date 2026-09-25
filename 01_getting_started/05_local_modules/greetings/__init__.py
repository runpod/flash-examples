"""Local package whose __init__ re-exports from a submodule.

Exercises transitive local-import resolution: the endpoint imports ``greetings``,
whose ``__init__`` imports ``greetings.messages`` — the resolver must pull in both
``greetings/__init__.py`` and ``greetings/messages.py``.
"""

from .messages import render

__all__ = ["render"]
