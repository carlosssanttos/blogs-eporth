---
tags: [ecoflow, delta-pro-ultra, instalação, elétrica, esquema, bifásico, trifásico]
fonte: RAW/pdfs (EcoFlow Valor — documentos técnicos)
data: 2026-05-11
---

# EcoFlow Delta Pro Ultra — Esquemas de Ligação Elétrica

> Referência técnica para instalação de **2 unidades Delta Pro Ultra** em paralelo, com transfer switch, nas duas configurações de entrada elétrica disponíveis no Brasil.

Arquivos originais: `RAW/pdfs/Esquema de ligação - Entrada Bifásica 127_220V - 2 Delta Pro Ultra.pdf` e `RAW/pdfs/Esquema de ligação - Entrada Trifásica 127_220V - 2 Delta Pro Ultra.pdf`

---

## Visão Geral

Ambos os esquemas mostram a mesma topologia base: **2 Delta Pro Ultra** conectados em paralelo, cada um com seu próprio transfer switch de dupla fonte (Fonte A / Fonte B). A diferença está na entrada elétrica que vem da rede.

| Ponto de comparação | Bifásico | Trifásico |
|---|---|---|
| Fases da rede | 2 (R + N) | 3 (R + S + T + N) |
| Disjuntor de entrada | 2 pólos | 3 pólos |
| Fios ativos do supply | Vermelho + Azul | Vermelho + Azul + Amarelo |
| Aplicação típica | Residências padrão, comércio leve | Indústria leve, comércio médio, instalações com cargas trifásicas |
| Saída | Barramentos de Neutro 1, Neutro 2 e Terra | Barramentos de Neutro 1, Neutro 2 e Terra |

---

## Esquema 1 — Entrada Bifásica 127/220V

### Descrição do diagrama

A entrada da rede elétrica chega com **2 fases + neutro** e é conectada a um disjuntor bipolar de entrada. A partir daí, o circuito se divide para alimentar os dois Delta Pro Ultra em paralelo.

### Componentes identificados

- **2× EcoFlow Delta Pro Ultra** — cada um com baterias expansoras empilhadas (visíveis no topo do diagrama)
- **2× Transfer Switch por unidade** com duas fontes:
  - **Fonte A (Principal)** — alimentação prioritária (rede elétrica)
  - **Fonte B (Secundária)** — alimentação de backup (quando Fonte A falha)
  - Terminais identificados como: **R · S · T · N**
- **1× Disjuntor bipolar** na entrada da rede (centro do diagrama)
- **Barramentos de saída** (na parte inferior):
  - Barramento 1 de Neutro (direita)
  - Barramento 2 de Neutro (esquerda)
  - Barramento Terra (lado direito)

### Fluxo de energia

```
REDE ELÉTRICA (bifásica)
        ↓
  Disjuntor bipolar
        ↓
  ┌─────┴─────┐
  │           │
Transfer    Transfer
Switch A    Switch B
(DPU 1)    (DPU 2)
  │           │
  └─────┬─────┘
        ↓
Barramentos Neutro 1 / Neutro 2 / Terra
        ↓
    Cargas da instalação
```

### Código de cores dos condutores

| Cor | Função |
|-----|--------|
| Vermelho | Fase ativa (L1) |
| Azul/Ciano | Neutro |
| Verde | Terra (PE) |

---

## Esquema 2 — Entrada Trifásica 127/220V

### Descrição do diagrama

A entrada da rede elétrica chega com **3 fases + neutro** e é conectada a um disjuntor tripolar de entrada. A topologia dos Delta Pro Ultra e transfer switches é idêntica ao esquema bifásico — a diferença está exclusivamente no supply da rede.

### Componentes identificados

Idênticos ao esquema bifásico, com a seguinte diferença:

- **1× Disjuntor tripolar** na entrada da rede (3 polos visíveis no centro do diagrama)
- **3 condutores ativos** na entrada (R + S + T), versus 2 no bifásico

### Fluxo de energia

```
REDE ELÉTRICA (trifásica)
        ↓
  Disjuntor tripolar
        ↓
  ┌─────┴─────┐
  │           │
Transfer    Transfer
Switch A    Switch B
(DPU 1)    (DPU 2)
  │           │
  └─────┬─────┘
        ↓
Barramentos Neutro 1 / Neutro 2 / Terra
        ↓
    Cargas da instalação
```

### Código de cores dos condutores

| Cor | Função |
|-----|--------|
| Vermelho | Fase R |
| Azul/Ciano | Fase S |
| Amarelo | Fase T |
| Verde | Terra (PE) |

---

## Pontos Críticos de Instalação

> Estas observações são derivadas da leitura dos diagramas. Para projetos reais, sempre exigir ART de eletricista habilitado.

1. **Transfer switch obrigatório** — cada Delta Pro Ultra opera com seu próprio transfer switch; não compartilhar entre as duas unidades
2. **Dois barramentos de neutro separados** — o esquema prevê Neutro 1 (DPU 1) e Neutro 2 (DPU 2); manter separados conforme o diagrama
3. **Barramento terra unificado** — os dois DPUs compartilham o mesmo barramento de terra
4. **Disjuntor na entrada** — sempre dimensionar o disjuntor de acordo com a corrente máxima de carregamento dos dois DPU em paralelo
5. **Terminais R·S·T·N** — presentes em ambos os transfer switches independente de ser bifásico ou trifásico; no bifásico, T fica sem conexão

---

## Quando Indicar Cada Esquema

| Perfil do cliente | Entrada recomendada |
|---|---|
| Residência padrão (maioria das casas brasileiras) | **Bifásico** |
| Comercial/industrial com quadro trifásico | **Trifásico** |
| Propriedade rural com gerador trifásico | **Trifásico** |
| Home office, condomínio, apartamento | **Bifásico** |

---

## Relacionados

- [[ecoflow-delta-pro|Linha Delta Pro — Produtos e Specs]]
- [[precificacao-powersafe|Precificação Powersafe]]
- [[portfolio-ecoflow|Portfolio EcoFlow — Visão Geral]]
