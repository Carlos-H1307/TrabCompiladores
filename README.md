# DialogueDSL – Compilador de Diálogos para Jogos

Trabalho de Compiladores (2026/2). Um compilador, feito com **PLY (Python Lex-Yacc)**, que lê roteiros de diálogo em uma linguagem própria (inspirada no Yarn Spinner), valida o fluxo e gera um **XML**. Uma interface web lê esse XML em tempo de execução e roda o diálogo como em um jogo.

```
roteiro.dialogo ──► lexer.py ──► parser.py ──► saida_dialogos.xml ──► visual/index.html
   (DSL)           (tokens)    (gramática,      (formato do jogo)      (diálogo no navegador)
                                semântica, XML)
```

## Estrutura

```
trabalho/
├── src/
│   ├── lexer.py              # Análise léxica (tokens)
│   ├── parser.py             # Análise sintática, semântica, geração do XML e servidor visual
│   ├── roteiro.dialogo       # Roteiro de exemplo (entrada)
│   ├── roteiro_passaros.dialogo  # Roteiro maior, usado nas árvores de derivação
│   ├── saida_dialogos.xml    # XML gerado (saída)
│   ├── prompt.md             # Prompt usado na ferramenta de IA
│   └── modificacoes.md       # Registro das modificações implementadas
├── docs/
│   └── tabela_traducao.md    # Regras léxicas, produções, ações e regras semânticas
├── testes/
│   ├── casos/                # Roteiros válidos e inválidos com o resultado esperado
│   └── rodar_testes.py       # Executa todos os casos
├── visual/
│   └── index.html            # Interface web que lê o XML e executa os diálogos
├── arvore_concreta_passaros.png  # Árvore de derivação
└── arvore_anotada_passaros_final_light.png  # Árvore de derivação anotada
```

Nos fontes, cada regra está marcada como `[ORIGINAL PLY]`, `[MODIFICADO]` ou `[NOVO]` em relação ao exemplo calc do PLY.

## Requisitos

- **Python 3** (testado com 3.15)
- **PLY**
- Um navegador moderno (Chrome, Edge, Firefox)

```powershell
pip install ply
```

> Se o `pip` não for reconhecido no Windows, use `python -m pip install ply`.

## Como executar

Todos os comandos abaixo partem da pasta `src`:

```powershell
cd src
```

### 1. Compilar o roteiro (gera o XML)

```powershell
python parser.py roteiro.dialogo
```

Isso faz as análises léxica e sintática, valida os saltos (`jump`) e escolhas e grava `src/saida_dialogos.xml`.

### 2. Abrir a interface visual (recomendado)

```powershell
python parser.py roteiro.dialogo --visual
```

Compila, sobe um servidor local e abre `http://127.0.0.1:8000/visual/index.html` no navegador. Use **Ctrl+C** no terminal para encerrar o servidor.

**Controles:**
- **Clique** na caixa de diálogo ou **Espaço/Enter**: avança. Durante a digitação, completa o texto na hora.
- **Botões de opção**: escolhem a resposta e seguem o fluxo.
- Ao fim do diálogo, o `dialog_frame` é destruído e só a cena principal permanece. O botão **Reiniciar diálogo** relê o XML.

**Editando o roteiro sem fechar o navegador:** altere `roteiro.dialogo`, rode `python parser.py roteiro.dialogo` em outro terminal e clique em **Reiniciar diálogo**. O XML é relido a cada início.

### 3. Jogar no terminal

```powershell
python parser.py roteiro.dialogo --jogar
```

### 4. Ver os tokens do analisador léxico

```powershell
python lexer.py roteiro.dialogo
```

### 5. Rodar os testes (a partir da raiz do projeto)

```powershell
python testes/rodar_testes.py
```

### Abrindo o `index.html` direto (sem servidor)

O navegador bloqueia a leitura do XML quando a página é aberta por duplo clique (`file://`). Nesse caso use o botão **Carregar XML...** na tela e selecione `src/saida_dialogos.xml`.

## A linguagem (DialogueDSL)

```text
// comentário
phrase: 001                                   // início de um bloco (id do diálogo)
---
[Rato] Ei, Cachorro... Está procurando [shake][color=#d6d6d6]algo[/color][/shake]?
-> [Cachorro] Sim, sim. Minha [color=#f00]Pochete[/color].
    <<jump 002>>                              // opção do jogador e destino
-> Por enquanto, não.
    <<stop>>                                  // encerra o diálogo
===                                           // fim do bloco
```

| Elemento | Sintaxe | Significado |
|---|---|---|
| Bloco | `phrase: ID` ... `---` ... `===` | Um diálogo identificado por `ID` (`dialog_node:` também é aceito) |
| Falante | `[Nome] texto` | Quem fala; aparece sobre a caixa de diálogo |
| Escolha | `-> [Falante] texto` + comando | Opção do jogador (falante é opcional) |
| Salto | `<<jump ID>>` | Vai para o diálogo `ID` |
| Fim | `<<stop>>` | Encerra a conversa |
| Comentário | `// ...` | Ignorado pelo compilador |
| Efeitos | `[shake]`, `[bobbing]`, `[b]`/`[bold]`, `[color=#hex]` ... `[/tag]` ou `[/]` | Efeitos visuais no texto |
| Pausa | `<pause=500/>` | Pausa (ms) durante a digitação |

Regras de cada bloco (verificadas pelo compilador):

1. Começa com uma ou mais falas `[Personagem] texto`, todas do **mesmo** personagem.
2. Termina com opções `-> [Personagem] texto` (cada uma com o seu `<<jump ID>>`/`<<stop>>`) **ou** com exatamente um `<<jump ID>>`/`<<stop>>`.
3. As tags de efeito precisam ser conhecidas e estar balanceadas: `[a][b]...[/b][/a]`.
4. Todo `jump` aponta para um `phrase` existente, e os IDs não se repetem.

O `[Personagem]` só é reconhecido no início da linha (ou logo após `->`). No meio da frase, `[nome]` é uma tag de efeito.

## Saída gerada (`saida_dialogos.xml`)

```xml
<conversation>
  <dialog id="001" speaker="Rato">
    <text>Ei, Cachorro... Está procurando &lt;shake&gt;...</text>
    <choices>
      <choice target="002" speaker="Cachorro"><text>Sim, sim. ...</text></choice>
      <choice target="exit"><text>Por enquanto, não.</text></choice>
    </choices>
  </dialog>
  <dialog id="002" speaker="Rato" target="003">...</dialog>
</conversation>
```

`target="exit"` indica o fim do diálogo.

## Erros comuns

| Mensagem | Causa / solução |
|---|---|
| `pip`/`python` não reconhecido | Python fora do `PATH`. Reabra o terminal ou use o caminho completo do executável. |
| `[Erro Léxico] ... caractere inválido` | `<`, `>` ou colchete sem par no texto. |
| `[Erro Sintático] ... token inesperado` | Bloco mal formado (falta `---`, `===` ou comando após a escolha). |
| `[Erro Semântico] ... bloco sem <<jump ID>> ou <<stop>>` | Toda fala precisa indicar o próximo passo. |
| `[Erro Semântico] ... fala de 'X' dentro de um bloco de 'Y'` | Um bloco tem um único personagem; use outro `phrase`. |
| `[Erro Semântico] ... tag desconhecida / não foi fechada / tags cruzadas` | Confira os efeitos `[tag]...[/tag]`. |
| `[Erro Semântico] ... que não existe` | Um `jump` ou escolha aponta para um `phrase` que não existe. |
| `Não consegui ler o XML do compilador` | Abra via `--visual` ou use **Carregar XML...**. |
| `Port already in use` | Outro servidor usa a porta 8000; encerre-o e rode de novo. |

## Tecnologias

Python 3, PLY (lex/yacc), HTML/CSS/JavaScript puro.

