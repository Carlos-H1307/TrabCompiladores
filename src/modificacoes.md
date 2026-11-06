# Modificação 1 - Interface Visual Web para Execução de Diálogos

Implementação finalizada em: [`/visual/index.html`](file:///d:/Cefet/2026_2/Compiladores/trabalho/visual/index.html)

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

Arquivos alterados: [`visual/index.html`](file:///d:/Cefet/2026_2/Compiladores/trabalho/visual/index.html) e [`src/parser.py`](file:///d:/Cefet/2026_2/Compiladores/trabalho/src/parser.py).

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



## Alterações realizadas

Arquivos alterados: [`visual/index.html`](file:///d:/Cefet/2026_2/Compiladores/trabalho/visual/index.html) e [`src/parser.py`](file:///d:/Cefet/2026_2/Compiladores/trabalho/src/parser.py).

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
