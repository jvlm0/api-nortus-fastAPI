import re

def tem_letra(valor: str) -> bool:
    return bool(re.search(r"[A-Za-z]", valor))