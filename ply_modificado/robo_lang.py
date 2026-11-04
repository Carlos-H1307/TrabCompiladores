# -----------------------------------------------------------------------------
# robo_lang.py - DSL de Controle de Robô / Desenho Turtle
#
# Trabalho de Compiladores (P2 - Parte 2)
# Modificações realizadas em relação ao calc.py original do PLY:
# 1. Modificação Léxica: Remoção de regras aritméticas puras de calculadora e 
#    inclusão de palavras reservadas (FORWARD, BACKWARD, LEFT, RIGHT, PENUP, 
#    PENDOWN, REPEAT, COLOR, PRINT, RESET), identificadores, strings e delimitadores.
# 2. Modificação Sintática: Estruturação de gramática para listas de instruções,
#    blocos de repetição aninhados ({ ... }), comandos de estado e expressões.
# 3. Ações Semânticas: Tradução dirigida pela sintaxe para manipulação do estado
#    de um Robô virtual (posição x, y, ângulo, estado da caneta, cor e histórico).
# -----------------------------------------------------------------------------

import math
import sys
import turtle
import ply.lex as lex
import ply.yacc as yacc

# Mapeamento de cores em português para inglês (para o Turtle)
CORES_MAP = {
    'PRETO': 'black',
    'AZUL': 'blue',
    'VERMELHO': 'red',
    'VERDE': 'green',
    'AMARELO': 'yellow',
    'LARANJA': 'orange',
    'ROXO': 'purple',
    'BRANCO': 'white',
    'CINZA': 'gray',
}

# =============================================================================
# ESTADO DO ROBÔ VIRTUAL (Código de Usuário / Ambiente Semântico)
# =============================================================================
class RoboVirtual:
    def __init__(self):
        self.tela_inicializada = False
        self.t = None
        self.reset()

    def _garantir_janela(self):
        """Inicializa a janela gráfica do turtle apenas quando necessário"""
        if not self.tela_inicializada:
            try:
                turtle.setup(width=800, height=600)
                turtle.title("Visualizador Gráfico - Robô Virtual (DSL)")
                self.t = turtle.Turtle()
                self.t.shape("turtle")
                self.t.speed(3)
                self.tela_inicializada = True
            except Exception:
                self.t = None

    def reset(self):
        self.x = 0.0
        self.y = 0.0
        self.angulo = 90.0  # Apontando para o norte
        self.caneta_abaixada = True
        self.cor = "PRETO"
        self.trilha = [(0.0, 0.0)]
        self.variaveis = {}
        
        self._garantir_janela()
        if self.t:
            self.t.reset()
            self.t.shape("turtle")
            self.t.speed(3)
            self.t.setheading(90)
            self.t.color("black")
            self.t.pendown()

        print("[Robô] Inicializado na posição (0.00, 0.00), ângulo 90° (Norte), caneta ABAIXADA.")

    def mover(self, distancia):
        self._garantir_janela()
        rad = math.radians(self.angulo)
        novo_x = self.x + distancia * math.cos(rad)
        novo_y = self.y + distancia * math.sin(rad)
        
        status_desenho = f"desenhando com cor {self.cor}" if self.caneta_abaixada else "sem desenhar"
        print(f"[Robô] Moveu {distancia:.2f} unidades de ({self.x:.2f}, {self.y:.2f}) para ({novo_x:.2f}, {novo_y:.2f}) [{status_desenho}].")
        
        if self.t:
            if distancia >= 0:
                self.t.forward(distancia)
            else:
                self.t.backward(abs(distancia))

        self.x = novo_x
        self.y = novo_y
        if self.caneta_abaixada:
            self.trilha.append((self.x, self.y))

    def girar(self, angulo_graus):
        self._garantir_janela()
        self.angulo = (self.angulo + angulo_graus) % 360.0
        print(f"[Robô] Girou {angulo_graus:.2f}°. Novo ângulo: {self.angulo:.2f}°.")
        if self.t:
            if angulo_graus >= 0:
                self.t.left(angulo_graus)
            else:
                self.t.right(abs(angulo_graus))

    def levantar_caneta(self):
        self._garantir_janela()
        self.caneta_abaixada = False
        if self.t:
            self.t.penup()
        print("[Robô] Caneta LEVANTADA (movimentos sem desenhar).")

    def abaixar_caneta(self):
        self._garantir_janela()
        self.caneta_abaixada = True
        if self.t:
            self.t.pendown()
        print("[Robô] Caneta ABAIXADA (desenhando).")

    def mudar_cor(self, nova_cor):
        self._garantir_janela()
        self.cor = str(nova_cor).upper()
        cor_ingles = CORES_MAP.get(self.cor, self.cor.lower())
        if self.t:
            try:
                self.t.color(cor_ingles)
            except Exception:
                pass
        print(f"[Robô] Cor alterada para: {self.cor}")

    def status(self):
        estado_caneta = "ABAIXADA (desenhando)" if self.caneta_abaixada else "LEVANTADA (livre)"
        print(f"[Robô Status] Pos: ({self.x:.2f}, {self.y:.2f}) | Ângulo: {self.angulo:.2f}° | Caneta: {estado_caneta} | Cor: {self.cor}")

robo = RoboVirtual()

# =============================================================================
# 1. ANÁLISE LÉXICA (Lexer)
# Expressões regulares e palavras reservadas
# =============================================================================

# Palavras reservadas da linguagem
reserved = {
    'frente': 'FORWARD',
    'tras': 'BACKWARD',
    'esquerda': 'LEFT',
    'direita': 'RIGHT',
    'levantar': 'PENUP',
    'abaixar': 'PENDOWN',
    'repetir': 'REPEAT',
    'cor': 'COLOR',
    'status': 'STATUS',
    'reset': 'RESET',
    'print': 'PRINT',
}

# Lista de tokens
tokens = [
    'NUMBER',
    'STRING',
    'NAME',
    'EQUALS',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'LPAREN',
    'RPAREN',
    'LBRACE',
    'RBRACE',
    'SEMI',
] + list(reserved.values())

# Tokens simples (operadores e delimitadores)
t_EQUALS = r'='
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_SEMI = r';'

# Expressão regular para strings literais entre aspas
def t_STRING(t):
    r'\"([^\\\n]|(\\.))*?\"'
    t.value = t.value[1:-1]  # remove as aspas
    return t

# Expressão regular para identificadores e detecção de palavras reservadas
def t_NAME(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value.lower(), 'NAME')
    return t

# Expressão regular para números inteiros ou com ponto flutuante
def t_NUMBER(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value)
    return t

# Ignorar espaços em branco e tabulações
t_ignore = ' \t'

# Linhas de comentários no formato //
def t_COMMENT(t):
    r'//.*'
    pass

# Rastreamento de número de linhas
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Tratamento de erro léxico
def t_error(t):
    print(f"Erro Léxico: caractere ilegal '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1)

# Constrói o analisador léxico
lexer = lex.lex()

# =============================================================================
# 2. ANÁLISE SINTÁTICA E AÇÕES SEMÂNTICAS (Parser & Semântica)
# Gramática livre de contexto com Tradução Dirigida pela Sintaxe
# =============================================================================

# Regras de precedência de operadores aritméticos para expressões
precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'UMINUS'),
)

# Programa é uma sequência de instruções
def p_program(p):
    '''program : statement_list
               | empty'''
    p[0] = p[1]

def p_statement_list(p):
    '''statement_list : statement_list statement
                      | statement'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]] if p[1] else [p[2]]
    else:
        p[0] = [p[1]] if p[1] else []

# Declaração dos comandos disponíveis na DSL
def p_statement_assign(p):
    '''statement : NAME EQUALS expression SEMI'''
    nome_var = p[1]
    valor = p[3]
    robo.variaveis[nome_var] = valor
    p[0] = ('assign', nome_var, valor)

def p_statement_forward(p):
    '''statement : FORWARD expression SEMI'''
    distancia = p[2]
    robo.mover(distancia)
    p[0] = ('forward', distancia)

def p_statement_backward(p):
    '''statement : BACKWARD expression SEMI'''
    distancia = p[2]
    robo.mover(-distancia)
    p[0] = ('backward', distancia)

def p_statement_left(p):
    '''statement : LEFT expression SEMI'''
    angulo = p[2]
    robo.girar(angulo)
    p[0] = ('left', angulo)

def p_statement_right(p):
    '''statement : RIGHT expression SEMI'''
    angulo = p[2]
    robo.girar(-angulo)
    p[0] = ('right', angulo)

def p_statement_penup(p):
    '''statement : PENUP SEMI'''
    robo.levantar_caneta()
    p[0] = ('penup',)

def p_statement_pendown(p):
    '''statement : PENDOWN SEMI'''
    robo.abaixar_caneta()
    p[0] = ('pendown',)

def p_statement_color(p):
    '''statement : COLOR STRING SEMI
                 | COLOR NAME SEMI'''
    robo.mudar_cor(p[2])
    p[0] = ('color', str(p[2]).upper())

def p_statement_status(p):
    '''statement : STATUS SEMI'''
    robo.status()
    p[0] = ('status',)

def p_statement_reset(p):
    '''statement : RESET SEMI'''
    robo.reset()
    p[0] = ('reset',)

def p_statement_print(p):
    '''statement : PRINT expression SEMI
                 | PRINT STRING SEMI'''
    print(f"[Saída PRINT]: {p[2]}")
    p[0] = ('print', p[2])

# Comando de repetição com bloco de comandos entre chaves { ... }
def p_statement_repeat(p):
    '''statement : REPEAT expression LBRACE statement_list RBRACE'''
    vezes = int(p[2])
    # A lista de comandos do bloco é reexecutada (ou avaliada)
    print(f">> Iniciando repetição de {vezes} vezes:")
    # Como as ações imediatas executaram na primeira passada do bloco durante a redução,
    # as iterações restantes (vezes - 1) são reprocessadas semanticamente:
    comandos_bloco = p[4]
    for i in range(1, max(1, vezes)):
        for cmd in comandos_bloco:
            _executar_comando_ast(cmd)
    print(f">> Fim da repetição ({vezes} vezes concluídas).")
    p[0] = ('repeat', vezes, comandos_bloco)

def _executar_comando_ast(cmd):
    """Execução semântica auxiliar para blocos repetidos"""
    if not cmd:
        return
    tipo = cmd[0]
    if tipo == 'forward':
        robo.mover(cmd[1])
    elif tipo == 'backward':
        robo.mover(-cmd[1])
    elif tipo == 'left':
        robo.girar(cmd[1])
    elif tipo == 'right':
        robo.girar(-cmd[1])
    elif tipo == 'penup':
        robo.levantar_caneta()
    elif tipo == 'pendown':
        robo.abaixar_caneta()
    elif tipo == 'color':
        robo.mudar_cor(cmd[1])
    elif tipo == 'print':
        print(f"[Saída PRINT]: {cmd[1]}")

# Avaliação semântica de expressões aritméticas
def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression'''
    if p[2] == '+':
        p[0] = p[1] + p[3]
    elif p[2] == '-':
        p[0] = p[1] - p[3]
    elif p[2] == '*':
        p[0] = p[1] * p[3]
    elif p[2] == '/':
        if p[3] == 0:
            print("Erro Semântico: Divisão por zero!")
            p[0] = 0
        else:
            p[0] = p[1] / p[3]

def p_expression_uminus(p):
    '''expression : MINUS expression %prec UMINUS'''
    p[0] = -p[2]

def p_expression_group(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = p[2]

def p_expression_number(p):
    '''expression : NUMBER'''
    p[0] = p[1]

def p_expression_name(p):
    '''expression : NAME'''
    try:
        p[0] = robo.variaveis[p[1]]
    except KeyError:
        print(f"Erro Semântico: Variável '{p[1]}' não definida.")
        p[0] = 0

def p_empty(p):
    '''empty :'''
    p[0] = []

def p_error(p):
    if p:
        print(f"Erro Sintático próximo ao token '{p.value}' (tipo: {p.type}) na linha {p.lineno}")
    else:
        print("Erro Sintático no final do arquivo (EOF inesperado)")

# Constrói o analisador sintático LALR
parser = yacc.yacc()

# =============================================================================
# MODO DE EXECUÇÃO
# =============================================================================
def executar_codigo(codigo):
    print("\n" + "="*60)
    print("EXECUTANDO CÓDIGO FONTE:")
    print("="*60)
    print(codigo.strip())
    print("-" * 60)
    print("EXECUÇÃO / ANÁLISE:")
    print("-" * 60)
    parser.parse(codigo)
    print("="*60 + "\n")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Modo arquivo: lê o arquivo passado como argumento
        caminho_arquivo = sys.argv[1]
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        executar_codigo(conteudo)
        
        # Mantém a janela gráfica aberta até o usuário clicar nela ou fechar
        if robo.tela_inicializada:
            print("\n[Visualização Gráfica] Desenho concluído! Clique na janela para fechar.")
            try:
                turtle.done()
            except Exception:
                pass
    else:
        # Modo interativo (REPL)
        print("DSL do Robô Virtual (Digite 'sair' ou Ctrl+C para encerrar)")
        robo.status()
        while True:
            try:
                s = input('robo > ')
            except EOFError:
                break
            if not s:
                continue
            if s.strip().lower() in ('sair', 'exit', 'quit'):
                break
            parser.parse(s)

