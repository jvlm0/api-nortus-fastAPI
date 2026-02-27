from typing import List
from app.schemas.ordem import ProblemaOrdem


def split_obs(obs): 

    titulo = obs.split(" - ")[0] if obs else None
    descricao = obs.split(" - ")[1] if obs and " - " in obs else None

    return titulo, descricao



def recuperar_problemas(texto_problema: str, texto_solucao: str) -> List[ProblemaOrdem]:
    """
    Recupera a lista de problemas a partir dos textos formatados.
    
    Args:
        texto_problema: Texto com os problemas formatados
        texto_solucao: Texto com as soluções formatadas
    
    Returns:
        Lista de dicts com 'descricao' e 'solucao'
    """

    if (not texto_problema or not texto_problema.strip()) and (not texto_solucao or not texto_solucao.strip()):
        return None

    problemas: List[ProblemaOrdem] = []

    # Caso texto simples (sem numeração "Problema X:")
    if not texto_problema.startswith("Problema 1:"):
        if texto_problema.strip():
            problemas.append(ProblemaOrdem(
                descricao=texto_problema.strip(),
                solucao=texto_solucao.strip() if texto_solucao else ""
            ))
        return problemas

    # Parsear soluções numeradas em um dict
    solucoes = {}
    for linha in texto_solucao.splitlines():
        linha = linha.strip()
        if linha.startswith("Solução "):
            partes = linha.split(":", 1)
            if len(partes) == 2:
                numero = partes[0].replace("Solução ", "").strip()
                if numero.isdigit():
                    solucoes[int(numero)] = partes[1].strip()

    # Parsear problemas numerados
    for linha in texto_problema.splitlines():
        linha = linha.strip()
        if linha.startswith("Problema "):
            partes = linha.split(":", 1)
            if len(partes) == 2:
                numero = partes[0].replace("Problema ", "").strip()
                if numero.isdigit():
                    idx = int(numero)
                    problemas.append(ProblemaOrdem(
                        descricao=partes[1].strip(),
                        solucao=solucoes.get(idx, "")
                    ))

    return problemas

def formatar_problemas(problemas: list) -> tuple:
    """
    Formata a lista de problemas em textos para armazenamento.
    
    Args:
        problemas: Lista de dicts com 'descricao' e 'solucao'
    
    Returns:
        Tuple com (texto_problema, texto_solucao)
    """
    texto_problema = ""
    texto_solucao = ""

    if (len(problemas) == 1):
        return problemas[0].descricao, problemas[0].solucao or ""

    for idx, problema in enumerate(problemas, start=1):
        texto_problema += f"Problema {idx}: {problema.descricao}\n"
        if problema.solucao:
            texto_solucao += f"Solução {idx}: {problema.solucao}\n"

    return texto_problema.strip(), texto_solucao.strip()