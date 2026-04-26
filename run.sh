#!/bin/bash

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Configuraciones de tamaños de redis y politicas (LRU y LFU)
TAMANOS=("50mb" "200mb" "500mb")
POLITICAS=("allkeys-lru" "allkeys-lfu")

draw_header() {
	local titulo=$1
	echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
	printf "${CYAN}║${NC}  ${YELLOW}%-58s${NC}  ${CYAN}║${NC}\n" " $titulo"
	echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
}
clear

draw_header "INICIANDO BATERÍA DE EXPERIMENTOS"


# Ejemplo dentro de un bucle
for tamano in "${TAMANOS[@]}"; do
    for politica in "${POLITICAS[@]}"; do
	echo -e "\n${BLUE}┌──────────────────────────────────────────────────────────────┐${NC}"
        echo -e "${BLUE}│${NC}  ${PURPLE}CONFIGURACIÓN ACTUAL${NC}"                    
        echo -e "${BLUE}├──────────────────────────────────────────────────────────────┤${NC}"
        echo -e "${BLUE}│${NC}  > Memoria Máxima: ${GREEN}$tamano${NC}"                
        echo -e "${BLUE}│${NC}  > Política:       ${GREEN}$politica${NC}"              
        echo -e "${BLUE}└──────────────────────────────────────────────────────────────┘${NC}"

	
	export REDIS_MAX_MEMORY=$tamano
	export REDIS_POLICY=$politica
	
	echo -e "${YELLOW} Desplegando contenedores Caché y Generador respuestas${NC}"
	docker compose up -d --remove-orphans cache generador_respuestas
	
	echo -e "${YELLOW} Ejecutando simulación de tráfico ${NC}"
	docker compose run generador_trafico

	echo -e "${GREEN}Simulación completada para $tamano - $politica${NC}"

	echo -e "${YELLOW}Limpiando volúmenes y contenedores...${NC}"
	docker compose down -v
   done
done

draw_header "EXPERIMENTOS FINALIZADOS"
