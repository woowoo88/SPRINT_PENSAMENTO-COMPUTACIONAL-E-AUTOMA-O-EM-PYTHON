# Arquitetura da prova de conceito

## Visao geral

A solucao foi dividida em quatro camadas para manter responsabilidades claras:

1. **Interface:** dashboard HTML, CSS e JavaScript.
2. **Aplicacao:** API HTTP implementada com a biblioteca padrao do Python.
3. **Dominio:** gerenciamento de carga, tarifacao e gateway de protocolo.
4. **Analise:** modelo de regressao para previsao de demanda.

## Fluxo de uma simulacao

1. O usuario informa as condicoes energeticas da instalacao.
2. O dashboard envia o cenario para `POST /api/simulate`.
3. O simulador calcula a margem da rede, considerando solar e BESS.
4. O DLM distribui a potencia entre os carregadores ativos.
5. O gateway informa o protocolo normalizado de cada equipamento.
6. O modulo de billing calcula energia, tarifa e receita estimada.
7. O modelo preditivo gera a curva de demanda de 24 horas.
8. A API devolve resultados e alertas para o dashboard.

## Regras de negocio

### Limite eletrico

A energia retirada da rede nunca deve superar a demanda contratada. Solar e
BESS sao tratados como fontes locais que ampliam a potencia disponivel para os
carregadores.

### Prioridade

Cada categoria possui um peso:

| Categoria | Peso |
|---|---:|
| Normal | 1,00 |
| Premium | 1,35 |
| Frota | 1,70 |
| Emergencia | 2,20 |

O nivel de bateria acrescenta urgencia: quanto menor a bateria, maior o peso.

### Tarifacao demonstrativa

| Condicao | Tarifa |
|---|---:|
| Ponta, das 18h as 22h | R$ 1,32/kWh |
| Solar, das 10h as 16h com pelo menos 20 kW | R$ 0,62/kWh |
| Fora de ponta | R$ 0,88/kWh |

Os valores sao parametros didaticos da simulacao, nao tarifas oficiais.

## Endpoints

| Metodo | Rota | Uso |
|---|---|---|
| GET | `/api/health` | Verificacao do servidor |
| GET | `/api/default` | Cenario inicial |
| POST | `/api/simulate` | Execucao da simulacao |

## Evolucao em relacao a Sprint 1

Na Sprint 1, DLM, billing, protocolos e IA foram apresentados como propostas.
Nesta Sprint 2, esses elementos passaram a possuir entradas, regras,
processamento, resultados visuais e testes automatizados.

