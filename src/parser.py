# -----------------------------------------------------------------------------
# parser.py - Analisador Sintático, Análise Semântica e Geração de XML
# Disciplina: Compiladores 2026_2 - Trabalho P2
#
# Gerador utilizado: PLY (yacc.py). Ponto de partida: o exemplo "calc" do PLY.
#
# LEGENDA DAS MARCAÇÕES NO CÓDIGO
#   [ORIGINAL PLY] estrutura mantida do exemplo calc (funções p_..., p_error,
#                  yacc.yacc()).
#   [MODIFICADO]   parte que existia no exemplo calc mas foi alterada.
#   [NOVO]         parte criada para a DialogueDSL (não existe na calc).
# Os números [P1]...[P26] são as produções da tabela em docs/tabela_traducao.md
# e [S1]...[S12] são as regras semânticas.
#
# Diferença para a calc: a calc avalia expressões aritméticas e usa a tabela
# 'precedence' para resolver a ambiguidade de E -> E + E | E * E. Esta gramática
# não tem ambiguidade (o PLY gera a tabela LALR sem conflitos), por isso não
# há tabela de precedência; a recursão à esquerda das listas é a forma
# recomendada para LALR (pilha constante).
# -----------------------------------------------------------------------------
import os
import re
import sys
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from ply import yacc
from lexer import tokens, lexer, erros_lexicos  # noqa: F401  (tokens é exigido pelo PLY)

# =============================================================================
# [NOVO] REGISTRO DE ERROS E AVISOS
# Erros são acumulados (com linha e trecho do roteiro). Se houver algum, o
# compilador falha e NÃO gera o XML. Avisos são mostrados, mas não impedem.
# =============================================================================
class ErroCompilacao(Exception):
    """Erro fatal que interrompe a análise sintática."""

erros = []            # lista de dicts: {'tipo', 'linha', 'msg', 'dica'}
avisos = []           # lista de dicts: {'linha', 'msg'}
_fonte_linhas = []    # linhas do roteiro, usadas para mostrar o trecho com erro

def definir_fonte(texto):
    """Guarda o roteiro e zera o estado antes de uma nova compilação."""
    global _fonte_linhas
    _fonte_linhas = texto.splitlines()
    erros.clear()
    avisos.clear()
    erros_lexicos.clear()
    lexer.lineno = 1

def registrar_erro(tipo, linha, msg, dica=None):
    erros.append({'tipo': tipo, 'linha': linha, 'msg': msg, 'dica': dica})

def registrar_aviso(linha, msg):
    avisos.append({'linha': linha, 'msg': msg})

def coletar_erros_lexicos():
    """Traz os erros registrados pelo lexer para a mesma lista de erros."""
    for e in erros_lexicos:
        registrar_erro('Erro Léxico', e['linha'], e['msg'], e.get('dica'))
    erros_lexicos.clear()

def _mostrar_trecho(linha):
    if 1 <= linha <= len(_fonte_linhas):
        print(f"    {linha:>4} | {_fonte_linhas[linha - 1].rstrip()}")

def imprimir_avisos(arquivo):
    for a in sorted(avisos, key=lambda a: a['linha']):
        print(f"\n[Aviso Semântico] {arquivo}, linha {a['linha']}: {a['msg']}")
        _mostrar_trecho(a['linha'])

def imprimir_erros(arquivo):
    """Mostra cada erro com o arquivo, a linha e o trecho do roteiro."""
    for e in sorted(erros, key=lambda e: e['linha']):
        print(f"\n[{e['tipo']}] {arquivo}, linha {e['linha']}: {e['msg']}")
        _mostrar_trecho(e['linha'])
        if e['dica']:
            print(f"    Dica: {e['dica']}")
    print(f"\nCompilação interrompida: {len(erros)} erro(s). Nenhum XML foi gerado.")

# =============================================================================
# [NOVO] ATRIBUTOS DO TEXTO
# Cada pedaço de texto é uma string que também carrega atributos usados pela
# análise semântica: as linhas em que começa e termina, se havia espaço antes
# dele no roteiro e a lista de tags de efeito ([shake], [/shake], ...).
# =============================================================================
class Texto(str):
    linha_ini = 0
    linha_fim = 0
    espaco_antes = False
    marcas = ()

# [NOVO] Tags de efeito conhecidas pelo compilador e pela interface visual.
#   'par'  -> precisa de abertura e fechamento: [shake]...[/shake]
#   'auto' -> autocontida: [pause=500/]
TAGS = {
    'b':       {'forma': 'par',  'valor': None},
    'bold':    {'forma': 'par',  'valor': None},     # sinônimo de [b] (usado no prompt.md)
    'shake':   {'forma': 'par',  'valor': None},
    'bobbing': {'forma': 'par',  'valor': None},
    'wave':    {'forma': 'par',  'valor': None},     # sinônimo de [bobbing]
    'color':   {'forma': 'par',  'valor': 'cor'},
    'pause':   {'forma': 'auto', 'valor': 'inteiro'},
}
_COR_RE = re.compile(r'^(#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?([0-9a-fA-F]{2})?|[a-zA-Z]+)$')

def _lista_tags():
    return ', '.join(f'[{n}]' for n in TAGS if TAGS[n]['forma'] == 'par') + ', [pause=ms/]'

def _validar_valor(nome, valor, linha):
    """[S9] O valor da tag precisa combinar com o tipo esperado."""
    esperado = TAGS[nome]['valor']
    if esperado is None and valor is not None:
        registrar_erro('Erro Semântico', linha, f'a tag [{nome}] não aceita valor ("{valor}").')
    elif esperado == 'cor' and (valor is None or not _COR_RE.match(valor)):
        registrar_erro('Erro Semântico', linha, f'cor inválida em [{nome}={valor or ""}].',
                       'use uma cor hexadecimal, por exemplo [color=#f00] ou [color=#ffd700]')
    elif esperado == 'inteiro' and (valor is None or not valor.isdigit()):
        registrar_erro('Erro Semântico', linha, f'tempo inválido em [{nome}={valor or ""}/].',
                       'a pausa é em milissegundos, por exemplo [pause=500/]')

def validar_marcacoes(texto):
    """[NOVO] [S8]-[S10] Confere as tags de efeito de uma frase com uma pilha:
    tag desconhecida, valor inválido, tag fechada sem abrir, tags cruzadas e tag
    não fechada. Devolve o texto final, com cada [/] trocado pelo nome da tag
    que ele fecha (a interface visual precisa do nome)."""
    pilha = []           # tags abertas: (nome, linha)
    nomes_vazios = []    # nome resolvido de cada [/], na ordem em que aparecem
    for m in texto.marcas:
        nome, linha = m['nome'], m['linha']
        if m['tipo'] == 'fecha':
            if not nome:
                if not pilha:
                    registrar_erro('Erro Semântico', linha, '[/] sem nenhuma tag aberta para fechar.')
                    nomes_vazios.append('')
                    continue
                nome = pilha[-1][0]
                nomes_vazios.append(nome)
            if not pilha or all(n != nome for n, _ in pilha):
                registrar_erro('Erro Semântico', linha, f'[/{nome}] fecha uma tag que não foi aberta.')
                continue
            if pilha[-1][0] != nome:
                registrar_erro('Erro Semântico', linha,
                               f'tags cruzadas: [/{nome}] aparece antes de [/{pilha[-1][0]}].',
                               'feche as tags na ordem inversa da abertura: [a][b]...[/b][/a]')
            # remove só a tag fechada; as outras continuam abertas (evita erros em cascata)
            i = max(i for i, (n, _) in enumerate(pilha) if n == nome)
            del pilha[i]
            continue

        if nome not in TAGS:
            registrar_erro('Erro Semântico', linha, f'tag desconhecida [{nome}].',
                           f'efeitos disponíveis: {_lista_tags()}')
            if m['tipo'] == 'abre':
                pilha.append((nome, linha))   # o [/nome] correspondente não gera outro erro
            continue
        if m['tipo'] == 'auto':
            if TAGS[nome]['forma'] != 'auto':
                registrar_erro('Erro Semântico', linha, f'[{nome}/] não pode ser autocontida.',
                               f'use [{nome}]...[/{nome}]')
                continue
            _validar_valor(nome, m['valor'], linha)
        else:  # abre
            if TAGS[nome]['forma'] == 'auto':
                registrar_erro('Erro Semântico', linha, f'[{nome}] é autocontida e deve terminar com "/]".',
                               'escreva, por exemplo, [pause=500/]')
                continue
            _validar_valor(nome, m['valor'], linha)
            pilha.append((nome, linha))

    for nome, linha in pilha:
        if nome not in TAGS:
            continue  # tag desconhecida já foi acusada
        registrar_erro('Erro Semântico', linha, f'a tag [{nome}] foi aberta e não foi fechada.',
                       f'feche com [/{nome}] antes do fim da frase')

    final = str(texto)
    for nome in nomes_vazios:
        final = final.replace('</>', f'</{nome}>', 1)
    return final

def _verificar_falante(nome, linha):
    """[S7] Um nome de tag no início da linha é lido como personagem. Avisamos
    o autor, porque quase sempre faltou o [Personagem] antes do efeito."""
    if nome.lower() in TAGS:
        registrar_erro('Erro Semântico', linha,
                       f'[{nome}] está no lugar do identificador do personagem.',
                       f'escreva o personagem antes do efeito: [Personagem] [{nome}]...')

# =============================================================================
# [MODIFICADO] GRAMÁTICA (produções LALR) E AÇÕES SEMÂNTICAS
# Na calc as produções eram de expressões (expression : expression PLUS ...);
# todas as produções abaixo foram criadas para a DialogueDSL.
# =============================================================================

# [NOVO] [P1]
def p_conversation(p):
    '''conversation : node_list'''
    p[0] = {'type': 'conversation', 'nodes': p[1]}

# [NOVO] [P2] [P3]
def p_node_list(p):
    '''node_list : node_list node
                 | node'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

# [NOVO] [P4]
def p_node(p):
    '''node : PHRASE COLON ID HEADER_DELIM body NODE_END'''
    p[0] = {
        'id': str(p[3]),
        'linha': p.lineno(1),
        'lines': p[5]['lines'],
        'choices': p[5]['choices'],
        'jump': p[5]['jump'],
        'jump_linha': p[5]['jump_linha'],
    }

# [NOVO] [P5] + regras semânticas de estrutura do bloco [S1]-[S4]
def p_body(p):
    '''body : statement_list'''
    lines, choices, comandos = [], [], []

    for item in p[1]:
        if item['type'] == 'line':
            # [S2] As falas vêm antes das opções e do comando final
            if choices or comandos:
                registrar_erro('Erro Semântico', item['linha'],
                               'fala depois de uma opção ou de um comando de fluxo.',
                               'a ordem no bloco é: falas, depois opções (->) OU um <<jump ID>>/<<stop>>')
            # [S4] Um bloco tem um único personagem falando (o XML guarda um speaker por <dialog>)
            elif lines and item['speaker'] != lines[0]['speaker']:
                registrar_erro('Erro Semântico', item['linha'],
                               f"fala de '{item['speaker']}' dentro de um bloco de '{lines[0]['speaker']}'.",
                               'cada bloco tem um único personagem; crie outro phrase e ligue com <<jump ID>>')
            lines.append(item)
        elif item['type'] == 'choice':
            choices.append(item)
        else:
            comandos.append(item)

    # [S1] Todo bloco tem pelo menos uma fala
    if not lines:
        registrar_erro('Erro Semântico', p[1][0]['linha'],
                       'bloco sem fala de personagem.',
                       'todo bloco começa com  [Personagem] texto')

    # [S3] Cada bloco termina de um único jeito: opções OU um comando de fluxo
    if choices and comandos:
        registrar_erro('Erro Semântico', comandos[0]['linha'],
                       'bloco com opções não pode ter um <<jump>>/<<stop>> solto.',
                       'cada opção já tem o seu próprio comando; remova este')
    elif len(comandos) > 1:
        registrar_erro('Erro Semântico', comandos[1]['linha'],
                       'mais de um comando de fluxo no mesmo bloco.',
                       'use apenas um <<jump ID>> ou <<stop>> por bloco')
    elif not choices and not comandos:
        registrar_erro('Erro Semântico', p[1][-1]['linha'],
                       'bloco sem <<jump ID>> ou <<stop>>.',
                       'toda fala deve ser seguida de <<jump ID>> (próximo bloco) ou <<stop>> (fim)')

    jump_target = jump_linha = None
    if comandos and not choices:
        cmd = comandos[0]
        jump_target = cmd['target'] if cmd['action'] == 'jump' else 'exit'
        jump_linha = cmd['linha']

    p[0] = {
        'lines': lines,
        'choices': choices,
        'jump': jump_target,
        'jump_linha': jump_linha,
    }

# [NOVO] [P6] [P7]
def p_statement_list(p):
    '''statement_list : statement_list statement
                      | statement'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

# [NOVO] [P8] [P9] [P10]
def p_statement(p):
    '''statement : dialogue_line
                 | choice_statement
                 | command_statement'''
    p[0] = p[1]

# [NOVO] [P11] Linha de diálogo falada por um personagem
def p_dialogue_line(p):
    '''dialogue_line : SPEAKER text_sequence'''
    _verificar_falante(p[1], p.lineno(1))
    p[0] = {
        'type': 'line',
        'speaker': p[1],
        'text': validar_marcacoes(p[2]),
        'linha': p.lineno(1),
    }

# [NOVO] [P12] Escolha interativa: TODA opção começa com o identificador do personagem
#     -> [Personagem] texto da opção
#        <<jump destino>>
def p_choice_statement(p):
    '''choice_statement : ARROW SPEAKER text_sequence command_statement'''
    _verificar_falante(p[2], p.lineno(2))
    cmd = p[4]
    p[0] = {
        'type': 'choice',
        'speaker': p[2],
        'text': validar_marcacoes(p[3]),
        'target': cmd['target'] if cmd['action'] == 'jump' else 'exit',
        'linha': p.lineno(1),
        'linha_destino': cmd['linha'],
    }

# [NOVO] [P13] Opção SEM identificador: reconhecida pela gramática apenas para
# apontar a linha exata do erro [S6]; o compilador falha ao final da análise.
def p_choice_statement_sem_falante(p):
    '''choice_statement : ARROW text_sequence command_statement'''
    registrar_erro(
        'Erro Semântico', p.lineno(1),
        f'a opção "{p[2]}" não tem o identificador do personagem.',
        'toda opção deve ser escrita como  -> [Personagem] texto da opção')
    cmd = p[3]
    p[0] = {
        'type': 'choice',
        'speaker': None,
        'text': str(p[2]),
        'target': cmd['target'] if cmd['action'] == 'jump' else 'exit',
        'linha': p.lineno(1),
        'linha_destino': cmd['linha'],
    }

# [NOVO] [P14] [P15] Comandos de fluxo: <<jump ID>> ou <<stop>>
def p_command_statement(p):
    '''command_statement : COMMAND_START JUMP ID COMMAND_END
                         | COMMAND_START STOP COMMAND_END'''
    if len(p) == 5:
        p[0] = {'type': 'command', 'action': 'jump', 'target': str(p[3]), 'linha': p.lineno(1)}
    else:
        p[0] = {'type': 'command', 'action': 'stop', 'linha': p.lineno(1)}

# [NOVO] [P16] [P17] Sequência de texto
# O espaço entre dois pedaços vem do próprio roteiro (atributo espaco_antes):
# o lexer descarta os espaços, e o texto é remontado como foi escrito.
def p_text_sequence(p):
    '''text_sequence : text_sequence text_item
                     | text_item'''
    if len(p) == 3:
        # [S5] Uma frase que continua em outra linha do roteiro não tem identificador de personagem
        if p[2].linha_ini > p[1].linha_fim:
            registrar_erro(
                'Erro Semântico', p[2].linha_ini,
                'frase sem o identificador do personagem.',
                'toda frase deve começar com [Personagem]; para continuar a fala, repita o identificador')
        novo = Texto(p[1] + (' ' if p[2].espaco_antes else '') + p[2])
        novo.linha_ini = p[1].linha_ini
        novo.linha_fim = p[2].linha_fim
        novo.marcas = list(p[1].marcas) + list(p[2].marcas)
        p[0] = novo
    else:
        p[0] = p[1]

# [NOVO] [P18]-[P26] Um pedaço de texto.
# COLON, JUMP, STOP e PHRASE também são aceitos como texto, para que frases
# como "Atenção: pare!" ou "Não dê stop" compilem.
# A gramática continua sem conflitos: esses tokens só têm papel estrutural fora
# de text_sequence (no cabeçalho e dentro de << >>).
def p_text_item(p):
    '''text_item : TEXT
                 | ID
                 | COLON
                 | JUMP
                 | STOP
                 | PHRASE
                 | MARKUP_OPEN
                 | MARKUP_CLOSE
                 | MARKUP_SELF'''
    val = p[1]
    tipo = p.slice[1].type
    linha = p.lineno(1)
    marcas = []
    # Se for markup, reconstrói a tag visual e guarda a tag para a análise semântica
    if tipo in ('MARKUP_OPEN', 'MARKUP_SELF'):
        texto = f"<{val}>" if tipo == 'MARKUP_OPEN' else f"<{val}/>"
        nome, _, valor = val.partition('=')
        marcas.append({'tipo': 'abre' if tipo == 'MARKUP_OPEN' else 'auto',
                       'nome': nome.strip().lower(),
                       'valor': valor.strip() if _ else None,
                       'linha': linha})
    elif tipo == 'MARKUP_CLOSE':
        texto = f"</{val}>"
        marcas.append({'tipo': 'fecha', 'nome': val.lower(), 'valor': None, 'linha': linha})
    else:
        texto = str(val)
    item = Texto(texto)
    item.linha_ini = item.linha_fim = linha
    pos = p.lexpos(1)
    item.espaco_antes = pos > 0 and p.lexer.lexdata[pos - 1] in ' \t\r\n'
    item.marcas = marcas
    p[0] = item

_TIPOS_DE_TEXTO = ('TEXT', 'ID', 'MARKUP_OPEN', 'MARKUP_CLOSE', 'MARKUP_SELF')

# [NOVO] Dicas para o erro sintático, conforme o token inesperado
_DICAS_SINTATICAS = {
    'NODE_END': 'bloco vazio ou incompleto: cada opção (->) precisa de <<jump ID>> ou <<stop>>',
    'PHRASE': 'o bloco anterior terminou com ===?',
    'HEADER_DELIM': 'o cabeçalho deve ser  phrase: ID  seguido de ---',
    'SPEAKER': 'faltou --- após o cabeçalho, ou <<jump ID>>/<<stop>> depois da opção anterior?',
    'ARROW': 'a opção (->) deve vir dentro de um bloco, depois das falas',
    'COMMAND_END': 'comando incompleto: use <<jump ID>> ou <<stop>>',
    'COMMAND_START': 'comando fora de lugar: ele deve vir depois de uma fala ou opção',
    'COLON': 'o cabeçalho é  phrase: ID',
}

# [MODIFICADO] Na calc, p_error apenas imprimia "Syntax error". Aqui o erro é
# registrado com linha e dica, e a análise é interrompida.
def p_error(p):
    if p is None:
        registrar_erro('Erro Sintático', len(_fonte_linhas) or 1,
                       'fim inesperado do arquivo.',
                       'verifique se o último bloco termina com ===')
    else:
        if p.type in _TIPOS_DE_TEXTO:
            dica = 'falta o identificador do personagem, [Personagem], antes desta frase?'
        else:
            dica = _DICAS_SINTATICAS.get(p.type)
        registrar_erro('Erro Sintático', p.lineno,
                       f"token inesperado '{p.value}' (tipo {p.type}).", dica)
    raise ErroCompilacao()

# [ORIGINAL PLY] Constrói o analisador sintático (tabela LALR)
parser = yacc.yacc()

# =============================================================================
# [NOVO] ANÁLISE SEMÂNTICA DO GRAFO DE DIÁLOGOS
# =============================================================================

def validar_semantica(ast):
    """[S11] IDs de bloco únicos; [S12] todo jump/opção aponta para um bloco que
    existe; aviso para blocos que nunca são alcançados a partir do primeiro."""
    definidos = {}
    for node in ast['nodes']:
        nid = node['id']
        if nid in definidos:
            registrar_erro('Erro Semântico', node['linha'],
                           f"phrase '{nid}' já foi definida na linha {definidos[nid]}.",
                           'cada bloco precisa de um ID único')
        else:
            definidos[nid] = node['linha']

    for node in ast['nodes']:
        if node['jump'] and node['jump'] != 'exit' and node['jump'] not in definidos:
            registrar_erro('Erro Semântico', node['jump_linha'],
                           f"salto para a phrase '{node['jump']}', que não existe.")
        for ch in node['choices']:
            if ch['target'] != 'exit' and ch['target'] not in definidos:
                registrar_erro('Erro Semântico', ch['linha_destino'],
                               f"a opção aponta para a phrase '{ch['target']}', que não existe.")

    # Blocos inalcançáveis: busca em largura a partir do primeiro bloco
    if ast['nodes']:
        por_id = {}
        for node in ast['nodes']:
            por_id.setdefault(node['id'], node)
        alcancados = set()
        fila = [ast['nodes'][0]['id']]
        while fila:
            nid = fila.pop()
            if nid in alcancados or nid not in por_id:
                continue
            alcancados.add(nid)
            node = por_id[nid]
            fila.extend(ch['target'] for ch in node['choices'])
            if node['jump']:
                fila.append(node['jump'])
        for nid, node in por_id.items():
            if nid not in alcancados:
                registrar_aviso(node['linha'], f"a phrase '{nid}' nunca é alcançada a partir de '{ast['nodes'][0]['id']}'.")

    return not erros

# =============================================================================
# [NOVO] GERAÇÃO DE CÓDIGO: XML lido pela interface visual
# =============================================================================

def compilar_para_xml(ast, arquivo_saida="dialogos.xml"):
    """Gera o arquivo XML no formato lido pelo motor do jogo (visual/index.html)"""
    root = ET.Element("conversation")

    for node in ast['nodes']:
        dialog_attrs = {"id": node['id']}
        # [S4] garante que todas as falas do bloco são do mesmo personagem
        dialog_attrs["speaker"] = node['lines'][0]['speaker']
        if node['jump']:
            dialog_attrs["target"] = node['jump']

        dialog_el = ET.SubElement(root, "dialog", dialog_attrs)

        # Texto da fala
        text_el = ET.SubElement(dialog_el, "text")
        text_el.text = "\n".join(line['text'] for line in node['lines'])

        # Escolhas
        if node['choices']:
            choices_el = ET.SubElement(dialog_el, "choices")
            for ch in node['choices']:
                choice_attrs = {"target": ch['target']}
                if ch['speaker']:
                    choice_attrs["speaker"] = ch['speaker']
                choice_el = ET.SubElement(choices_el, "choice", choice_attrs)
                choice_text_el = ET.SubElement(choice_el, "text")
                choice_text_el.text = ch['text']

    # Formata com indentação
    xml_str = ET.tostring(root, encoding="utf-8")
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="\t", encoding="utf-8").decode("utf-8")

    with open(arquivo_saida, "w", encoding="utf-8") as f:
        f.write(pretty_xml)
    print(f"[Compilador] XML gerado com sucesso: '{arquivo_saida}'")

# [NOVO] Etapas do compilador reunidas em uma função (usada pelo main e pelos testes)
def compilar(conteudo):
    """Executa as análises léxica, sintática e semântica.
    Devolve a AST, ou None se houver erro (os erros ficam em 'erros')."""
    definir_fonte(conteudo)
    ast = None
    try:
        ast = parser.parse(conteudo, lexer=lexer)
    except ErroCompilacao:
        pass
    coletar_erros_lexicos()
    if ast and not erros:
        validar_semantica(ast)
    if not ast and not erros:
        registrar_erro('Erro Sintático', 1, 'o roteiro está vazio ou não pôde ser interpretado.')
    return None if erros else ast

# [NOVO] Servidor local para a interface visual (opção --visual)
def servir_visual(porta=8000):
    """Sobe um servidor HTTP local na raiz do projeto e abre a interface visual.
    A interface (visual/index.html) lê src/saida_dialogos.xml em tempo de execução."""
    import functools
    import http.server
    import os
    import socketserver
    import webbrowser

    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=raiz)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", porta), handler) as httpd:
        url = f"http://127.0.0.1:{porta}/visual/index.html"
        print(f"\n[Visual] Servindo em {url}  (Ctrl+C para encerrar)")
        print("[Visual] Edite o roteiro, recompile e clique em 'Reiniciar diálogo': o XML é relido.")
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[Visual] Servidor encerrado.")

# [NOVO] Execução do roteiro no terminal (opção --jogar)
def executar_jogo_terminal(ast):
    """Executa o roteiro interativo diretamente no terminal para demonstração"""
    nodes_map = {n['id']: n for n in ast['nodes']}
    current_id = ast['nodes'][0]['id'] if ast['nodes'] else None

    print("\n" + "=" * 65)
    print(" INICIANDO JOGO NARRATIVO INTERATIVO (DEMONSTRAÇÃO)")
    print("=" * 65)

    while current_id and current_id != 'exit':
        node = nodes_map.get(current_id)
        if not node:
            break

        print(f"\n--- [CENA {node['id']}] ---")
        for line in node['lines']:
            print(f"\n[{line['speaker']}]: {line['text']}")

        # Se tem escolhas
        if node['choices']:
            print("\nEscolha sua resposta:")
            for idx, ch in enumerate(node['choices'], 1):
                speaker_prefix = f"[{ch['speaker']}] " if ch['speaker'] else ""
                print(f"  {idx}) {speaker_prefix}{ch['text']}")

            escolha_valida = False
            while not escolha_valida:
                try:
                    escolha = input("\nDigite o número da sua escolha (ou 'sair'): ").strip()
                    if escolha.lower() in ('sair', 'exit'):
                        print("Jogo encerrado.")
                        return
                    opc_num = int(escolha)
                    if 1 <= opc_num <= len(node['choices']):
                        current_id = node['choices'][opc_num - 1]['target']
                        escolha_valida = True
                    else:
                        print("Opção inválida!")
                except ValueError:
                    print("Por favor, digite um número válido.")
        elif node['jump']:
            current_id = node['jump']
            input("\n[Pressione ENTER para continuar...]")
        else:
            break

    print("\n================== FIM DO DIÁLOGO ==================\n")

if __name__ == '__main__':
    pasta_src = os.path.dirname(os.path.abspath(__file__))
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = [a for a in sys.argv[1:] if a.startswith('--')]
    caminho_entrada = args[0] if args else os.path.join(pasta_src, 'roteiro.dialogo')
    with open(caminho_entrada, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    print(f"Compilando roteiro '{caminho_entrada}'...")
    ast = compilar(conteudo)
    nome_arquivo = os.path.basename(caminho_entrada)

    # Qualquer erro registrado (léxico, sintático ou semântico) faz o compilador falhar
    if ast is None:
        imprimir_erros(nome_arquivo)
        sys.exit(1)

    imprimir_avisos(nome_arquivo)
    print("[Análise Semântica] Sucesso: Grafo de diálogos e saltos 100% íntegro!")

    # O XML sempre fica em src/, onde a interface visual o procura
    compilar_para_xml(ast, os.path.join(pasta_src, "saida_dialogos.xml"))
    if '--jogar' in flags:
        executar_jogo_terminal(ast)
    elif '--visual' in flags:
        servir_visual()
    else:
        print("\nPara jogar no terminal:  python parser.py roteiro.dialogo --jogar")
        print("Para abrir a interface visual:  python parser.py roteiro.dialogo --visual")
