# -----------------------------------------------------------------------------
# parser.py - Analisador Sintático e Motor Semântico / Compilador
#
# Disciplina: Compiladores 2026_2 - Trabalho P2
# -----------------------------------------------------------------------------
import sys
import json
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from ply import yacc
from lexer import tokens

# =============================================================================
# ESTRUTURAÇÃO DA GRAMÁTICA SINTÁTICA (Regras de Produção LALR)
# =============================================================================

def p_conversation(p):
    '''conversation : node_list'''
    p[0] = {'type': 'conversation', 'nodes': p[1]}

def p_node_list(p):
    '''node_list : node_list node
                 | node'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_node(p):
    '''node : PHRASE COLON ID HEADER_DELIM body NODE_END'''
    p[0] = {
        'id': str(p[3]),
        'lines': p[5]['lines'],
        'choices': p[5]['choices'],
        'jump': p[5]['jump']
    }

def p_body(p):
    '''body : statement_list'''
    lines = []
    choices = []
    jump_target = None

    for item in p[1]:
        if item['type'] == 'line':
            lines.append(item)
        elif item['type'] == 'choice':
            choices.append(item)
        elif item['type'] == 'command':
            if item['action'] == 'jump':
                jump_target = item['target']
            elif item['action'] == 'stop':
                jump_target = 'exit'

    p[0] = {
        'lines': lines,
        'choices': choices,
        'jump': jump_target
    }

def p_statement_list(p):
    '''statement_list : statement_list statement
                      | statement'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_statement(p):
    '''statement : dialogue_line
                 | choice_statement
                 | command_statement'''
    p[0] = p[1]

# Linha de diálogo falada por um personagem
def p_dialogue_line(p):
    '''dialogue_line : SPEAKER text_sequence'''
    p[0] = {
        'type': 'line',
        'speaker': p[1],
        'text': p[2]
    }

# Escolha interativa com comando aninhado
def p_choice_statement(p):
    '''choice_statement : ARROW SPEAKER text_sequence command_statement
                         | ARROW text_sequence command_statement'''
    if len(p) == 5:
        speaker = p[2]
        text = p[3]
        cmd = p[4]
    else:
        speaker = None
        text = p[2]
        cmd = p[3]

    target = cmd['target'] if cmd['action'] == 'jump' else 'exit'
    p[0] = {
        'type': 'choice',
        'speaker': speaker,
        'text': text,
        'target': target
    }

# Comandos de fluxo: <<jump ID>> ou <<stop>>
def p_command_statement(p):
    '''command_statement : COMMAND_START JUMP ID COMMAND_END
                         | COMMAND_START STOP COMMAND_END'''
    if p[2].lower() == 'jump':
        p[0] = {'type': 'command', 'action': 'jump', 'target': str(p[3])}
    else:
        p[0] = {'type': 'command', 'action': 'stop'}

# Sequência de texto com suporte a palavras e tags de formatação
def p_text_sequence(p):
    '''text_sequence : text_sequence text_item
                     | text_item'''
    if len(p) == 3:
        p[0] = p[1] + " " + p[2]
    else:
        p[0] = p[1]

def p_text_item(p):
    '''text_item : TEXT
                 | ID
                 | MARKUP_OPEN
                 | MARKUP_CLOSE
                 | MARKUP_SELF'''
    val = p[1]
    # Se for markup, reconstrói a tag visual
    if p.slice[1].type == 'MARKUP_OPEN':
        p[0] = f"<{val}>"
    elif p.slice[1].type == 'MARKUP_CLOSE':
        tag_nome = val if val else ""
        p[0] = f"</{tag_nome}>"
    elif p.slice[1].type == 'MARKUP_SELF':
        p[0] = f"<{val}/>"
    else:
        p[0] = str(val)

def p_error(p):
    if p:
        print(f"Erro Sintático próximo ao token '{p.value}' (tipo: {p.type}) na linha {p.lineno}")
    else:
        print("Erro Sintático: fim inesperado do arquivo (EOF).")

parser = yacc.yacc()

# =============================================================================
# AÇÕES SEMÂNTICAS, VALIDAÇÃO E GERAÇÃO DO XML
# =============================================================================

def validar_semantica(ast):
    """Verifica nós duplicados e saltos (jump/target) para IDs inexistentes"""
    ids_existentes = set()
    for node in ast['nodes']:
        nid = node['id']
        if nid in ids_existentes:
            print(f"[Aviso Semântico] ID duplicado: phrase '{nid}'.")
        ids_existentes.add(nid)

    erros = 0
    for node in ast['nodes']:
        nid = node['id']
        # Valida jump direto
        if node['jump'] and node['jump'] != 'exit' and node['jump'] not in ids_existentes:
            print(f"[Erro Semântico] Na phrase '{nid}': salto para ID inexistente '{node['jump']}'!")
            erros += 1
        # Valida choices
        for ch in node['choices']:
            if ch['target'] != 'exit' and ch['target'] not in ids_existentes:
                print(f"[Erro Semântico] Na escolha da phrase '{nid}': destino inexistente '{ch['target']}'!")
                erros += 1

    if erros == 0:
        print("[Análise Semântica] Sucesso: Grafo de diálogos e saltos 100% íntegro!")
    return erros == 0

def compilar_para_xml(ast, arquivo_saida="dialogos.xml"):
    """Gera o arquivo XML idêntico ao formato exigido para o motor do jogo"""
    root = ET.Element("conversation")

    for node in ast['nodes']:
        dialog_attrs = {"id": node['id']}
        # Determina o falante principal do diálogo
        speaker = node['lines'][0]['speaker'] if node['lines'] else "Narrador"
        dialog_attrs["speaker"] = speaker
        if node['jump']:
            dialog_attrs["target"] = node['jump']

        dialog_el = ET.SubElement(root, "dialog", dialog_attrs)

        # Texto da fala
        text_content = "\n".join([line['text'] for line in node['lines']])
        text_el = ET.SubElement(dialog_el, "text")
        text_el.text = text_content

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

    # Formata com indentação bonita
    xml_str = ET.tostring(root, encoding="utf-8")
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="\t", encoding="utf-8").decode("utf-8")

    with open(arquivo_saida, "w", encoding="utf-8") as f:
        f.write(pretty_xml)
    print(f"[Compilador] XML gerado com sucesso: '{arquivo_saida}'")

    # Exporta também para visual/dialogos.js para que o index.html leia o script compilado automaticamente
    try:
        dados_json = {}
        for node in ast['nodes']:
            speaker = node['lines'][0]['speaker'] if node['lines'] else "Narrador"
            text_content = "\n".join([line['text'] for line in node['lines']])
            dados_json[node['id']] = {
                'speaker': speaker,
                'text': text_content,
                'choices': [{'speaker': ch['speaker'], 'text': ch['text'], 'target': ch['target']} for ch in node['choices']],
                'target': node['jump']
            }
        with open("visual/dialogos.js", "w", encoding="utf-8") as f_js:
            f_js.write("const roteiroJogo = " + json.dumps(dados_json, indent=4, ensure_ascii=False) + ";\n")
        print("[Compilador] Arquivo visual atualizado com sucesso: 'visual/dialogos.js'")
    except Exception as e:
        pass

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
    caminho_entrada = sys.argv[1] if len(sys.argv) > 1 else 'roteiro.dialogo'
    with open(caminho_entrada, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    print(f"Compilando roteiro '{caminho_entrada}'...")
    ast = parser.parse(conteudo)

    if ast:
        valido = validar_semantica(ast)
        if valido:
            compilar_para_xml(ast, "saida_dialogos.xml")
            if len(sys.argv) > 2 and sys.argv[2] == '--jogar':
                executar_jogo_terminal(ast)
            else:
                print("\nPara jogar interativamente no terminal, execute:")
                print(f"python parser.py {caminho_entrada} --jogar")
