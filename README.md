# Bioreactor Simulator (Docker + MQTT + UI)

Simulador didático de biorreator:
- **Python** (dinâmica simplificada)
- **MQTT** para sensores/atuadores
- **UI 2D** em SVG via WebSocket
- **Docker Compose** para subir tudo

## Rodando
```bash
docker compose up --build
# UI: http://localhost:8000
# MQTT: localhost:1883
```

## Variáveis de ambiente (serviço `sim`)
- `MQTT_HOST`/`MQTT_PORT`: broker MQTT
- `TICK_MS`: período de integração/telemetria (ms)
- `UI_ENABLED`: `true|false` habilita/desabilita UI e WS
- `SEED`: semente inicial do simulador (reprodutibilidade)

## Tópicos MQTT
- Sensores (QoS 1, retain): `bioreactor/sensors/{level|temperature|do|ph|agitation_rpm}`
- Estado agregado (só sensores): `bioreactor/state` (JSON)
- Atuadores (QoS 1, retain): `bioreactor/actuators/{valve_in|valve_out|heater|aeration|agitation}`
- Comandos de processo:
  - `bioreactor/cmd/{valve_in|valve_out}`: `0|1|on|off|true|false`
  - `bioreactor/cmd/{heater|aeration|agitation}`: `0..1` ou `on|off`
- Comandos de simulação:
  - `bioreactor/simCmd/reset` (payload opcional: `SEED` numérico)
  - `bioreactor/simCmd/time_scale` (`float`, ex.: `0.5`, `1`, `5`)

## Observações
- A UI é apenas visualização; opacidade de aquecimento e aeração refletem os comandos.
- `valve_out` inicia em `1` (aberta) por padrão.
 - O time scale padrão é `1.0` e pode ser alterado via `bioreactor/simCmd/time_scale`.

## Exemplos

A partir do host (broker local):

```bash
# Ajustar time scale para 2.0x (sim mais rápida)
mosquitto_pub -h localhost -t bioreactor/simCmd/time_scale -m 2.0

# Pausar evolução (time scale 0.0)
mosquitto_pub -h localhost -t bioreactor/simCmd/time_scale -m 0.0

# Resetar sim com seed 123
mosquitto_pub -h localhost -t bioreactor/simCmd/reset -m 123

# Resetar usando SEED atual do compose (payload vazio)
mosquitto_pub -h localhost -t bioreactor/simCmd/reset -n

# Atuar no processo (exemplos)
mosquitto_pub -h localhost -t bioreactor/cmd/heater -m 0.7
mosquitto_pub -h localhost -t bioreactor/cmd/valve_in -m on
```

Usando o container do broker (`mqtt`):

```bash
docker compose exec -T mqtt sh -lc "mosquitto_pub -t bioreactor/simCmd/time_scale -m 1.5"
docker compose exec -T mqtt sh -lc "mosquitto_pub -t bioreactor/simCmd/reset -m 42"

# Verificar publicações (sensores/atuadores)
docker compose exec -T mqtt sh -lc "mosquitto_sub -t 'bioreactor/state' -C 1 -v"
docker compose exec -T mqtt sh -lc "mosquitto_sub -t 'bioreactor/actuators/#' -C 5 -v"
```

## Tabela rápida de tópicos
- Sensores: `bioreactor/sensors/{level|temperature|do|ph|agitation_rpm}` — número; QoS 1; retain
- Estado agregado: `bioreactor/state` — JSON com sensores; QoS 1; retain
- Atuadores (publicados): `bioreactor/actuators/{valve_in|valve_out|heater|aeration|agitation}` — números (binários: 0/1; analógicos: 0..1); QoS 1; retain
- Comandos de processo (consumidos):
  - `bioreactor/cmd/{valve_in|valve_out}` — `0|1|on|off|true|false`
  - `bioreactor/cmd/{heater|aeration|agitation}` — `0..1` ou `on|off`
- Comandos de simulação (consumidos):
  - `bioreactor/simCmd/reset` — payload vazio usa `SEED`; número inteiro define seed
  - `bioreactor/simCmd/time_scale` — `float` (ex.: `0.0` pausa; `1.0` normal; `>1` acelera; faixa 0..50)


# Como testar

Subir: docker compose up -d --build
UI: http://localhost:8000/ui/ (redireciona de /)
Health: http://localhost:8000/health
MQTT (no container MQTT):
docker compose exec -T mqtt sh -lc "mosquitto_pub -t bioreactor/cmd/heater -m 0.8"
docker compose exec -T mqtt sh -lc "mosquitto_sub -t 'bioreactor/actuators/#' -v -C 5"
