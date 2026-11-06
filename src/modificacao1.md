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

  