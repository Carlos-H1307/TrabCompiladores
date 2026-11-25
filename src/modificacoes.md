# Modificação 1 - Interface Visual Web para Execução de Diálogos

Implementação finalizada em: [`/visual/index.html`](../visual/index.html)

## Requisitos Atendidos:
1. **`dialog_manager`**: Gerencia o ciclo de vida completo dos diálogos, controle de fluxo e destruição do contêiner.
2. **`dialog_frame`**: Onde o texto dos diálogos é renderizado e clicável para avançar.
3. **`speaker_badge`**: O nome do personagem que fala aparece **destacado ACIMA do `dialog_frame`**.
4. **`choices_frame`**: Quando o jogador precisa responder, um diálogo com botões de opções é renderizado **ACIMA do `dialog_frame`**.
5. **Tags de Modificações Visuais**:
   - `[shake]` / `<shake>`: Efeito de tremor contínuo particionado na palavra.
   - `[bobbing]` / `<bobbing>`: Efeito de flutuação suave.
   - `[color=#hex]` / `<color=#hex>`: Modificação dinâmica de cor e brilho (glow).
   - `[b]` / `<strong>`: Negrito destacado.
6. **Destruição do Dialog Frame**: Ao encerrar os diálogos (ou escolher sair), o `dialog_frame` sofre animação de fade-out e é destruído/escondido, mantendo apenas a **cena main** ativa.

  
# Modificação 2

A interface visual deve ler o arquivo xml gerado pelo compilar e executar os dialogos baseado no fluxo descrito nele. Não deve ser um código imutável, mas sim mudar os diálogos em tempo de execução.

As letras das palavras dos diálogos devem aparecer sequencialmente, letra após letra.


## Alterações realizadas

Arquivos alterados: [`visual/index.html`](../visual/index.html) e [`src/parser.py`](parser.py).

### 1. Leitura do XML em tempo de execução (`visual/index.html`)
- Removido o roteiro fixo (`roteiroJogo`) que estava no código.
- A página faz `fetch` de `../src/saida_dialogos.xml` e interpreta o XML com `DOMParser` (`parseDialogosXML`), montando o grafo de diálogos a partir de `<dialog id speaker target>`, `<text>` e `<choices>/<choice target speaker>`.
- O primeiro `<dialog>` do XML é o ponto de partida; o fluxo (`target`, `choices`, `exit`) vem inteiramente do arquivo.
- O XML é relido a cada início ou "Reiniciar diálogo" (`cache: no-store`), então editar o roteiro, recompilar e reiniciar muda os diálogos sem recarregar a página.
- Se o `fetch` falhar (por exemplo, ao abrir via `file://`), aparece o botão **"Carregar XML..."** para escolher o arquivo manualmente.

### 2. Letras aparecendo sequencialmente (`visual/index.html`)
- O texto é particionado por `particionarTexto()` em uma lista de letras, cada uma com seu estilo (cor, negrito, `shake`, `bobbing`), a partir das tags `<tag>`, `<tag=valor>`, `</tag>` e `[tag]`.
- Cada letra vira um `<span>` próprio, inserido um a um por `DialogManager` (`proximaLetra` / `inserirLetra`), com intervalo de 28 ms.
- Pausa maior após `. ! ?` e menor após `, ; :`.
- Suporte à tag `<pause=500/>` para pausas manuais.
- Clicar ou apertar Espaço/Enter durante a digitação completa o texto na hora; um novo clique avança.
- As opções de escolha só aparecem depois que o texto termina de ser digitado.
- As palavras ficam agrupadas em `span.word` (sem quebra no meio da palavra).
- O texto é inserido com `textContent`, sem `innerHTML`, evitando injeção de HTML vinda do XML.

### 3. Ciclo de vida dos componentes
- `dialog_manager`, `dialog_frame`, `speaker_badge` e `choices_frame` agora são criados dinamicamente no início do diálogo.
- Ao terminar, o `dialog_manager` é removido do DOM (`root.remove()`), restando apenas a cena main.

### 4. Compilador (`src/parser.py`)
- Nova opção `--visual`: compila o roteiro, sobe um servidor HTTP local na raiz do projeto e abre `http://127.0.0.1:8000/visual/index.html`.
- O XML passa a ser sempre gravado em `src/saida_dialogos.xml` (caminho relativo ao script), onde a interface o procura.
- Removida a exportação para `visual/dialogos.js`, que deixaria os dados fixos no front-end.
- Corrigido o espaçamento do texto gerado: antes saía `Ei , Cachorro ...` e agora sai `Ei, Cachorro...`. Não há espaço antes de pontuação e de tags de fechamento, nem depois de tags de abertura (`_juntar_texto`).

### Como executar
```powershell
cd src
python parser.py roteiro.dialogo --visual
```

# Modificação 3
A regra de ter o nome do personagem na frase da opção não está funcionando. quando não houver o identificador do personagem na frase da opção, o compilador deve falha e mostrar onde está o erro pois antes de toda frase deve ter o identificador do personagem.



## Alterações realizadas

Arquivos alterados: [`src/parser.py`](parser.py) e [`src/roteiro.dialogo`](roteiro.dialogo).

### Problema
A gramática aceitava duas formas de opção: `ARROW SPEAKER text_sequence` e `ARROW text_sequence`. Por causa da segunda, uma opção sem `[Personagem]` compilava normalmente (o falante ficava `None`). Além disso, como o lexer descarta quebras de linha, uma frase escrita sem personagem na linha seguinte era absorvida pela frase anterior, sem aviso.

### 1. Identificador obrigatório na opção
- `p_choice_statement` agora só aceita `-> [Personagem] texto` seguido de `<<jump>>` ou `<<stop>>`.
- A forma sem personagem foi isolada em `p_choice_statement_sem_falante`, que existe apenas para apontar a linha exata do erro. Ao reconhecê-la, o compilador registra o erro e falha no final.

### 2. Frase sem personagem em outra linha
- Cada pedaço de texto agora guarda a linha em que começa e termina (classe `Texto`).
- Em `p_text_sequence`, se um novo pedaço começa em uma linha posterior à do anterior, a frase continua sem o identificador. Isso é registrado como erro, com a linha correta.

### 3. Falha com localização do erro
- Os erros são acumulados em `erros` (função `registrar_erro`) com tipo, linha, mensagem e dica.
- `imprimir_erros` mostra o arquivo, a linha, o trecho do roteiro e uma dica.
- Se houver qualquer erro, o compilador termina com código de saída 1 e **não gera** o `saida_dialogos.xml` (antes ele podia gerar um XML incompleto).
- `p_error` passou a registrar o erro e abortar a análise. Quando o erro é uma frase sem `[Personagem]`, a dica sugere esse motivo.
- O estado de erros e o contador de linhas são zerados a cada compilação (`definir_fonte`).

### 4. Roteiro de exemplo
- Em `roteiro.dialogo`, a opção `-> Por enquanto, não.` passou a `-> [Cachorro] Por enquanto, não.`. Sem isso o próprio exemplo deixaria de compilar. O XML correspondente indica `speaker="Cachorro"` nessa opção.

### Exemplos de saída

Opção sem personagem:
```text
[Erro Semântico] roteiro.dialogo, linha 7: a opção "Por enquanto, não." não tem o identificador do personagem.
       7 | -> Por enquanto, não.
    Dica: toda opção deve ser escrita como  -> [Personagem] texto da opção

Compilação interrompida: 1 erro(s). Nenhum XML foi gerado.
```

Frase sem personagem:
```text
[Erro Sintático] roteiro.dialogo, linha 3: token inesperado 'Oi' (tipo ID).
       3 | Oi sem falante.
    Dica: falta o identificador do personagem, [Personagem], antes desta frase?
```

Continuação sem personagem na linha seguinte:
```text
[Erro Semântico] roteiro.dialogo, linha 4: frase sem o identificador do personagem.
       4 | Segunda linha sem falante.
```

### Limitação conhecida
Caracteres inválidos para o lexer (por exemplo, hífen no meio do texto) ainda só imprimem um aviso léxico e a compilação continua.


> Resolvida na Modificação 4: agora `-` e `=` são aceitos no texto, e qualquer caractere inválido interrompe a compilação.


# Modificação 4 - Correções da análise léxica e semântica

Correções feitas a partir de testes com roteiros inválidos. Os casos ficam em `testes/casos/` e rodam com `python testes/rodar_testes.py`. A tabela de produções e ações semânticas está em [`docs/tabela_traducao.md`](../docs/tabela_traducao.md).

Arquivos alterados: [`src/lexer.py`](lexer.py), [`src/parser.py`](parser.py) e [`visual/index.html`](../visual/index.html). Cada regra nos fontes está marcada como `[ORIGINAL PLY]`, `[MODIFICADO]` ou `[NOVO]` em relação ao exemplo calc do PLY.

### Análise léxica
| Problema | Antes | Agora |
|---|---|---|
| `[b] Gato` (tag seguida de espaço) | virava o personagem "b" sem aviso | `SPEAKER` só é reconhecido no início da linha ou após `->`; no meio da frase o lexema é `MARKUP_OPEN` |
| `bem-vindo`, `2 = 2`, `e/ou` | `-` e `=` descartados com um aviso | aceitos no texto, desde que não formem `->`, `---`, `===` ou `//` |
| caractere inválido (`<`, colchete sem par) | só um aviso, e o XML era gerado | **Erro Léxico** com linha e dica; nenhum XML é gerado |
| `dialog_node:` (forma usada no prompt) | erro | sinônimo de `phrase:` |

### Análise sintática
- `:` e as palavras `jump`, `stop` e `phrase` podem aparecer dentro da fala (produções P20–P23). Antes, `Atenção: perigo` ou `Não dê stop` davam erro sintático. A tabela LALR continua sem conflitos.
- O espaço entre os pedaços de texto vem do próprio roteiro (atributo `espaco_antes`), não de uma regra baseada em pontuação. A função `_juntar_texto`, citada na Modificação 2, foi removida. Por isso `[pause=500/]Texto` não ganha mais um espaço extra.
- Dicas específicas no `p_error` conforme o token inesperado.

### Análise semântica (novas regras, ver S1–S12 na tabela)
- **S1–S3**: todo bloco tem pelo menos uma fala; as falas vêm antes das opções; o bloco termina com opções **ou** com exatamente um `<<jump>>`/`<<stop>>`. Antes, um bloco sem comando compilava, dois comandos eram aceitos (o último vencia) e opções podiam conviver com um `<<jump>>` solto.
- **S4**: falas de personagens diferentes no mesmo bloco são erro. Antes, o XML atribuía todas ao primeiro personagem.
- **S7–S10**: validação das tags de efeito com uma pilha: tag desconhecida, valor inválido (`[color=#zz]`, `[pause=rapido/]`), tag não fechada, fechada sem abrir e tags cruzadas. `[/]` fecha a última tag aberta e o XML recebe o nome dela.
- **S11**: ID de bloco duplicado deixou de ser aviso e passou a ser erro, com a linha da primeira definição.
- **S12**: os erros de salto passaram a indicar a linha do `<<jump>>`.
- **A1**: aviso (não bloqueia) para blocos que nunca são alcançados.

### Interface visual
- `[bold]` é reconhecido como sinônimo de `[b]`.
