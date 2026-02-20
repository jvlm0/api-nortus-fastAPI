from typing import List
from app.schemas.servico import ServicoCreate



def calculaTotal(servicos: List[ServicoCreate]):
    
    if (servicos == None): return 0

    total = 0

    for serv in servicos:
        total_serv = serv.quantidade*serv.valorUnitario
        desconto = total_serv*serv.desconto/100
        total+= total_serv - desconto
    
    return total, total



 
