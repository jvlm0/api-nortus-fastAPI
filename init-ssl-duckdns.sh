#!/bin/bash

# ============================================
# Script de inicialização SSL para DuckDNS
# ============================================

set -e  # Parar em caso de erro

# CONFIGURAÇÕES
domain="apinortus.duckdns.org"
email="seu-email@example.com"  # ALTERE AQUI
staging=0  # Mude para 1 para testar primeiro

# ============================================

data_path="./certbot"
rsa_key_size=4096

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Configuração SSL para DuckDNS${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Validações
if [ "$email" = "seu-email@example.com" ]; then
  echo -e "${RED}❌ ERRO: Altere o email no script!${NC}"
  exit 1
fi

echo -e "${YELLOW}📧 Email: $email${NC}"
echo -e "${YELLOW}🌐 Domínio: $domain${NC}"
echo ""

# Verificar se domínio resolve
echo -e "${YELLOW}🔍 Verificando DNS...${NC}"
if ! host $domain > /dev/null 2>&1; then
    echo -e "${RED}❌ ERRO: Domínio $domain não resolve!${NC}"
    echo "Verifique se o DuckDNS está configurado corretamente."
    exit 1
fi
echo -e "${GREEN}✓ DNS configurado${NC}"
echo ""

# Parar containers se estiverem rodando
echo -e "${YELLOW}🛑 Parando containers...${NC}"
docker-compose down 2>/dev/null || true
echo -e "${GREEN}✓ Containers parados${NC}"
echo ""

# Criar diretórios
echo -e "${YELLOW}📁 Criando diretórios...${NC}"
mkdir -p "$data_path/conf"
mkdir -p "$data_path/www/.well-known/acme-challenge"
mkdir -p nginx
echo -e "${GREEN}✓ Diretórios criados${NC}"
echo ""

# Baixar configurações SSL recomendadas
if [ ! -e "$data_path/conf/options-ssl-nginx.conf" ]; then
  echo -e "${YELLOW}⬇️  Baixando configurações SSL...${NC}"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$data_path/conf/options-ssl-nginx.conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$data_path/conf/ssl-dhparams.pem"
  echo -e "${GREEN}✓ Configurações SSL baixadas${NC}"
  echo ""
fi

# Usar configuração temporária do nginx (sem SSL)
echo -e "${YELLOW}📝 Configurando Nginx (modo HTTP)...${NC}"
if [ -f "nginx-temp.conf" ]; then
    cp nginx-temp.conf nginx/nginx.conf
    echo -e "${GREEN}✓ Configuração temporária aplicada${NC}"
else
    echo -e "${RED}❌ Arquivo nginx-temp.conf não encontrado!${NC}"
    exit 1
fi
echo ""

# Iniciar apenas API e Firebird
echo -e "${YELLOW}🚀 Iniciando serviços...${NC}"
docker-compose up -d firebird api
echo -e "${GREEN}✓ Firebird e API iniciados${NC}"
echo ""

# Aguardar serviços ficarem prontos
echo -e "${YELLOW}⏳ Aguardando serviços (10s)...${NC}"
sleep 10
echo -e "${GREEN}✓ Serviços prontos${NC}"
echo ""

# Iniciar Nginx
echo -e "${YELLOW}🌐 Iniciando Nginx...${NC}"
docker-compose up -d nginx
sleep 5
echo -e "${GREEN}✓ Nginx iniciado${NC}"
echo ""

# Verificar se nginx está acessível
echo -e "${YELLOW}🔍 Testando acesso HTTP...${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8081 | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✓ Nginx acessível${NC}"
else
    echo -e "${YELLOW}⚠️  Nginx pode não estar totalmente pronto${NC}"
fi
echo ""

# Selecionar servidor apropriado
if [ $staging != "0" ]; then 
    staging_arg="--staging"
    echo -e "${YELLOW}⚠️  Modo TESTE ativado (staging)${NC}"
else 
    staging_arg=""
fi

# Solicitar certificado (SOMENTE para o domínio principal, sem www)
echo -e "${YELLOW}🔐 Solicitando certificado Let's Encrypt...${NC}"
echo -e "${YELLOW}Aguarde, isso pode levar alguns minutos...${NC}"
echo ""

docker-compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    $staging_arg \
    -d $domain \
    --email $email \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    --verbose

# Verificar se certificado foi criado
if [ -d "$data_path/conf/live/$domain" ]; then
    echo ""
    echo -e "${GREEN}✓ Certificado obtido com sucesso!${NC}"
    echo ""
    
    # Aplicar configuração final com HTTPS
    echo -e "${YELLOW}📝 Aplicando configuração SSL...${NC}"
    if [ -f "nginx-final.conf" ]; then
        cp nginx-final.conf nginx/nginx.conf
        echo -e "${GREEN}✓ Configuração SSL aplicada${NC}"
    else
        echo -e "${RED}❌ Arquivo nginx-final.conf não encontrado!${NC}"
        exit 1
    fi
    echo ""
    
    # Reiniciar nginx com nova configuração
    echo -e "${YELLOW}🔄 Reiniciando Nginx...${NC}"
    docker-compose restart nginx
    sleep 3
    
    # Iniciar certbot para renovação automática
    echo -e "${YELLOW}🔄 Iniciando serviço de renovação...${NC}"
    docker-compose up -d certbot
    echo -e "${GREEN}✓ Renovação automática configurada${NC}"
    echo ""
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ Configuração concluída!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${GREEN}URLs de acesso:${NC}"
    echo -e "  HTTP:  ${YELLOW}http://$domain:8081${NC} (redireciona)"
    echo -e "  HTTPS: ${YELLOW}https://$domain:8443${NC}"
    echo -e "  Docs:  ${YELLOW}https://$domain:8443/docs${NC}"
    echo ""
    echo -e "${GREEN}Certificados em:${NC} $data_path/conf/live/$domain"
    echo -e "${YELLOW}Renovação automática: a cada 12 horas${NC}"
    echo ""
    
    # Testar HTTPS
    echo -e "${YELLOW}🧪 Testando HTTPS...${NC}"
    sleep 2
    if curl -k -s -o /dev/null -w "%{http_code}" https://localhost:8443 | grep -q "200\|301\|302"; then
        echo -e "${GREEN}✓ HTTPS funcionando!${NC}"
    else
        echo -e "${YELLOW}⚠️  HTTPS pode levar alguns segundos para ficar disponível${NC}"
    fi
    
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}❌ Falha ao obter certificado${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Verifique:${NC}"
    echo "1. Seu domínio DuckDNS está atualizado?"
    echo "2. A porta 80 está acessível externamente?"
    echo "3. Os logs do certbot (acima) para mais detalhes"
    echo ""
    echo -e "${YELLOW}Para testar primeiro (evitar rate limit):${NC}"
    echo "Edite este script e mude: staging=1"
    echo ""
    exit 1
fi