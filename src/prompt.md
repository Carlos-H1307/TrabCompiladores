dialog_node: 001
---
[Rato] Ei, Cachorro... Está procurando [shake][color=#d6d6d6]algo[/color][/shake]?
-> [Cachorro] Sim, sim. Minha [color=#f00]Pochete[/color].
    <<jump 002>>
-> [Cachorro] Por enquanto, não.
    <<stop>>
===

dialog_node: 002
---
[Rato] Um Cachorro? De Pochete?
<<jump 003>>
===

dialog_node: 003
---
[Rato] Estranho.
<<jump 004>>
===

dialog_node: 004
---
[Rato] Enfim...
<<jump 005>>
===

dialog_node: 005
---
[Rato] Eu vi um [bold]Gato [shake]suspeito[/shake][/bold] passando com algo bem de baixo do [color=#10c8e0]SUVACO[/color], agorinha pouco.
<<jump 006>>
===

dialog_node: 006
---
[Rato] Ele desceu. Acho que pode estar com o que você procura.
-> [Cachorro] Humm... Vou dar uma olhada. Valeu, Rato!
    <<jump 007>>
===

dialog_node: 007
---
[Rato] De nada.
<<stop>>
===


Com base neste exemplo, atualize o modifique os arquivos lexer.py e parser.py.

O arquivo começa com o comando "dialog_node: <numero>". Este número representa o ID da fala do personagem. Cada frase contém um ID único, porque após uma fala pode haver uma resposta encaminhando, a partir do ID, a um outro dialo_node. O que está entre --- e === compõe um único dialog_node. Dentro do dialog_node há, necessariamente, uma frase do personagem que está falando. Após, pode haver opções que divergem o caminho do diálogo.

O dialog_node deve ter, obrigatoriamente uma frase que é composta por um identificador com o nome do personagem que está falando, depois um texto. Necessariamente nesta ordem. Essa estrutura de Personagem + Frase também compõem uma option.

Cada frase deve ser seguida, obrigatoriamente, de um "<<jump x>>" ou "<<stop>>" para indicar o próximo passo. Enquanto "<<jump x>>" mostra para qual dialog_node o diálogo deve seguir, "<<stop>>" encerra o diálogo.

Nas frases, exceto no identificador do personagem, pode ou não haver modificadores para animar as palavras. Em um primeiro momento os modificadores são: 
- bold
- shake
- color
