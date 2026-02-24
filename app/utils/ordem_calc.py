from typing import List
from app.schemas.produto import ItemProdutoCreate
from app.schemas.servico import ServicoCreate



def calculaTotal(servicos: List[ServicoCreate], produtos: List[ItemProdutoCreate]):
    
    

    total = 0

    totalServ = 0
    if (servicos != None):
        for serv in servicos:
            total_serv = serv.quantidade*serv.valorUnitario
            desconto = total_serv*serv.desconto/100
            totalServ += total_serv - desconto
    
    totalProd = 0
    if (produtos != None):
        for prod in produtos:
            total_prod = prod.quantidade*prod.valorUnitario
            desconto = total_prod*prod.desconto/100
            totalProd += total_prod - desconto
    
    total = totalServ + totalProd
    return total, totalServ, totalProd



 
