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

docker compose build

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
	
	echo -e "${YELLOW} Desplegando infraestructura base...${NC}"
	docker compose up -d cache generador_respuestas

# --- FASE 1: UNIFORME ---
	echo -e "${CYAN} > Ejecutando Simulación UNIFORME...${NC}"
	docker compose run --rm -e SIMULATION_MODE=uniforme generador_trafico
	echo -e "${GREEN} > Generando Reporte UNIFORME...${NC}"
	docker compose run --rm -e MODO_METRICAS=uniforme metricas

# --- TRANSICIÓN CRÍTICA ---
# Forzamos al motor a reiniciarse para que vuelva a poner 'status:engine_ready' en Redis.
# Esto es necesario porque la simulación anterior probablemente borró esa llave por la política LRU/LFU.
	echo -e "${YELLOW} Re-sincronizando motor para distribución ZIPF...${NC}"
	docker compose restart generador_respuestas

# --- FASE 2: ZIPF ---
	echo -e "${CYAN} > Ejecutando Simulación ZIPF...${NC}"
	docker compose run --rm -e SIMULATION_MODE=zipf generador_trafico
	echo -e "${GREEN} > Generando Reporte ZIPF...${NC}"
	docker compose run --rm -e MODO_METRICAS=zipf metricas

	echo -e "${GREEN} Simulación completada para $tamano - $politica ${NC}"
	docker compose down -v
   done
done

draw_header "EXPERIMENTOS FINALIZADOS"
