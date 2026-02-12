#!/bin/bash

# ============================================
# Script de Deploy Completo com HTTPS
# ============================================

set -e  # Parar em caso de erro

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Deploy da Aplicação com HTTPS${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Função para verificar se comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar Docker
if ! command_exists docker; then
    echo -e "${RED}❌ Docker não está instalado!${NC}"
    echo "Instale o Docker: https://docs.docker.com/engine/install/"
    exit 1
fi

# Verificar Docker Compose
if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker Compose não está instalado!${NC}"
    echo "Instale o Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker instalado${NC}"
echo -e "${GREEN}✓ Docker Compose instalado${NC}"
echo ""

# Criar diretórios necessários
echo -e "${YELLOW}📁 Criando estrutura de diretórios...${NC}"
mkdir -p nginx
mkdir -p certbot/conf
mkdir -p certbot/www
mkdir -p firebird_data
echo -e "${GREEN}✓ Diretórios criados${NC}"
echo ""

# Verificar se arquivo .env existe
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Arquivo .env não encontrado. Criando template...${NC}"
    cat > .env << 'EOF'
# Configurações do Banco de Dados Firebird
FIREBIRD_HOST=firebird
FIREBIRD_PORT=3050
FIREBIRD_DATABASE=/firebird/data/APPUSERS.FDB
FIREBIRD_USER=SYSDBA
FIREBIRD_PASSWORD=masterkey

# Configurações da API
API_TITLE=Minha API
API_VERSION=1.0.0
DEBUG=False
EOF
    echo -e "${GREEN}✓ Arquivo .env criado${NC}"
    echo -e "${YELLOW}⚠️  Revise o arquivo .env antes de continuar!${NC}"
    echo ""
fi

# Verificar se docker-compose.yml existe
if [ ! -f docker-compose.yml ]; then
    echo -e "${RED}❌ Arquivo docker-compose.yml não encontrado!${NC}"
    exit 1
fi

# Verificar se nginx.conf existe
if [ ! -f nginx/nginx.conf ]; then
    echo -e "${RED}❌ Arquivo nginx/nginx.conf não encontrado!${NC}"
    echo "Execute primeiro: mv nginx.conf nginx/nginx.conf"
    exit 1
fi

# Perguntar se deseja parar containers existentes
if [ "$(docker ps -q -f name=fastapi_app)" ] || [ "$(docker ps -q -f name=nginx_proxy)" ]; then
    echo -e "${YELLOW}⚠️  Containers já estão rodando.${NC}"
    read -p "Deseja parar e recriar? (s/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        echo -e "${YELLOW}🛑 Parando containers...${NC}"
        docker-compose down
        echo -e "${GREEN}✓ Containers parados${NC}"
        echo ""
    fi
fi

# Build das imagens
echo -e "${YELLOW}🔨 Construindo imagens Docker...${NC}"
docker-compose build --no-cache
echo -e "${GREEN}✓ Imagens construídas${NC}"
echo ""

# Iniciar banco de dados primeiro
echo -e "${YELLOW}🗄️  Iniciando banco de dados Firebird...${NC}"
docker-compose up -d firebird
echo -e "${GREEN}✓ Firebird iniciado${NC}"
echo ""

# Aguardar banco de dados ficar pronto
echo -e "${YELLOW}⏳ Aguardando Firebird ficar pronto (10s)...${NC}"
sleep 10
echo -e "${GREEN}✓ Firebird pronto${NC}"
echo ""

# Iniciar API
echo -e "${YELLOW}🚀 Iniciando API FastAPI...${NC}"
docker-compose up -d api
echo -e "${GREEN}✓ API iniciada${NC}"
echo ""

# Aguardar API ficar pronta
echo -e "${YELLOW}⏳ Aguardando API ficar pronta (5s)...${NC}"
sleep 5
echo -e "${GREEN}✓ API pronta${NC}"
echo ""

# Verificar se certificados SSL já existem
if [ -d "certbot/conf/live" ] && [ "$(ls -A certbot/conf/live)" ]; then
    echo -e "${GREEN}✓ Certificados SSL já existem${NC}"
    echo -e "${YELLOW}🔄 Iniciando Nginx e Certbot...${NC}"
    docker-compose up -d nginx certbot
    echo -e "${GREEN}✓ Nginx e Certbot iniciados${NC}"
else
    echo -e "${YELLOW}⚠️  Certificados SSL não encontrados${NC}"
    echo -e "${YELLOW}Execute: ./init-letsencrypt.sh para configurar HTTPS${NC}"
    echo ""
    read -p "Deseja iniciar sem HTTPS por enquanto? (s/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        docker-compose up -d nginx
        echo -e "${GREEN}✓ Nginx iniciado (sem HTTPS)${NC}"
    fi
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Status dos Containers${NC}"
echo -e "${BLUE}========================================${NC}"
docker-compose ps

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Deploy concluído!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Mostrar URLs de acesso
if [ -d "certbot/conf/live" ] && [ "$(ls -A certbot/conf/live)" ]; then
    echo -e "${GREEN}🌐 URLs de acesso:${NC}"
    echo -e "  HTTPS: ${YELLOW}https://apinortus.duckdns.org:8443${NC}"
    echo -e "  HTTP:  ${YELLOW}http://apinortus.duckdns.org:8081${NC} (redireciona para HTTPS)"
    echo -e "  Docs:  ${YELLOW}https://apinortus.duckdns.org:8443/docs${NC}"
else
    echo -e "${YELLOW}🌐 URLs de acesso (HTTP apenas):${NC}"
    echo -e "  HTTP:  ${YELLOW}http://apinortus.duckdns.org:8081${NC}"
    echo -e "  Docs:  ${YELLOW}http://apinortus.duckdns.org:8081/docs${NC}"
    echo ""
    echo -e "${YELLOW}Para habilitar HTTPS, execute: ./init-letsencrypt.sh${NC}"
fi

echo ""
echo -e "${BLUE}📊 Comandos úteis:${NC}"
echo -e "  Ver logs:           ${YELLOW}docker-compose logs -f${NC}"
echo -e "  Parar aplicação:    ${YELLOW}docker-compose down${NC}"
echo -e "  Reiniciar:          ${YELLOW}docker-compose restart${NC}"
echo -e "  Status:             ${YELLOW}docker-compose ps${NC}"
echo ""