# Instrumentacao do Biorreator

## Sensores

| Sigla | Instrumento | Faixa de operacao nominal | Topico MQTT | Tipo de variavel |
| --- | --- | --- | --- | --- |
| LT-101 | Nivel do tanque | 0 - 100% da altura util (`clamp` no modelo) | `bioreactor/sensors/level` | `float` (% com 1 casa) |
| TT-102 | Temperatura do caldo | Sem saturacao; balanco termico gira em torno de 25-80 deg C | `bioreactor/sensors/temperature` | `float` (deg C com 2 casas) |
| AIT-103 | Oxigenio dissolvido | 0 - 150% de saturacao (limite didatico) | `bioreactor/sensors/do` | `float` (% com 1 casa) |
| AIT-104 | pH | 5.5 - 8.5 | `bioreactor/sensors/ph` | `float` (pH com 2 casas) |
| ST-105 | Agitacao medida | 100 - 700 rpm (derivado do comando 0-1) | `bioreactor/sensors/agitation_rpm` | `float` (rpm inteiro) |
| AIT-106 | Biomassa (X) | Crescimento logistico ate ~5 g/L | `bioreactor/sensors/biomass` | `float` (g/L com 3 casas) |
| PT-107 | Pressao no headspace | 95 - 200 kPa | `bioreactor/sensors/pressure_kpa` | `float` (kPa com 1 casa) |

## Atuadores

| Sigla | Instrumento | Faixa de operacao nominal | Topico MQTT | Tipo de variavel |
| --- | --- | --- | --- | --- |
| XV-201 | Valvula de entrada | 0 (fechada) ou 1 (aberta) | `bioreactor/cmd/valve_in` | `int`/`bool` |
| XV-202 | Valvula de saida | 0 (fechada) ou 1 (aberta) | `bioreactor/cmd/valve_out` | `int`/`bool` |
| EH-203 | Aquecedor (potencia relativa) | 0.0 - 1.0 (fracao da potencia nominal) | `bioreactor/cmd/heater` | `float` (0-1) |
| FV-204 | Aeracao (controle de fluxo) | 0.0 - 1.0 (fracao do fluxo maximo) | `bioreactor/cmd/aeration` | `float` (0-1) |
| AC-205 | Setpoint de agitacao | 0.0 - 1.0 (escala que vira 100-700 rpm) | `bioreactor/cmd/agitation` | `float` (0-1) |
| XV-206 | Valvula de exaustao (vent) | 0.0 - 1.0 (abertura relativa) | `bioreactor/cmd/vent` | `float` (0-1) |

## Valores nominais dos atuadores

| Sigla | Descricao | Valor nominal usado no modelo |
| --- | --- | --- |
| XV-201 | Valvula de entrada do processo | Vazao maxima `Q_in_max = 0.001 m^3/s` (equivalente a ~60 L/min) quando aberta |
| XV-202 | Valvula de saida do processo | Vazao maxima `Q_out_max = 0.001 m^3/s` (~60 L/min) quando aberta |
| EH-203 | Aquecedor eletrico | Potencia termica nominal `P_h = 5.0 kW` para comando 1.0 |
| FV-204 | Valvula de aeracao | Fluxo relativo 100%; no modelo a contribuicao maxima gera `k_pin = 2 kPa/s` no termo de pressurizacao |
| AC-205 | Controle da agitacao mecanica | Comando 1.0 corresponde a 700 rpm (100 rpm no minimo) |
| XV-206 | Valvula de exaustao do headspace | Abertura 100% aplica `k_pout = 5 1/s` sobre `(P - P_atm)` |

_Na simulacao, os atuadores tambem sao publicados em `bioreactor/actuators/*` para facilitar a inspecao do estado retido no broker._

