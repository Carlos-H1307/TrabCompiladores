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
│   ├── saida_dialogos.xml    # XML gerado (saída)
│   └── modificacoes.md       # Registro das modificações implementadas
├── visual/
│   └── index.html            # Interface web que lê o XML e executa os diálogos
└── ply_modificado/           # Exemplo anterior (DSL do robô); não faz parte do compilador de diálogos
```

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
python lexer.py
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
| Bloco | `phrase: ID` ... `---` ... `===` | Um diálogo identificado por `ID` |
| Falante | `[Nome] texto` | Quem fala; aparece sobre a caixa de diálogo |
| Escolha | `-> [Falante] texto` + comando | Opção do jogador (falante é opcional) |
| Salto | `<<jump ID>>` | Vai para o diálogo `ID` |
| Fim | `<<stop>>` | Encerra a conversa |
| Comentário | `// ...` | Ignorado pelo compilador |
| Efeitos | `[shake]`, `[bobbing]`, `[b]`, `[color=#hex]` ... `[/tag]` | Efeitos visuais no texto |
| Pausa | `<pause=500/>` | Pausa (ms) durante a digitação |

Um bloco sem escolha termina com `<<jump ID>>` (segue para o próximo) ou `<<stop>>` (fim).

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
| `Erro Sintático próximo ao token ...` | Bloco mal formado (falta `---`, `===` ou comando após a escolha). |
| `[Erro Semântico] ... destino inexistente` | Um `jump` ou escolha aponta para um `phrase` que não existe. |
| `Não consegui ler o XML do compilador` | Abra via `--visual` ou use **Carregar XML...**. |
| `Port already in use` | Outro servidor usa a porta 8000; encerre-o e rode de novo. |

## Tecnologias

Python 3, PLY (lex/yacc), HTML/CSS/JavaScript puro.

