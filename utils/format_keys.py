import re


def format_private_key(text: str) -> str | None:
    parts = re.split(r'[,;:\s]\s*', text)
    private_key_pattern = re.compile(r'^(0x[a-fA-F0-9]{64}|[a-fA-F0-9]{64})$')

    for part in parts:
        if private_key_pattern.match(part):
            return part if part.startswith('0x') else f'0x{part}'

    return None
