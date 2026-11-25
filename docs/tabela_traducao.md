# DialogueDSL: Tabela de Tradução Dirigida pela Sintaxe

Gerador: **PLY (Python Lex-Yacc)**, analisador **LALR(1)**. A tabela gerada pelo PLY (`src/parser.out`) tem **0 conflitos** shift/reduce e reduce/reduce.

Os códigos `[L*]`, `[P*]` e `[S*]` aparecem como comentários em `src/lexer.py` e `src/parser.py`, ao lado da regra correspondente.

## 1. Análise léxica (`src/lexer.py`)

| Regra | Token | Expressão regular | Observação |
|---|---|---|---|
| L1 | `NODE_END` | `===` | fim do bloco |
| L2 | `HEADER_DELIM` | `---` | início do corpo do bloco |
| L3 | `COMMAND_START` | `<<` | abre comando |
| L4 | `COMMAND_END` | `>>` | fecha comando |
| L5 | `ARROW` | `->` | opção do jogador |
| L6 | `COLON` | `:` | cabeçalho `phrase: ID` (também aceito no texto) |
| L7 | `SPEAKER` | `\[[a-zA-ZÀ-ÿ_][a-zA-ZÀ-ÿ0-9_ ]*\]` | só no **início da linha** ou após `->`. Em outra posição vira `MARKUP_OPEN` |
| L8 | `MARKUP_CLOSE` | `\[\/[a-zA-Z0-9_]*\]` | `[/shake]` ou `[/]` |
| L9 | `MARKUP_SELF` | `\[[a-zA-Z0-9_]+(=[^\]\/]+)?\/\]` | `[pause=500/]` |
| L10 | `MARKUP_OPEN` | `\[[a-zA-Z0-9_]+(=[^\]]+)?\]` | `[shake]`, `[color=#f00]` |
| L11 | (descartado) | `//.*` | comentário |
| L12 | `ID` / reservadas | `[a-zA-ZÀ-ÿ_0-9]+` | `phrase`/`dialog_node` → `PHRASE`, `jump` → `JUMP`, `stop` → `STOP` |
| L13 | `TEXT` | `(?:[^\s\[\]<>\-=:/]\|-(?!>\|--)\|=(?!==)\|/(?!/))+` | pontuação e símbolos; `-`, `=` e `/` só quando não formam `->`, `---`, `===`, `//` |

Espaços, tabs e `\r` são ignorados (`t_ignore`). `\n` atualiza o número da linha (`t_newline`). Um caractere que nenhuma regra reconhece (`<`, `>`, colchete sem par) gera **Erro Léxico** e a compilação falha.

**Ordem das regras:** no PLY, as regras escritas como função são testadas na ordem do arquivo. Por isso `===`, `---`, `<<`, `>>` e `->` vêm antes de `TEXT`. Essa ordem, junto com a verificação de posição em L7, elimina a ambiguidade léxica entre `[Personagem]` e `[tag]`.

## 2. Produções e ações semânticas (`src/parser.py`)

Notação: `X.val` é o atributo **sintetizado** do símbolo X (o `p[0]` do PLY). `tok.lex` é o valor do token e `tok.linha` é a linha dele. Todos os atributos são sintetizados, ou seja, a definição é **S-atribuída** e é avaliada de baixo para cima durante as reduções LALR.

| # | Produção | Ação semântica |
|---|---|---|
| P1 | `conversation → node_list` | `conversation.val = {type:'conversation', nodes: node_list.val}` |
| P2 | `node_list → node_list₁ node` | `node_list.val = node_list₁.val + [node.val]` |
| P3 | `node_list → node` | `node_list.val = [node.val]` |
| P4 | `node → PHRASE COLON ID HEADER_DELIM body NODE_END` | `node.val = {id: ID.lex, linha: PHRASE.linha, lines: body.lines, choices: body.choices, jump: body.jump, jump_linha: body.jump_linha}` |
| P5 | `body → statement_list` | separa `statement_list.val` em `lines`, `choices` e `comandos`; aplica **S1–S4**; `body.jump = cmd.target`, ou `'exit'` se for `stop` |
| P6 | `statement_list → statement_list₁ statement` | `statement_list.val = statement_list₁.val + [statement.val]` |
| P7 | `statement_list → statement` | `statement_list.val = [statement.val]` |
| P8 | `statement → dialogue_line` | `statement.val = dialogue_line.val` |
| P9 | `statement → choice_statement` | `statement.val = choice_statement.val` |
| P10 | `statement → command_statement` | `statement.val = command_statement.val` |
| P11 | `dialogue_line → SPEAKER text_sequence` | **S7**; `dialogue_line.val = {type:'line', speaker: SPEAKER.lex, text: validar_marcacoes(text_sequence.val), linha: SPEAKER.linha}` |
| P12 | `choice_statement → ARROW SPEAKER text_sequence command_statement` | **S7**; `choice_statement.val = {type:'choice', speaker: SPEAKER.lex, text: validar_marcacoes(text_sequence.val), target: (cmd.action = jump ? cmd.target : 'exit')}` |
| P13 | `choice_statement → ARROW text_sequence command_statement` | **S6**: registra o erro "opção sem identificador do personagem" (produção de erro) |
| P14 | `command_statement → COMMAND_START JUMP ID COMMAND_END` | `command_statement.val = {type:'command', action:'jump', target: ID.lex, linha: COMMAND_START.linha}` |
| P15 | `command_statement → COMMAND_START STOP COMMAND_END` | `command_statement.val = {type:'command', action:'stop', linha: COMMAND_START.linha}` |
| P16 | `text_sequence → text_sequence₁ text_item` | **S5**; `text_sequence.val = text_sequence₁.val ⧺ (text_item.espaco ? ' ' : '') ⧺ text_item.val`; `marcas = text_sequence₁.marcas + text_item.marcas`; `linha_fim = text_item.linha` |
| P17 | `text_sequence → text_item` | `text_sequence.val = text_item.val` (com os mesmos atributos) |
| P18 | `text_item → TEXT` | `text_item.val = TEXT.lex`; `espaco` = havia espaço antes no roteiro |
| P19 | `text_item → ID` | `text_item.val = ID.lex` |
| P20 | `text_item → COLON` | `text_item.val = ':'` |
| P21 | `text_item → JUMP` | `text_item.val = JUMP.lex` (permite "jump" dentro da fala) |
| P22 | `text_item → STOP` | `text_item.val = STOP.lex` (permite "stop" dentro da fala) |
| P23 | `text_item → PHRASE` | `text_item.val = PHRASE.lex` (permite "phrase" dentro da fala) |
| P24 | `text_item → MARKUP_OPEN` | `text_item.val = '<' ⧺ lex ⧺ '>'`; `marcas = [{abre, nome, valor}]` |
| P25 | `text_item → MARKUP_CLOSE` | `text_item.val = '</' ⧺ lex ⧺ '>'`; `marcas = [{fecha, nome}]` |
| P26 | `text_item → MARKUP_SELF` | `text_item.val = '<' ⧺ lex ⧺ '/>'`; `marcas = [{auto, nome, valor}]` |

Após a análise sintática, a ação do símbolo inicial produz a AST (`conversation.val`). Sobre ela rodam **S11** e **S12** (grafo de diálogos) e depois a **geração de código** (`compilar_para_xml`), que emite um `<dialog id speaker target>` por bloco, com `<text>` e `<choices>/<choice target speaker>`.

### Ambiguidade e precedência

A calculadora do PLY precisa da tabela `precedence` porque `E → E + E | E * E` é ambígua. A gramática da DialogueDSL **não é ambígua**: cada construção começa por um token diferente (`PHRASE`, `SPEAKER`, `ARROW`, `<<`). Por isso a tabela LALR é gerada sem conflitos e não há regras de precedência. As listas (`node_list`, `statement_list`, `text_sequence`) usam **recursão à esquerda**, a forma recomendada para LALR.

## 3. Regras semânticas

| Regra | Onde | Verificação | Mensagem |
|---|---|---|---|
| S1 | P5 | todo bloco tem pelo menos uma fala | `bloco sem fala de personagem` |
| S2 | P5 | falas vêm antes das opções e do comando | `fala depois de uma opção ou de um comando de fluxo` |
| S3 | P5 | o bloco termina com opções **ou** com exatamente um `<<jump>>`/`<<stop>>` | `bloco sem <<jump ID>> ou <<stop>>`, `mais de um comando de fluxo`, `bloco com opções não pode ter um <<jump>>/<<stop>> solto` |
| S4 | P5 | todas as falas do bloco são do mesmo personagem (o XML tem um `speaker` por `<dialog>`) | `fala de 'Gato' dentro de um bloco de 'Rato'` |
| S5 | P16 | o texto não continua em outra linha sem `[Personagem]` | `frase sem o identificador do personagem` |
| S6 | P13 | toda opção tem `[Personagem]` | `a opção "..." não tem o identificador do personagem` |
| S7 | P11, P12 | o personagem não é o nome de uma tag (ex.: `[shake]` no início da linha) | `[shake] está no lugar do identificador do personagem` |
| S8 | P11, P12 | toda tag é conhecida e usada na forma certa (`[pause=ms/]` é autocontida; as demais têm abertura e fechamento) | `tag desconhecida [piscar]` |
| S9 | P11, P12 | o valor da tag tem o tipo certo: `color` exige uma cor; `pause` exige um inteiro; as demais não aceitam valor | `cor inválida em [color=#zz]`, `tempo inválido em [pause=rapido/]` |
| S10 | P11, P12 | as tags estão balanceadas (verificação com **pilha**); `[/]` fecha a última aberta | `tags cruzadas`, `fecha uma tag que não foi aberta`, `foi aberta e não foi fechada` |
| S11 | AST | IDs de bloco únicos | `phrase 'x' já foi definida na linha N` |
| S12 | AST | todo `jump` e toda opção apontam para um bloco existente | `salto para a phrase 'x', que não existe` |
| A1 | AST | (aviso) bloco que não é alcançado a partir do primeiro | `a phrase 'x' nunca é alcançada` |

Qualquer erro léxico, sintático ou semântico interrompe a compilação, com código de saída 1 e **nenhum XML gerado**. As mensagens mostram arquivo, linha, o trecho do roteiro e uma dica.

## 4. Exemplo de tradução

Entrada (a mesma sentença das árvores `arvore_concreta_passaros.png` e `arvore_anotada_passaros_final_light.png`, compilada sozinha):

```text
phrase: final_bom
---
[Pipo] [bobbing]Piooo![/bobbing]
<<stop>>
===
```

| Redução | Atributo sintetizado |
|---|---|
| P24 `text_item → MARKUP_OPEN` | `'<bobbing>'`, marcas = [abre bobbing] |
| P17 `text_sequence → text_item` | `'<bobbing>'` |
| P19 `text_item → ID` | `'Piooo'` (sem espaço antes) |
| P16 | `'<bobbing>Piooo'` |
| P18 `text_item → TEXT` | `'!'` |
| P16 | `'<bobbing>Piooo!'` |
| P25 `text_item → MARKUP_CLOSE` | `'</bobbing>'`, marcas = [fecha bobbing] |
| P16 | `'<bobbing>Piooo!</bobbing>'`, marcas = [abre bobbing, fecha bobbing] |
| P11 `dialogue_line` | S7 ok, S10 ok → `{type:'line', speaker:'Pipo', text:'<bobbing>Piooo!</bobbing>', linha:3}` |
| P15 `command_statement` | `{type:'command', action:'stop', linha:4}` |
| P5 `body` | S1–S4 ok → `{lines:[…], choices:[], jump:'exit', jump_linha:4}` |
| P4 `node` | `{id:'final_bom', linha:1, lines:[…], choices:[], jump:'exit', jump_linha:4}` |

Saída XML:

```xml
<dialog id="final_bom" speaker="Pipo" target="exit">
	<text>&lt;bobbing&gt;Piooo!&lt;/bobbing&gt;</text>
</dialog>
```
