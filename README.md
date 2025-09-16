# Simulador Simplificado de Biorreator
UFSJ/CAP – Engenharia Mecatrônica
Simulador com dinâmica simplificada para fins didáticos para a disciplina de Sistemas Supervisórios.

Simulador didático de biorreator:
- **Python** (dinâmica simplificada)
- **MQTT** para comunicação com sensores/atuadores da planta
- **UI 2D** em SVG via WebSocket
- **Docker Compose** para subir tudo

## Rodando
Navegue no terminal até a pasta do pacote e execute:
```bash
docker compose up --build
```

- Para visualizar a UI do simulador, acesse no navegador `http://localhost:8000`.


## MQTT 
É levantado um servidor MQTT no endereço: `localhost:1883`

### Tópicos MQTT
- Sensores (QoS 1, retain): `bioreactor/sensors/{level|temperature|do|ph|agitation_rpm}`
- Estado agregado (só sensores): `bioreactor/state` (JSON)
- Atuadores (QoS 1, retain): `bioreactor/actuators/{valve_in|valve_out|heater|aeration|agitation}`
- Comandos de processo:
  - `bioreactor/cmd/{valve_in|valve_out}`: `0|1|on|off|true|false`
  - `bioreactor/cmd/{heater|aeration|agitation}`: `0..1` ou `on|off`
- Comandos de simulação:
  - `bioreactor/simCmd/reset` (payload opcional: `SEED` numérico)
  - `bioreactor/simCmd/time_scale` (`float`, ex.: `0.5`, `1`, `5`)


### Exemplos

#### A partir do host (broker local):

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
NOTA: Estes comandos consideram que a máquina host possui o `mosquitto` instalado.


#### Usando o container do broker (`mqtt`):

```bash
docker compose exec -T mqtt sh -lc "mosquitto_pub -t bioreactor/simCmd/time_scale -m 1.5"
docker compose exec -T mqtt sh -lc "mosquitto_pub -t bioreactor/simCmd/reset -m 42"

# Verificar publicações (sensores/atuadores)
docker compose exec -T mqtt sh -lc "mosquitto_sub -t 'bioreactor/state' -C 1 -v"
docker compose exec -T mqtt sh -lc "mosquitto_sub -t 'bioreactor/actuators/#' -C 5 -v"
```
NOTA: Estes comandos executam comandos do `mosquitto` em execução no container do MQTT.


### Observações
- A UI é apenas visualização; opacidade de aquecimento e aeração refletem os comandos.
- `valve_out` inicia em `1` (aberta) por padrão.
 - O time scale padrão é `1.0` e pode ser alterado via `bioreactor/simCmd/time_scale`.

