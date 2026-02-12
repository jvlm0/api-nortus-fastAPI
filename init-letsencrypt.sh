#!/bin/bash

# ============================================
# Script de inicialização do Let's Encrypt
# ============================================

# CONFIGURAÇÕES - ALTERE AQUI
domains=(apinortus.duckdns.org www.apinortus.duckdns.org)
email="seu-email@exemplo.com" # Email para notificações de renovação
staging=0 # Mude para 1 para testar (evita rate limit)

# ============================================

data_path="./certbot"
rsa_key_size=4096

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Inicializando certificados SSL${NC}"
echo -e "${GREEN}========================================${NC}"

# Validações
if [ "$email" = "seu-email@example.com" ]; then
  echo -e "${RED}❌ ERRO: Você precisa alterar o email no script!${NC}"
  exit 1
fi

if [[ " ${domains[@]} " =~ "seudominio.com.br" ]]; then
  echo -e "${RED}❌ ERRO: Você precisa alterar o domínio no script!${NC}"
  exit 1
fi

echo -e "${YELLOW}📧 Email: $email${NC}"
echo -e "${YELLOW}🌐 Domínios: ${domains[*]}${NC}"
echo ""

# Criar diretórios necessários
if [ ! -e "$data_path/conf/options-ssl-nginx.conf" ] || [ ! -e "$data_path/conf/ssl-dhparams.pem" ]; then
  echo "### Baixando configurações SSL recomendadas..."
  mkdir -p "$data_path/conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$data_path/conf/options-ssl-nginx.conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$data_path/conf/ssl-dhparams.pem"
  echo -e "${GREEN}✓ Configurações SSL baixadas${NC}"
fi

echo ""
echo "### Criando certificado temporário para ${domains[0]}..."
path="/etc/letsencrypt/live/${domains[0]}"
mkdir -p "$data_path/conf/live/${domains[0]}"

docker-compose run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1\
    -keyout '$path/privkey.pem' \
    -out '$path/fullchain.pem' \
    -subj '/CN=localhost'" certbot
echo -e "${GREEN}✓ Certificado temporário criado${NC}"

echo ""
echo "### Iniciando nginx..."
docker-compose up --force-recreate -d nginx
echo -e "${GREEN}✓ Nginx iniciado${NC}"

echo ""
echo "### Deletando certificado temporário..."
docker-compose run --rm --entrypoint "\
  rm -rf /etc/letsencrypt/live/${domains[0]} && \
  rm -rf /etc/letsencrypt/archive/${domains[0]} && \
  rm -rf /etc/letsencrypt/renewal/${domains[0]}.conf" certbot
echo -e "${GREEN}✓ Certificado temporário removido${NC}"

echo ""
echo "### Solicitando certificado Let's Encrypt..."

# Selecionar servidor apropriado
if [ $staging != "0" ]; then staging_arg="--staging"; else staging_arg=""; fi

# Construir argumentos de domínio
domain_args=""
for domain in "${domains[@]}"; do
  domain_args="$domain_args -d $domain"
done

# Solicitar certificado
docker-compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $staging_arg \
    $domain_args \
    --email $email \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --no-eff-email \
    --force-renewal" certbot

echo ""
echo "### Recarregando nginx..."
docker-compose exec nginx nginx -s reload

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Configuração concluída!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Seus certificados estão em: ${YELLOW}$data_path/conf/live/${domains[0]}${NC}"
echo ""
echo -e "${GREEN}URLs de acesso:${NC}"
echo -e "  HTTP:  http://${domains[0]}:8081 ${YELLOW}(redireciona para HTTPS)${NC}"
echo -e "  HTTPS: https://${domains[0]}:8443"
echo ""
echo -e "${YELLOW}Nota: Os certificados serão renovados automaticamente a cada 12 horas${NC}"