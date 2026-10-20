import argparse
import sys

DIRECOES = {"R": 1, "L": -1, "S": 0}

class Fita:

    def __init__(self, entrada, branco):
        self.branco = branco
        self.celulas = {i: s for i, s in enumerate(entrada)}
        self.cabeca = 0
        self.min_pos = 0
        self.max_pos = max(len(entrada) - 1, 0)

    def ler(self):
        return self.celulas.get(self.cabeca, self.branco)

    def escrever(self, simbolo):
        if simbolo == self.branco:
            self.celulas.pop(self.cabeca, None)
        else:
            self.celulas[self.cabeca] = simbolo

    def mover(self, delta):
        self.cabeca += delta
        self.min_pos = min(self.min_pos, self.cabeca)
        self.max_pos = max(self.max_pos, self.cabeca)

    def conteudo(self):
        if not self.celulas:
            return ""
        ini, fim = min(self.celulas), max(self.celulas)
        return "".join(self.celulas.get(i, self.branco) for i in range(ini, fim + 1))

    def formatar(self):
        ini = min(self.min_pos, min(self.celulas, default=0)) - 1
        fim = max(self.max_pos, max(self.celulas, default=0)) + 1
        partes = []
        for i in range(ini, fim + 1):
            s = self.celulas.get(i, self.branco)
            partes.append(f"[{s}]" if i == self.cabeca else f" {s} ")
        return "".join(partes)

class MaquinaDeTuring:
    def __init__(self, estados, alf_entrada, alf_fita, branco, inicial, finais, regras):
        self.estados = estados
        self.alf_entrada = alf_entrada
        self.alf_fita = alf_fita
        self.branco = branco
        self.inicial = inicial
        self.finais = finais
        self.regras = regras

    @staticmethod
    def carregar(caminho):
        try:
            with open(caminho, encoding="utf-8") as f:
                linhas = f.readlines()
        except OSError as e:
            raise ValueError(f"Nao foi possivel abrir '{caminho}': {e}")

        uteis = []
        for n, bruta in enumerate(linhas, 1):
            texto = bruta.split(";", 1)[0].strip()
            if texto:
                uteis.append((n, texto))

        if len(uteis) < 6:
            raise ValueError("Arquivo incompleto: faltam secoes (estados, alfabetos, "
                             "branco, estado inicial, estados finais).")

        def lista(texto):
            return [x.strip() for x in texto.split(",") if x.strip()]

        estados = lista(uteis[0][1])
        alf_entrada = lista(uteis[1][1])
        alf_fita = lista(uteis[2][1])
        branco = uteis[3][1].strip()
        inicial = uteis[4][1].strip()
        finais = set(lista(uteis[5][1]))

        if branco not in alf_fita:
            raise ValueError(f"Linha {uteis[3][0]}: o branco '{branco}' nao esta no alfabeto da fita.")
        if inicial not in estados:
            raise ValueError(f"Linha {uteis[4][0]}: estado inicial '{inicial}' nao esta na lista de estados.")
        for q in finais:
            if q not in estados:
                raise ValueError(f"Linha {uteis[5][0]}: estado final '{q}' nao esta na lista de estados.")
        for s in alf_entrada:
            if s not in alf_fita:
                raise ValueError(f"Simbolo de entrada '{s}' nao esta no alfabeto da fita.")

        regras = {}
        for n, texto in uteis[6:]:
            campos = [c.strip() for c in texto.split(",")]
            if len(campos) != 5:
                raise ValueError(f"Linha {n}: regra invalida '{texto}' "
                                 "(esperado: origem,le,escreve,direcao,destino).")
            origem, le, escreve, direcao, destino = campos
            direcao = direcao.upper()
            if origem not in estados:
                raise ValueError(f"Linha {n}: estado de origem '{origem}' desconhecido.")
            if destino not in estados:
                raise ValueError(f"Linha {n}: estado de destino '{destino}' desconhecido.")
            if le not in alf_fita or escreve not in alf_fita:
                raise ValueError(f"Linha {n}: simbolo fora do alfabeto da fita.")
            if direcao not in DIRECOES:
                raise ValueError(f"Linha {n}: direcao '{direcao}' invalida (use R, L ou S).")
            if (origem, le) in regras:
                raise ValueError(f"Linha {n}: transicao duplicada para ({origem}, {le}). "
                                 "A maquina deve ser deterministica.")
            regras[(origem, le)] = (escreve, direcao, destino)

        return MaquinaDeTuring(estados, alf_entrada, alf_fita, branco, inicial, finais, regras)

    def executar(self, entrada, max_passos=100_000, trace=True):
        """Retorna (resultado, passos, fita) com resultado em ACEITA/REJEITADA/LOOP."""
        for s in entrada:
            if s not in self.alf_entrada:
                raise ValueError(f"Simbolo '{s}' da entrada nao pertence ao alfabeto de entrada.")

        fita = Fita(entrada, self.branco)
        estado = self.inicial
        passos = 0

        if trace:
            print(f"{'Passo':>6} | {'Estado':<10} | Fita")
            print(f"{passos:>6} | {estado:<10} | {fita.formatar()}")

        while True:
            if estado in self.finais:
                return "ACEITA", passos, fita

            regra = self.regras.get((estado, fita.ler()))
            if regra is None:
                return "REJEITADA", passos, fita

            if passos >= max_passos:
                return "LOOP", passos, fita

            escreve, direcao, destino = regra
            fita.escrever(escreve)
            fita.mover(DIRECOES[direcao])
            estado = destino
            passos += 1

            if trace:
                print(f"{passos:>6} | {estado:<10} | {fita.formatar()}")

def rodar_cadeia(mt, cadeia, max_passos, trace):
    print(f"\n=== Entrada: '{cadeia}' ===")
    try:
        resultado, passos, fita = mt.executar(cadeia, max_passos=max_passos, trace=trace)
    except ValueError as e:
        print(f"Erro: {e}", file=sys.stderr)
        return cadeia, "ERRO", 0

    if resultado == "LOOP":
        print(f"\nResultado: LOOP INFINITO provavel (abortado apos {passos} passos)")
    else:
        print(f"\nResultado: {resultado} em {passos} passos")
    print(f"Fita final: '{fita.conteudo()}'")
    return cadeia, resultado, passos


def modo_interativo(mt, max_passos, trace):
    print("Simulador de Maquina de Turing")
    print("Digite uma cadeia e tecle Enter. Enter sem nada testa a cadeia vazia.")
    print("Digite 'sair' para encerrar.")
    while True:
        try:
            cadeia = input("\nCadeia: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if cadeia.lower() == "sair":
            print("Encerrando.")
            break
        rodar_cadeia(mt, cadeia, max_passos, trace)


def main():
    ap = argparse.ArgumentParser(description="Simulador de Maquina de Turing deterministica.")
    ap.add_argument("arquivo", help="arquivo .txt com a definicao da maquina")
    ap.add_argument("entradas", nargs="*",
                    help='cadeias de entrada (opcional; sem elas abre o modo interativo; use "" para a cadeia vazia)')
    ap.add_argument("--max-passos", type=int, default=100_000,
                    help="limite de passos para detectar loops (padrao: 100000)")
    ap.add_argument("--sem-trace", action="store_true", help="nao imprime o passo a passo")
    args = ap.parse_args()

    try:
        mt = MaquinaDeTuring.carregar(args.arquivo)
    except ValueError as e:
        print(f"Erro no arquivo da maquina: {e}", file=sys.stderr)
        sys.exit(1)

    trace = not args.sem_trace

    if not args.entradas:
        modo_interativo(mt, args.max_passos, trace)
        return

    resumo = [rodar_cadeia(mt, c, args.max_passos, trace) for c in args.entradas]
    if len(resumo) > 1:
        print("\n--- Resumo ---")
        for cadeia, res, passos in resumo:
            rotulo = '"' + cadeia + '"'
            print(f"{rotulo:<14} {res:<10} {passos} passos")


if __name__ == "__main__":
    main()