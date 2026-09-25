"""Local sibling module (not pip-installable) that lives next to the endpoint.

Demonstrates SLS-360: a Flash endpoint can factor logic into local files and
have them ship to the worker.
"""


def shout(text: str) -> str:
    """Uppercase with emphasis."""
    return f"{text.upper()}!"
