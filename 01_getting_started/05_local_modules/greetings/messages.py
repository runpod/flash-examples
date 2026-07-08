"""Package submodule with greeting templates."""

TEMPLATES = {
    "en": "Hello, {name}",
    "es": "Hola, {name}",
    "fr": "Bonjour, {name}",
}


def render(name: str, lang: str = "en") -> str:
    template = TEMPLATES.get(lang, TEMPLATES["en"])
    return template.format(name=name)
