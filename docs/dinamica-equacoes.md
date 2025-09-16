# Dinamica do Simulador de Biorreator

Este arquivo resume as principais equacoes implementadas em `sim/sim.py` para atualizar as variaveis de estado a cada passo de integracao com passo `dt` efetivo (ajustado pelo `time_scale`). As expressoes abaixo ignoram os pequenos ruidos aleatorios adicionados para simular medidas reais, mas indicam a estrutura deterministica da dinamica.

## Variaveis de processo e atuadores

- `L` : nivel do liquido no tanque (% da altura util)
- `T` : temperatura do caldo (deg C)
- `OD` : oxigenio dissolvido (% de saturacao)
- `pH` : pH do meio
- `X` : concentracao de biomassa (g/L)
- `N_rpm` : velocidade do agitador (rpm)
- `P` : pressao no headspace (kPa)
- `u_valve_in`, `u_valve_out` : abertura das valvulas de entrada/saida (0 ou 1)
- `u_heater`, `u_aeration`, `u_agitation`, `u_vent` : atuadores continuos (0..1)

Constantes relevantes: area da secao `A`, vasoes maximas `Q_in_max`, `Q_out_max`, parametros termicos `P_h`, `k_loss`, `T_amb`, transferencia de oxigenio `kla0`, consumo `k_ro2`, saturacao `OD_sat`, pressao atmosferica `P_atm`, ganhos de pressao `k_pin`, `k_pout`, `k_pgen`, limites de pressao `P_min`, `P_max`, taxa de crescimento `mu`, capacidade de carga `X_max`.

## Balanco de nivel

O nivel eh atualizado com base nas vazoes ligadas ao estado das valvulas, convertido para escala percentual:

$$$ Q_{in} = u_{valve\_in} \cdot Q_{in\_max} $$$
$$$ Q_{out} = u_{valve\_out} \cdot Q_{out\_max} $$$
$$$ L_{k+1} = \operatorname{clamp}_{[0,100]}\Big( L_k + 10 \cdot \frac{Q_{in} - Q_{out}}{A} \cdot dt \Big) $$$

## Balanco de energia (temperatura)

A temperatura responde ao aquecedor e as perdas para o ambiente:

$$$ \frac{dT}{dt} = \frac{P_h \cdot u_{heater} - k_{loss} (T - T_{amb})}{C_p} $$$
$$$ T_{k+1} = T_k + \frac{dT}{dt} \cdot dt $$$

## Oxigenio dissolvido

O coeficiente de transferencia eh amplificado por aeracao e agitacao. O consumo microbiano eh proporcional a `X`.

$$$ k_{La} = k_{La0} \cdot (1 + 2 u_{aeration} + 1.5 u_{agitation}) $$$
$$$ OD_{sat}^{eff} = OD_{sat} \cdot \frac{P}{P_{atm}} $$$
$$$ \frac{dOD}{dt} = k_{La} (OD_{sat}^{eff} - OD) - 0.03 X $$$
$$$ OD_{k+1} = \operatorname{clamp}_{[0,150]}\Big( OD_k + \frac{dOD}{dt} \cdot dt \Big) $$$

## Dinamica de pH

O pH relaxa para 6.8 com termo amortecedor (ruido omitido):

$$$ \frac{dpH}{dt} = -0.02 (pH - 6.8) $$$
$$$ pH_{k+1} = \operatorname{clamp}_{[5.5,8.5]}\Big( pH_k + \frac{dpH}{dt} \cdot dt \Big) $$$

## Crescimento de biomassa

A biomassa segue modelo logistico:

$$$ \frac{dX}{dt} = \mu X \Big( 1 - \frac{X}{X_{max}} \Big) $$$
$$$ X_{k+1} = X_k + \frac{dX}{dt} \cdot dt $$$

## Conversao de agitacao

O atuador adimensional eh convertido em rpm:

$$$ N_{rpm} = 100 + 600 \cdot u_{agitation} $$$

## Pressao no headspace

A pressao responde a aeracao, abertura da valvula de exaustao e geracao biologica, com saturacao entre `P_min` e `P_max`:

$$$ \frac{dP}{dt} = k_{pin} \cdot u_{aeration} - k_{pout} \cdot u_{vent} (P - P_{atm}) + k_{pgen} X $$$
$$$ P_{k+1} = \operatorname{clamp}_{[P_{min}, P_{max}]}\Big( P_k + \frac{dP}{dt} \cdot dt \Big) $$$

## Tempo de simulacao

O relogio interno acumula o passo:

$$$ t_{k+1} = t_k + dt $$$

## Observacao sobre ruidos

O codigo adiciona ruidos gaussianos uniformes de pequena amplitude em `T`, `OD` e `pH` apos as equacoes acima para representar incerteza de medicao. Esses termos nao alteram o modelo medio, mas conferem realismo as leituras.

