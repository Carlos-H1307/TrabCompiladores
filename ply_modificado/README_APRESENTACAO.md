# Documentação do Trabalho de Compiladores (P2 - Parte 2)

## 1. Identificação do Projeto
- **Nome do Projeto:** DSL Robô Virtual / Geometria Turtle (`robo_lang`)
- **Gerador de Analisadores Utilizado:** PLY (Python Lex-Yacc) versão 3.11
- **Linguagem Base:** Python
- **Pasta:** `ply_modificado/`
- **Arquivo Principal:** `robo_lang.py`
- **Arquivo de Teste:** `programa_teste.robo`

---

## 2. Prompt Utilizado na IA (Item 3 do PDF)
Este prompt deve ser apresentado ao professor e exibido nos slides:

> *"Atue como um especialista em compiladores e crie uma Domain-Specific Language (DSL) em Python utilizando a biblioteca PLY (Python Lex-Yacc), modificando a estrutura padrão do exemplo de calculadora (`calc.py`). A linguagem deve ser uma DSL de controle de robô virtual (inspirada em Logo/Turtle) para atender aos critérios de não ser uma calculadora. Implemente:*
> 1. *Analisador Léxico com tokens para palavras reservadas em português (`frente`, `tras`, `esquerda`, `direita`, `levantar`, `abaixar`, `repetir`, `cor`, `status`, `reset`, `print`), números reais, identificadores, strings e delimitadores, com suporte a comentários de linha `//`.*
> 2. *Analisador Sintático LALR com regras de produção para lista de comandos, atribuição de variáveis, expressões aritméticas com precedência e associatividade, além de estrutura de repetição com blocos entre chaves `{ ... }`.*
> 3. *Ações Semânticas Dirigidas pela Sintaxe que manipulam o estado de um robô virtual em 2D (coordenadas x, y, ângulo em graus, controle de caneta abaixada/levantada, cor e tabela de símbolos de variáveis).*
> 4. *Suporte a execução via arquivo `.robo` e modo interativo (REPL)."*

---

## 3. Modificações em Relação ao `calc.py` Original (Item 4.b do PDF)

| Aspecto | `calc.py` Original | `robo_lang.py` Modificado |
|---|---|---|
| **Objetivo** | Avaliar expressões aritméticas simples em uma linha. | DSL para controle de traçado vetorial e estado de robô 2D. |
| **Tokens Léxicos** | Apenas operadores básicos (`+`, `-`, `*`, `/`, `=`) e `NAME`, `NUMBER`. | Adicionados tokens para palavras reservadas (`FORWARD`, `BACKWARD`, `LEFT`, `RIGHT`, `PENUP`, `PENDOWN`, `REPEAT`, `COLOR`, `STATUS`, `RESET`, `PRINT`), strings (`STRING`), chaves (`{`, `}`) e ponto-e-vírgula (`;`). |
| **Comentários** | Não suportava comentários. | Suporte a comentários no estilo C/Java: `// comentário`. |
| **Gramática** | Uma instrução por linha (`statement : NAME = expression` ou `statement : expression`). | Gramática para programas estruturados com sequência de declarações (`statement_list`), blocos aninhados (`repeat N { ... }`) e comandos imperativos. |
| **Ações Semânticas** | Apenas cálculos numéricos imediatos. | Manipulação do estado do robô (cálculo trigonométrico com seno e cosseno para translação, rotação angular, alternância de estado de desenho e persistência em tabela de símbolos). |

---

## 4. Tabela de Produções e Ações Semânticas (Item 4.c do PDF)

| Produção Gramatical | Ação Semântica (Tradução Dirigida pela Sintaxe) |
|---|---|
| `program -> statement_list` | `p[0] = p[1]` (Retorna a árvore do programa) |
| `statement -> FORWARD expression ;` | `distancia = p[2]`; calcula nova posição $(x + d \cdot \cos(\theta), y + d \cdot \sin(\theta))$ e move o robô. |
| `statement -> BACKWARD expression ;` | Move o robô na direção oposta ao ângulo atual. |
| `statement -> LEFT expression ;` | `angulo = p[2]`; atualiza orientação: $\theta \leftarrow (\theta + \text{angulo}) \pmod{360}$. |
| `statement -> RIGHT expression ;` | `angulo = p[2]`; atualiza orientação: $\theta \leftarrow (\theta - \text{angulo}) \pmod{360}$. |
| `statement -> PENUP ;` | Define `robo.caneta_abaixada = False` (não deixa rastro). |
| `statement -> PENDOWN ;` | Define `robo.caneta_abaixada = True` (desenha rastro). |
| `statement -> COLOR STRING ;` | Altera a cor ativa do robô para `p[2]`. |
| `statement -> NAME = expression ;` | Armazena o valor na tabela de variáveis: `robo.variaveis[NAME] = expression.val`. |
| `statement -> REPEAT expression { statement_list }` | Itera `N = int(expression.val)` vezes reexecutando as ações do bloco. |
| `statement -> STATUS ;` | Exibe coordenadas atuais, orientação e estado da caneta. |
| `statement -> RESET ;` | Restaura a posição para $(0,0)$, ângulo para $90^\circ$ e caneta abaixada. |
| `expression -> expression + expression` | `p[0] = p[1] + p[3]` |
| `expression -> expression * expression` | `p[0] = p[1] * p[3]` |
| `expression -> ( expression )` | `p[0] = p[2]` |
| `expression -> NUMBER` | `p[0] = float(NUMBER.val)` |
| `expression -> NAME` | `p[0] = lookup(NAME)` (Busca valor na tabela de símbolos) |

---

## 5. Exemplo de Árvore de Derivação e Derivação Anotada (Item 4.d do PDF)

Considere a sentença aceita:
```
frente 50 + 10;
```

### Árvore de Derivação Concreta (Parse Tree)
```
                  program
                     |
               statement_list
                     |
                 statement
    _________________|_________________
   |        |             |            |
FORWARD  expression       ;          (fim)
            |
     +------+------+
     |      |      |
  expr1     +    expr2
    |              |
 NUMBER          NUMBER
  (50)            (10)
```

### Árvore de Derivação Anotada (com Atributos Sintetizados)
```
                           program
                              |
                        statement_list
                              |
                 statement [executa: mover(60.0)]
    _________________|___________________________
   |                 |                           |
FORWARD      expression [val = 60.0]             ;
                     |
       +-------------+-------------+
       |             |             |
expr1 [val = 50.0]   +    expr2 [val = 10.0]
       |                           |
NUMBER [val = 50.0]         NUMBER [val = 10.0]
```

---

## 6. Como Executar (Item 4.e do PDF)

No terminal PowerShell:

### Modo Arquivo:
```powershell
python ply_modificado/robo_lang.py ply_modificado/programa_teste.robo
```

### Modo Interativo (REPL):
```powershell
python ply_modificado/robo_lang.py
```
*Exemplo no REPL:*
```text
robo > reset;
robo > cor "AZUL";
robo > frente 50;
robo > direita 90;
robo > status;
robo > sair
```

