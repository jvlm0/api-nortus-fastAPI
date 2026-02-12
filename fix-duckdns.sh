#!/bin/bash

# ============================================
# Script Rápido de Correção - DuckDNS
# ============================================

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔧 Correção Rápida - Let's Encrypt DuckDNS${NC}"
echo ""

# 1. Parar containers
echo -e "${YELLOW}1. Parando containers...${NC}"
docker-compose down
echo -e "${GREEN}✓ Containers parados${NC}"
echo ""

# 2. Limpar certificados antigos
echo -e "${YELLOW}2. Limpando certificados antigos...${NC}"
sudo rm -rf certbot/conf/live 2>/dev/null || true
sudo rm -rf certbot/conf/archive 2>/dev/null || true
sudo rm -rf certbot/conf/renewal 2>/dev/null || true
echo -e "${GREEN}✓ Certificados limpos${NC}"
echo ""

# 3. Criar diretórios
echo -e "${YELLOW}3. Criando estrutura de diretórios...${NC}"
mkdir -p certbot/conf
mkdir -p certbot/www/.well-known/acme-challenge
mkdir -p nginx
echo -e "${GREEN}✓ Diretórios criados${NC}"
echo ""

# 4. Verificar arquivos necessários
echo -e "${YELLOW}4. Verificando arquivos...${NC}"

if [ ! -f "nginx-temp.conf" ]; then
    echo -e "${RED}❌ nginx-temp.conf não encontrado${NC}"
    exit 1
fi

if [ ! -f "nginx-final.conf" ]; then
    echo -e "${RED}❌ nginx-final.conf não encontrado${NC}"
    exit 1
fi

if [ ! -f "init-ssl-duckdns.sh" ]; then
    echo -e "${RED}❌ init-ssl-duckdns.sh não encontrado${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Todos os arquivos encontrados${NC}"
echo ""

# 5. Mover arquivos
echo -e "${YELLOW}5. Configurando arquivos...${NC}"
cp nginx-temp.conf nginx/nginx.conf
chmod +x init-ssl-duckdns.sh
echo -e "${GREEN}✓ Arquivos configurados${NC}"
echo ""

# 6. Verificar DNS
echo -e "${YELLOW}6. Verificando DNS...${NC}"
domain="apinortus.duckdns.org"

if host $domain > /dev/null 2>&1; then
    ip=$(host $domain | grep "has address" | awk '{print $4}')
    echo -e "${GREEN}✓ DNS resolve para: $ip${NC}"
else
    echo -e "${RED}❌ DNS não resolve!${NC}"
    echo "Verifique em: https://www.duckdns.org"
    exit 1
fi
echo ""

# 7. Verificar portas
echo -e "${YELLOW}7. Verificando portas necessárias...${NC}"
required_ports=(80 8081 8443)
for port in "${required_ports[@]}"; do
    if sudo netstat -tulpn 2>/dev/null | grep -q ":$port "; then
        echo -e "${YELLOW}⚠️  Porta $port já em uso${NC}"
    else
        echo -e "${GREEN}✓ Porta $port disponível${NC}"
    fi
done
echo ""

# 8. Instruções finais
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Preparação concluída!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Próximos passos:${NC}"
echo ""
echo -e "1️⃣  ${YELLOW}Edite o email no script:${NC}"
echo "   nano init-ssl-duckdns.sh"
echo "   Altere: email=\"seu-email@example.com\""
echo ""
echo -e "2️⃣  ${YELLOW}Para TESTAR primeiro (recomendado):${NC}"
echo "   nano init-ssl-duckdns.sh"
echo "   Mude: staging=1"
echo ""
echo -e "3️⃣  ${YELLOW}Execute o script:${NC}"
echo "   ./init-ssl-duckdns.sh"
echo ""
echo -e "4️⃣  ${YELLOW}Se funcionar em teste, rode em produção:${NC}"
echo "   nano init-ssl-duckdns.sh"
echo "   Mude: staging=0"
echo "   ./init-ssl-duckdns.sh"
echo ""
echo -e "${YELLOW}📌 IMPORTANTE:${NC}"
echo "- NÃO use 'www' com DuckDNS"
echo "- Certifique-se que porta 80 está acessível externamente"
echo "- Primeiro teste com staging=1"
echo ""