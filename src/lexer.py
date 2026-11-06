# -----------------------------------------------------------------------------
# lexer.py - Analisador Léxico para DialogueDSL (Yarn Spinner com [Speaker])
# Disciplina: Compiladores 2026_2 - Trabalho P2
# -----------------------------------------------------------------------------
from ply import lex

# Palavras reservadas para controle de fluxo e cabeçalhos
reserved = {
    'phrase': 'PHRASE',
    'jump': 'JUMP',
    'stop': 'STOP',
}

# Lista obrigatória de tokens para o PLY
tokens = (
    *reserved.values(),
    'HEADER_DELIM',    # --- (início do corpo da frase/cena)
    'NODE_END',        # === (fim da frase/cena)
    'COMMAND_START',   # <<
    'COMMAND_END',     # >>
    'ARROW',           # -> (opção de escolha)
    'COLON',           # : (após a palavra phrase)
    'SPEAKER',         # [Nome do Personagem] no início da fala ou escolha
    'MARKUP_OPEN',     # [tag] ou [tag=valor] (ex: [shake], [color=#f00])
    'MARKUP_CLOSE',    # [/tag] ou [/] (ex: [/shake], [/color])
    'MARKUP_SELF',     # [pause=500/]
    'ID',              # Identificador da cena (ex: 001, taverna)
    'TEXT',            # Texto falado, pontuação e palavras normais
)

# No PLY, funções são avaliadas antes de variáveis simples (t_...).
# Definimos NODE_END e HEADER_DELIM como funções para garantir que
# '===' e '---' nunca sejam consumidos pela regra t_TEXT.
def t_NODE_END(t):
    r'==='
    return t

def t_HEADER_DELIM(t):
    r'---'
    return t

def t_COMMAND_START(t):
    r'<<'
    return t

def t_COMMAND_END(t):
    r'>>'
    return t

def t_ARROW(t):
    r'->'
    return t

t_COLON = r':'

# Falante entre colchetes no início de falas ou escolhas: [Rato Mafioso], [Dogpoch]
# Deve começar com letra ou underscore e conter palavras normais
def t_SPEAKER(t):
    r'\[[a-zA-ZÀ-ÿ_][a-zA-ZÀ-ÿ0-9_ ]*\](?=\s+[^\/\]])'
    # Remove os colchetes externos e guarda o nome limpo do personagem
    t.value = t.value[1:-1].strip()
    return t

# Tags de Markup estilo Yarn / Text Animator
def t_MARKUP_CLOSE(t):
    r'\[\/[a-zA-Z0-9_]*\]'
    t.value = t.value[2:-1].strip()
    return t

def t_MARKUP_SELF(t):
    r'\[[a-zA-Z0-9_]+(=[^\]\/]+)?\/\]'
    t.value = t.value[1:-2].strip()
    return t

def t_MARKUP_OPEN(t):
    r'\[[a-zA-Z0-9_]+(=[^\]]+)?\]'
    t.value = t.value[1:-1].strip()
    return t

# Comentários de linha estilo //
def t_COMMENT(t):
    r'//.*'
    pass  # Ignora comentários durante o parsing

# Identificadores de nós/cenas ou comandos (ex: 001, inicio, jump, stop, phrase)
def t_ID(t):
    r'[a-zA-ZÀ-ÿ_0-9]+'
    val_lower = t.value.lower()
    if val_lower in reserved:
        t.type = reserved[val_lower]
    return t

# Texto livre: qualquer caractere que não seja delimitador estrutural especial (=, -, :, [, ], <, >, etc.)
def t_TEXT(t):
    r'[^ \t\n\[\]<>\-:=]+'
    return t

# Rastreamento de linhas
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Ignora espaços e tabs comuns entre tokens
t_ignore = ' \t\r'

# Tratamento de erros léxicos
def t_error(t):
    print(f"Erro Léxico: caractere inválido '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1)

# Constrói o analisador léxico
lexer = lex.lex()

if __name__ == '__main__':
    with open('roteiro.dialogo', 'r', encoding='utf-8') as f:
        dados = f.read()
    lexer.input(dados)
    print("Tokens gerados pelo Lexer:")
    print("=" * 60)
    for tok in lexer:
        print(f"Linha {tok.lineno:2d} | Tipo: {tok.type:<15} | Valor: {tok.value!r}")
