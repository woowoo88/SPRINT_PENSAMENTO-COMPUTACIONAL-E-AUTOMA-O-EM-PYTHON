# Cenarios de teste

Estes cenarios podem ser reproduzidos diretamente no dashboard.

## 1. Pico com atuacao do DLM

Use os valores iniciais:

| Parametro | Valor |
|---|---:|
| Demanda contratada | 150 kW |
| Consumo do predio | 115 kW |
| Geracao solar | 18 kW |
| Suporte BESS | 10 kW |
| Horario | 19h |

Resultado esperado:

- os carregadores solicitam 84,4 kW;
- apenas 63 kW ficam disponiveis;
- o DLM evita 21,4 kW de ultrapassagem;
- carregadores prioritarios recebem uma parcela maior da potencia.

## 2. Operacao sem restricao

Altere somente o consumo do predio para 80 kW.

Resultado esperado:

- ficam disponiveis 98 kW;
- os 84,4 kW solicitados sao atendidos;
- todos os carregadores operam em carga nominal;
- o alerta informa que a operacao esta dentro dos limites.

## 3. Aproveitamento de energia solar

Configure:

| Parametro | Valor |
|---|---:|
| Consumo do predio | 80 kW |
| Geracao solar | 30 kW |
| Horario | 13h |

Resultado esperado:

- a geracao local aumenta a potencia disponivel;
- o sistema aplica a tarifa solar demonstrativa de R$ 0,62/kWh;
- a receita estimada muda conforme energia entregue, duracao e tarifa.

## 4. Comparacao com horario de ponta

Mantenha o mesmo cenario e altere o horario para 19h.

Resultado esperado:

- a tarifa muda para R$ 1,32/kWh;
- a receita estimada aumenta;
- o exemplo evidencia a influencia do horario no modulo de billing.

## Evidencias verificaveis

Para cada cenario, compare:

1. potencia disponivel;
2. potencia solicitada;
3. potencia alocada;
4. sobrecarga evitada;
5. status individual dos carregadores;
6. tarifa e receita estimada.

