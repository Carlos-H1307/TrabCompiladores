# -----------------------------------------------------------------------------
# lexer.py - Analisador Léxico para DialogueDSL (Yarn Spinner com [Speaker])
# Disciplina: Compiladores 2026_2 - Trabalho P2
#
# Gerador utilizado: PLY (Python Lex-Yacc). Ponto de partida: o exemplo
# "calc" que acompanha o PLY (ply/example/calc/calc.py).
#
# LEGENDA DAS MARCAÇÕES NO CÓDIGO
#   [ORIGINAL PLY] estrutura mantida do exemplo calc (lista de tokens,
#                  t_ignore, t_newline, t_error, lex.lex()).
#   [MODIFICADO]   parte que existia no exemplo calc mas foi alterada.
#   [NOVO]         parte criada para a DialogueDSL (não existe na calc).
# Os números [L1]...[L13] são as regras léxicas citadas em docs/tabela_traducao.md.
# -----------------------------------------------------------------------------
from ply import lex

# [NOVO] Palavras reservadas para controle de fluxo e cabeçalhos.
# 'dialog_node' é sinônimo de 'phrase' (forma usada no prompt.md).
reserved = {
    'phrase': 'PHRASE',
    'dialog_node': 'PHRASE',
    'jump': 'JUMP',
    'stop': 'STOP',
}

# [MODIFICADO] Lista de tokens: a calc tinha NAME, NUMBER e operadores aritméticos;
# aqui ficam apenas os tokens da linguagem de diálogos.
tokens = (
    'PHRASE', 'JUMP', 'STOP',
    'HEADER_DELIM',    # --- (início do corpo da frase/cena)
    'NODE_END',        # === (fim da frase/cena)
    'COMMAND_START',   # <<
    'COMMAND_END',     # >>
    'ARROW',           # -> (opção de escolha)
    'COLON',           # : (após a palavra phrase; também aceito dentro do texto)
    'SPEAKER',         # [Nome do Personagem] no início da fala ou escolha
    'MARKUP_OPEN',     # [tag] ou [tag=valor] (ex: [shake], [color=#f00])
    'MARKUP_CLOSE',    # [/tag] ou [/] (ex: [/shake], [/color])
    'MARKUP_SELF',     # [pause=500/]
    'ID',              # Identificador da cena (ex: 001, taverna) ou palavra
    'TEXT',            # Pontuação e demais caracteres do texto falado
)

# [NOVO] Erros léxicos acumulados. O parser os lê e, se houver algum,
# a compilação falha (antes o caractere inválido era só descartado).
erros_lexicos = []

# No PLY, regras definidas como função são testadas na ordem em que aparecem,
# antes das regras definidas como string. Por isso '===', '---', '<<', '>>' e '->'
# vêm primeiro: assim nunca são consumidos pela regra t_TEXT.

# [NOVO] [L1]
def t_NODE_END(t):
    r'==='
    return t

# [NOVO] [L2]
def t_HEADER_DELIM(t):
    r'---'
    return t

# [NOVO] [L3]
def t_COMMAND_START(t):
    r'<<'
    return t

# [NOVO] [L4]
def t_COMMAND_END(t):
    r'>>'
    return t

# [NOVO] [L5]
def t_ARROW(t):
    r'->'
    return t

# [NOVO] [L6]
t_COLON = r':'

# [NOVO] [L7] Falante entre colchetes: [Rato], [Dona Jandira].
# O falante só é reconhecido no INÍCIO da linha (ou logo após "->").
# Em qualquer outra posição o mesmo lexema é uma tag de abertura (MARKUP_OPEN):
# assim "[b] Gato" no meio da frase é negrito, e não um personagem chamado "b".
def t_SPEAKER(t):
    r'\[[a-zA-ZÀ-ÿ_][a-zA-ZÀ-ÿ0-9_ ]*\]'
    dados = t.lexer.lexdata
    inicio_linha = dados.rfind('\n', 0, t.lexpos) + 1
    antes = dados[inicio_linha:t.lexpos].strip()
    t.value = t.value[1:-1].strip()
    if antes not in ('', '->'):
        t.type = 'MARKUP_OPEN'
    return t

# [NOVO] [L8] Tags de fechamento: [/shake], [/color] ou [/] (fecha a última aberta)
def t_MARKUP_CLOSE(t):
    r'\[\/[a-zA-Z0-9_]*\]'
    t.value = t.value[2:-1].strip()
    return t

# [NOVO] [L9] Tags autocontidas: [pause=500/]
def t_MARKUP_SELF(t):
    r'\[[a-zA-Z0-9_]+(=[^\]\/]+)?\/\]'
    t.value = t.value[1:-2].strip()
    return t

# [NOVO] [L10] Tags de abertura com valor opcional: [shake], [color=#f00]
def t_MARKUP_OPEN(t):
    r'\[[a-zA-Z0-9_]+(=[^\]]+)?\]'
    t.value = t.value[1:-1].strip()
    return t

# [NOVO] [L11] Comentários de linha estilo //
def t_COMMENT(t):
    r'//.*'
    pass  # Ignora comentários durante o parsing

# [MODIFICADO] [L12] Na calc existia t_NAME; aqui o ID também identifica
# palavras reservadas (sem diferenciar maiúsculas de minúsculas).
def t_ID(t):
    r'[a-zA-ZÀ-ÿ_0-9]+'
    val_lower = t.value.lower()
    if val_lower in reserved:
        t.type = reserved[val_lower]
    return t

# [NOVO] [L13] Texto livre: pontuação e símbolos da fala.
# '-', '=' e '/' são aceitos no texto ("bem-vindo", "2 = 2", "e/ou"), desde que não
# formem os delimitadores estruturais '->', '---', '===' nem o comentário '//'.
# '<' e '>' continuam proibidos: no XML gerado eles marcam efeitos visuais, e
# aceitá-los permitiria escrever "<b>" direto no texto, sem passar pela validação.
def t_TEXT(t):
    r'(?:[^\s\[\]<>\-=:/]|-(?!>|--)|=(?!==)|/(?!/))+'
    return t

# [ORIGINAL PLY] Rastreamento de linhas (igual à calc)
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# [ORIGINAL PLY] Ignora espaços e tabs entre tokens ('\r' adicionado para arquivos do Windows)
t_ignore = ' \t\r'

# [MODIFICADO] Tratamento de erros léxicos: além de pular o caractere (como na calc),
# o erro é registrado com a linha para que a compilação falhe.
def t_error(t):
    c = t.value[0]
    dica = None
    if c in '<>':
        dica = "'<' e '>' são reservados para comandos (<<jump ID>>, <<stop>>)."
    elif c in '[]':
        dica = "colchete sem par: personagens e efeitos são escritos como [Nome] ou [tag]...[/tag]."
    erros_lexicos.append({
        'linha': t.lexer.lineno,
        'msg': f"caractere inválido '{c}'.",
        'dica': dica,
    })
    t.lexer.skip(1)

# [ORIGINAL PLY] Constrói o analisador léxico
lexer = lex.lex()

if __name__ == '__main__':
    import sys
    arquivo = sys.argv[1] if len(sys.argv) > 1 else 'roteiro.dialogo'
    with open(arquivo, 'r', encoding='utf-8') as f:
        dados = f.read()
    lexer.input(dados)
    print("Tokens gerados pelo Lexer:")
    print("=" * 60)
    for tok in lexer:
        print(f"Linha {tok.lineno:2d} | Tipo: {tok.type:<15} | Valor: {tok.value!r}")
    for e in erros_lexicos:
        print(f"[Erro Léxico] linha {e['linha']}: {e['msg']}")
