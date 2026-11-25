# -----------------------------------------------------------------------------
# rodar_testes.py - Testes do compilador DialogueDSL
#
# Cada arquivo em testes/casos/ começa com uma linha que diz o resultado esperado:
#   // espera: erro | trecho da mensagem de erro
#   // espera: ok | texto da primeira fala no XML
#   // espera: ok aviso | texto da primeira fala (e pelo menos um aviso)
# Os roteiros de exemplo de src/ também são compilados e devem passar.
#
# Uso (a partir da raiz do projeto):  python testes/rodar_testes.py
# -----------------------------------------------------------------------------
import glob
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'src'))

import parser as compilador  # noqa: E402  (src/parser.py)


def ler(caminho):
    with open(caminho, encoding='utf-8') as f:
        return f.read()


def rodar_caso(caminho):
    conteudo = ler(caminho)
    cabecalho = conteudo.splitlines()[0]
    if not cabecalho.startswith('// espera:'):
        return False, 'primeira linha sem "// espera:"'
    resultado, _, esperado = cabecalho[len('// espera:'):].partition('|')
    resultado, esperado = resultado.strip(), esperado.strip()

    ast = compilador.compilar(conteudo)
    mensagens = [e['msg'] for e in compilador.erros]

    if resultado == 'erro':
        if ast is not None:
            return False, 'compilou, mas deveria falhar'
        if not any(esperado in m for m in mensagens):
            return False, f'erro esperado "{esperado}", obtido {mensagens}'
        return True, mensagens[0] if len(mensagens) == 1 else f'{mensagens}'

    if ast is None:
        return False, f'deveria compilar, mas falhou: {mensagens}'
    texto = ast['nodes'][0]['lines'][0]['text']
    if texto != esperado:
        return False, f'texto esperado {esperado!r}, obtido {texto!r}'
    if resultado == 'ok aviso' and not compilador.avisos:
        return False, 'esperava pelo menos um aviso'
    return True, texto


def main():
    casos = sorted(glob.glob(os.path.join(RAIZ, 'testes', 'casos', '*.dialogo')))
    falhas = 0
    for caminho in casos:
        ok, detalhe = rodar_caso(caminho)
        falhas += not ok
        print(f"{'PASSOU' if ok else 'FALHOU'}  {os.path.basename(caminho):<32} {detalhe}")

    for nome in ('roteiro.dialogo', 'roteiro_passaros.dialogo'):
        ast = compilador.compilar(ler(os.path.join(RAIZ, 'src', nome)))
        ok = ast is not None
        falhas += not ok
        print(f"{'PASSOU' if ok else 'FALHOU'}  {nome:<32} {len(ast['nodes']) if ok else compilador.erros} blocos")

    total = len(casos) + 2
    print(f"\n{total - falhas}/{total} testes passaram.")
    sys.exit(1 if falhas else 0)


if __name__ == '__main__':
    main()
