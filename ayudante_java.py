"""
Módulo de ayuda para orquestar el análisis de Expr.g4.
"""

import antlr4

from generated.ExprLexer import ExprLexer
from generated.ExprParser import ExprParser
from oyente_semantico import SemanticListener


class InfoErrorSintactico:
    def __init__(self, linea, columna, mensaje):
        self.linea = linea
        self.columna = columna
        self.mensaje = mensaje

    def __str__(self):
        return f"[Linea {self.linea}:{self.columna}] {self.mensaje}"


class OyenteErrores(antlr4.error.ErrorListener.ErrorListener):
    """Listener para recolectar errores léxicos y sintácticos."""

    def __init__(self):
        super().__init__()
        self.errores = []

    def syntaxError(self, reconocedor, simbolo_ofensor, linea, columna, mensaje, excepcion):
        self.errores.append(InfoErrorSintactico(linea, columna, mensaje))


def analizar(codigo_fuente: str) -> dict:
    """Analiza el código fuente y devuelve el resultado."""

    flujo_entrada = antlr4.InputStream(codigo_fuente)

    # 1. Análisis léxico
    oyente_errores_lexer = OyenteErrores()
    analizador_lexico = ExprLexer(flujo_entrada)
    analizador_lexico.removeErrorListeners()
    analizador_lexico.addErrorListener(oyente_errores_lexer)

    flujo_tokens = antlr4.CommonTokenStream(analizador_lexico)
    flujo_tokens.fill()

    def obtener_nombre_tipo(tipo_id):
        if tipo_id == -1:
            return "EOF"
        tipo_simbolico = ExprParser.symbolicNames[tipo_id] if tipo_id < len(ExprParser.symbolicNames) else None
        if not tipo_simbolico or tipo_simbolico == "<INVALID>":
            tipo_literal = ExprParser.literalNames[tipo_id] if tipo_id < len(ExprParser.literalNames) else None
            if tipo_literal and tipo_literal != "<INVALID>":
                return tipo_literal.strip("'")
            return "OTRO"
        return tipo_simbolico

    informacion_tokens = [
        {
            "texto": t.text,
            "tipo": obtener_nombre_tipo(t.type),
            "linea": t.line,
            "columna": t.column,
        }
        for t in flujo_tokens.tokens
        if t.type != antlr4.Token.EOF
    ]

    # 2. Análisis sintáctico
    oyente_errores_parser = OyenteErrores()
    analizador_sintactico = ExprParser(flujo_tokens)
    analizador_sintactico.removeErrorListeners()
    analizador_sintactico.addErrorListener(oyente_errores_parser)

    arbol = analizador_sintactico.unidadCompilacion()

    errores_sintacticos = oyente_errores_lexer.errores + oyente_errores_parser.errores

    resultado = {
        "tokens": informacion_tokens,
        "errores_lexicos_sintacticos": [str(e) for e in errores_sintacticos],
        "errores_semanticos": [],
        "advertencias_semanticas": [],
        "arbol": arbol.toStringTree(recog=analizador_sintactico) if not errores_sintacticos else None,
    }

    # 3. Análisis semántico
    if not errores_sintacticos:
        oyente_semantico = SemanticListener()
        caminador = antlr4.ParseTreeWalker()
        caminador.walk(oyente_semantico, arbol)

        resultado["errores_semanticos"] = [str(e) for e in oyente_semantico.errores]
        resultado["advertencias_semanticas"] = [str(w) for w in oyente_semantico.advertencias]

    return resultado
