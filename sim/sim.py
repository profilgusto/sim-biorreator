from dataclasses import dataclass
import random, math

@dataclass
class State:
    t: float = 0.0                  # tempo de simulação [s]
    level: float = 50.0             # nível de líquido no tanque do biorreator [% da altura útil]
    temp: float = 30.0              # temperatura interna do caldo no biorreator [°C]
    od: float = 60.0                # concentração de oxigênio dissolvido (O.D.) no meio líquido [% de saturação]
    ph: float = 6.8                 # pH da mistura interna do biorreator [pH]
    agitation_rpm: float = 200.0    # velocidade do agitador mecânico do biorreator [rpm]
    X: float = 0.5                  # concentração de biomassa (micro-organismos) no caldo [g/L]
    pressure_kpa: float = 101.3     # pressão interna do headspace [kPa]


@dataclass
class Inputs:
    valve_in: int = 0               # estado da válvula de entrada (aberta/fechada) [adimensional]
    valve_out: int = 1              # estado da válvula de saída (aberta/fechada) [adimensional]
    heater: float = 0.0             # potência relativa do aquecedor (0 a 1, fração da potência máxima) [adimensional]
    aeration: float = 0.3           # taxa de aeração pelo difusor de ar (0 a 1, fração do fluxo máximo de ar) [adimensional]
    agitation: float = 0.5          # intensidade relativa de agitação (0 a 1, fração da velocidade máxima do motor) [adimensional]
    vent: float = 0.5               # abertura da válvula de exaustão (0..1) [adimensional]

class BioReactorSim:
    def __init__(self, seed=42):
        random.seed(seed)
        self.x = State()       # estado atual do processo (variáveis físicas medidas)
        self.u = Inputs()      # entradas de controle (atuadores)

        self.A = 0.05          # área da seção transversal do tanque [m²], usada no balanço de nível
        self.Qin_max = 0.001   # vazão máxima de entrada (quando válvula de entrada aberta) [m³/s]
        self.Qout_max = 0.001  # vazão máxima de saída (quando válvula de saída aberta) [m³/s]

        self.Cp = 1.5          # capacidade calorífica efetiva do caldo [kJ/(kg·K) ou unidade simplificada], usada no balanço de energia
        self.k_loss = 0.05     # coeficiente de perda de calor para o ambiente [1/s], representa dissipação térmica
        self.P_h = 5.0         # potência térmica nominal do aquecedor [kW] (valor máximo que o heater pode fornecer)
        self.Tamb = 25.0       # temperatura ambiente [°C], para onde o sistema troca calor

        self.ODsat = 100.0     # concentração de oxigênio dissolvido em saturação [%], valor de referência máximo de OD
        self.kla0 = 0.2        # coeficiente de transferência de oxigênio base (kLa) [1/s], escalado por aeração/agitação
        # Parâmetros de pressão no headspace

        self.Patm = 101.3      # pressão atmosférica de referência [kPa]
        self.k_pin = 2.0       # [kPa/s] ganho por aeração (entrada de gás eleva pressão)
        self.k_pout = 5.0      # [1/s] ganho de exaustão (multiplica (P-Patm)*vent)
        self.k_pgen = 0.2      # [kPa/s] geração por biomassa (produção de CO2 etc.)
        self.P_min = 95.0
        self.P_max = 200.0


    def step(self, dt: float):
        x, u = self.x, self.u

        Qin  = self.Qin_max  if u.valve_in  else 0.0
        Qout = self.Qout_max if u.valve_out else 0.0
        # Define as vazões de entrada e saída do tanque conforme o estado das válvulas:
        # - Se a válvula de entrada está aberta, usa a vazão máxima de entrada; caso contrário, 0.
        # - Idem para a saída.

        dL = (Qin - Qout)/self.A * dt
        # Balanço de volume/nível: variação do nível é (vazão líquida / área da seção) * passo de tempo.

        x.level = max(0, min(100, x.level + dL*10))
        # Atualiza o nível em [%]. O fator "*10" faz uma escala didática (transforma metros em “%” da altura útil).
        # Aplica saturação para manter o nível entre 0% e 100%.

        dT = ((self.P_h*u.heater) - self.k_loss*(x.temp - self.Tamb))/self.Cp * dt
        # Balanço de energia simples:
        # - Termo de aquecimento: potência do aquecedor (P_h) modulada por u.heater (0..1).
        # - Perdas térmicas: proporcional ao excesso de temperatura (x.temp - Tamb).
        # - Divide pela capacidade térmica efetiva (Cp) para obter dT/dt; depois multiplica por dt.

        x.temp += dT
        # Integra a temperatura no tempo (método de Euler explícito).

        kla = self.kla0 * (1 + 2*u.aeration + 1.5*u.agitation)
        # Coeficiente de transferência de oxigênio (kLa) aumentado pela aeração e agitação:
        # - Mais ar e mais agitação → maior transferência gás-líquido.

        ro2 = 0.03 * x.X
        # Consumo de O2 pela biomassa (termo simplificado): proporcional à concentração de biomassa X.

        # Saturação efetiva de OD escala com a pressão (Lei de Henry simplificada)
        ODsat_eff = self.ODsat * (x.pressure_kpa / self.Patm)
        dOD = (kla*(ODsat_eff - x.od) - ro2) * dt
        # Dinâmica do oxigênio dissolvido (OD):
        # - Ganho por transferência: kLa*(ODsat - OD) (tende à saturação).
        # - Perda por consumo microbiano: ro2.
        # - Integra no passo dt.

        x.od = max(0, min(150, x.od + dOD))
        # Atualiza OD e limita em um intervalo didático (0% a 150%) para evitar valores absurdos.

        x.ph += (-0.02*(x.ph - 6.8) + 0.01*(random.random()-0.5)) * dt
        # pH com relaxação para 6.8 (estado “nominal”) e um pequeno ruído aleatório para parecer medida real.

        x.ph = max(5.5, min(8.5, x.ph))
        # Limita pH a uma faixa plausível para manter estabilidade numérica e realismo básico.

        mu, Xmax = 0.08, 5.0
        # Parâmetros do crescimento da biomassa: taxa máxima (mu) e capacidade de carga (Xmax).

        x.X += mu*x.X*(1 - x.X/Xmax)*dt
        # Crescimento logístico da biomassa: rápido quando X é pequeno, saturando ao se aproximar de Xmax.

        x.agitation_rpm = 100 + 600*u.agitation
        # Converte a entrada adimensional de agitação (0..1) em rpm: 100 rpm mínimos + 600*rpm de faixa.

        dP = (
            self.k_pin * u.aeration
            - self.k_pout * u.vent * (x.pressure_kpa - self.Patm)
            + self.k_pgen * x.X
        )
        x.pressure_kpa = max(self.P_min, min(self.P_max, x.pressure_kpa + dP * dt))
        # Dinâmica de pressão do headspace (acoplada a aeração/exaustão e biomassa)
        # dP = k_pin*aeration - k_pout*vent*(P-Patm) + k_pgen*X

        x.temp += (random.random()-0.5)*0.02
        x.od   += (random.random()-0.5)*0.1
        # Injeta ruído de medição (pequeno) em temperatura e OD para simular sensores reais.

        x.t += dt
        # Avança o relógio de simulação.

    def actuators(self) -> dict:
        return {
            "valve_in": int(self.u.valve_in),
            "valve_out": int(self.u.valve_out),
            "heater": round(float(self.u.heater), 3),
            "aeration": round(float(self.u.aeration), 3),
            "agitation": round(float(self.u.agitation), 3),
            "vent": round(float(self.u.vent), 3),
        }

    def readout(self, include_actuators: bool = False):
        d = {
            "t": round(self.x.t, 2),
            "level": round(self.x.level, 1),
            "temperature": round(self.x.temp, 2),
            "do": round(self.x.od, 1),
            "ph": round(self.x.ph, 2),
            "agitation_rpm": round(self.x.agitation_rpm, 0),
            "biomass": round(self.x.X, 3),
            "pressure_kpa": round(self.x.pressure_kpa, 1),
        }
        if include_actuators:
            d.update(self.actuators())
        return d
