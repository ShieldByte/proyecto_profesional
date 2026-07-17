"""
Listener para la validación semántica de Expr.g4.
"""

from generated.ExprListener import ExprListener
from generated.ExprParser import ExprParser


class ErrorSemantico:
    def __init__(self, linea, columna, mensaje):
        self.linea = linea
        self.columna = columna
        self.mensaje = mensaje

    def __str__(self):
        return f"[Linea {self.linea}:{self.columna}] {self.mensaje}"


# Tipos primitivos y numéricos admitidos
_TIPO_LITERAL_DE = {
    "LITERAL_ENTERO": "int",
    "LITERAL_FLOTANTE": "double",
    "LITERAL_CADENA": "String",
    "LITERAL_CARACTER": "char",
    "LITERAL_BOOL": "boolean",
    "LITERAL_NULO": "null",
}

_TIPOS_NUMERICOS = {"int", "double", "float", "long", "short", "byte"}


class Ambito:
    def __init__(self, padre=None):
        self.padre = padre
        self.simbolos = {}  # nombre -> tipo (str)

    def declarar(self, nombre, tipo):
        self.simbolos[nombre] = tipo

    def declarado_aqui(self, nombre):
        return nombre in self.simbolos

    def resolver(self, nombre):
        ambito = self
        while ambito is not None:
            if nombre in ambito.simbolos:
                return ambito.simbolos[nombre]
            ambito = ambito.padre
        return None


class SemanticListener(ExprListener):
    def __init__(self):
        self.errores = []
        self.advertencias = []
        self.ambito_global = Ambito()
        self.pila_ambitos = [self.ambito_global]

        self.clases = {}          # nombre_clase -> {"extends":..., "abstract": bool}
        self.clase_actual = None
        self.tipo_retorno_metodo_actual = None  # 'void' o tipo, o None fuera de metodo
        self.metodos_clase_actual = {}          # nombre_clase -> [(nombre, [tipos_param])]
        self.atributos_clase = {}               # nombre_clase -> {nombre_attr: tipo}

    # Utilidades

    def _ambito_actual(self):
        return self.pila_ambitos[-1]

    def _apilar_ambito(self):
        self.pila_ambitos.append(Ambito(padre=self._ambito_actual()))

    def _desapilar_ambito(self):
        self.pila_ambitos.pop()

    def _error(self, ctx, mensaje):
        tok = ctx.start
        self.errores.append(ErrorSemantico(tok.line, tok.column, mensaje))

    def _advertir(self, ctx, mensaje):
        tok = ctx.start
        self.advertencias.append(ErrorSemantico(tok.line, tok.column, mensaje))

    def _texto_tipo(self, ctx_tipo):
        return ctx_tipo.getText() if ctx_tipo else "void"

    # Clases e interfaces

    def enterDeclClase(self, ctx: ExprParser.DeclClaseContext):
        nombre_clase = ctx.ID(0).getText()
        padre = ctx.ID(1).getText() if ctx.EXTIENDE() else None
        es_abstracto = ctx.modificadores() is not None and "abstract" in ctx.modificadores().getText()

        self.clases[nombre_clase] = {"extends": padre, "abstract": es_abstracto}
        self.metodos_clase_actual[nombre_clase] = []
        self.clase_actual = nombre_clase
        self._apilar_ambito()

        # Inicializar atributos de la clase
        self.atributos_clase[nombre_clase] = {}

        # Copiar atributos heredados de la clase padre si está definida
        if padre and padre in self.atributos_clase:
            for nom_attr, tipo_attr in self.atributos_clase[padre].items():
                self._ambito_actual().declarar(nom_attr, tipo_attr)
                self.atributos_clase[nombre_clase][nom_attr] = tipo_attr

    def exitDeclClase(self, ctx: ExprParser.DeclClaseContext):
        # Validar que la clase padre exista
        info = self.clases.get(self.clase_actual, {})
        padre = info.get("extends")
        if padre and padre not in self.clases:
            self._advertir(
                ctx,
                f"La clase padre '{padre}' no está definida en este archivo.",
            )
        self._desapilar_ambito()
        self.clase_actual = None

    # Atributos

    def enterDeclCampo(self, ctx: ExprParser.DeclCampoContext):
        nombre = ctx.ID().getText()
        tipo_declarado = self._texto_tipo(ctx.tipo())
        ambito = self._ambito_actual()

        if ambito.declarado_aqui(nombre):
            self._error(ctx, f"El atributo '{nombre}' ya fue declarado en esta clase.")
        else:
            ambito.declarar(nombre, tipo_declarado)
            if self.clase_actual:
                self.atributos_clase[self.clase_actual][nombre] = tipo_declarado

        if ctx.expresion():
            self._verificar_asignacion_literal(ctx, tipo_declarado, ctx.expresion())

    # Métodos

    def enterDeclMetodo(self, ctx: ExprParser.DeclMetodoContext):
        nombre = ctx.ID().getText()
        tipo_retorno = self._texto_tipo(ctx.tipo()) if ctx.tipo() else "void"
        parametros = ctx.listaParametros().parametro() if ctx.listaParametros() else []
        tipos_parametros = [self._texto_tipo(p.tipo()) for p in parametros]

        # Verificar duplicidad de firma
        hermanos = self.metodos_clase_actual.get(self.clase_actual, [])
        for (otro_nombre, otros_tipos) in hermanos:
            if otro_nombre == nombre and otros_tipos == tipos_parametros:
                self._error(
                    ctx,
                    f"El método '{nombre}({', '.join(tipos_parametros)})' ya está declarado en la clase '{self.clase_actual}'.",
                )
        hermanos.append((nombre, tipos_parametros))
        self.metodos_clase_actual[self.clase_actual] = hermanos

        # Validar método sin cuerpo
        tiene_cuerpo = ctx.bloque() is not None
        info_clase = self.clases.get(self.clase_actual, {})
        if not tiene_cuerpo and not info_clase.get("abstract", False):
            self._error(
                ctx,
                f"El método '{nombre}' no tiene cuerpo y la clase '{self.clase_actual}' no es abstracta.",
            )

        self.tipo_retorno_metodo_actual = tipo_retorno
        self._apilar_ambito()
        for p, t in zip(parametros, tipos_parametros):
            self._ambito_actual().declarar(p.ID().getText(), t)

    def exitDeclMetodo(self, ctx: ExprParser.DeclMetodoContext):
        self._desapilar_ambito()
        self.tipo_retorno_metodo_actual = None

    def enterDeclConstructor(self, ctx: ExprParser.DeclConstructorContext):
        self._apilar_ambito()
        if ctx.listaParametros():
            for p in ctx.listaParametros().parametro():
                self._ambito_actual().declarar(p.ID().getText(), self._texto_tipo(p.tipo()))

    def exitDeclConstructor(self, ctx: ExprParser.DeclConstructorContext):
        self._desapilar_ambito()

    # Bloques

    def enterSentenciaBloque(self, ctx: ExprParser.SentenciaBloqueContext):
        self._apilar_ambito()

    def exitSentenciaBloque(self, ctx: ExprParser.SentenciaBloqueContext):
        self._desapilar_ambito()

    # Variables locales

    def enterDeclVarLocal(self, ctx: ExprParser.DeclVarLocalContext):
        nombre = ctx.ID().getText()
        tipo_declarado = self._texto_tipo(ctx.tipo())
        ambito = self._ambito_actual()

        if ambito.declarado_aqui(nombre):
            self._error(ctx, f"La variable '{nombre}' ya fue declarada en este ambito.")
        else:
            ambito.declarar(nombre, tipo_declarado)

        if ctx.expresion():
            self._verificar_asignacion_literal(ctx, tipo_declarado, ctx.expresion())

    # Uso de identificadores

    def enterExpresionPrimaria(self, ctx: ExprParser.ExpresionPrimariaContext):
        primary = ctx.primario()
        # Verificar declaración de identificadores
        if primary.ID() is not None:
            nombre = primary.ID().getText()
            if self._ambito_actual().resolver(nombre) is None:
                self._error(
                    ctx,
                    f"El identificador '{nombre}' no ha sido declarado.",
                )

    def enterExpresionAsignacion(self, ctx: ExprParser.ExpresionAsignacionContext):
        nombre = ctx.ID().getText()
        if self._ambito_actual().resolver(nombre) is None:
            self._error(
                ctx,
                f"La variable '{nombre}' no está declarada.",
            )

    # Retornos

    def enterSentenciaReturn(self, ctx: ExprParser.SentenciaReturnContext):
        if self.tipo_retorno_metodo_actual is None:
            return

        tiene_valor = ctx.expresion() is not None
        if self.tipo_retorno_metodo_actual == "void" and tiene_valor:
            self._error(
                ctx,
                "El método es void pero retorna un valor.",
            )
        elif self.tipo_retorno_metodo_actual != "void" and not tiene_valor:
            self._error(
                ctx,
                f"El método debe retornar un valor de tipo '{self.tipo_retorno_metodo_actual}'.",
            )

    # Excepciones (Catch / Finally)

    def enterClausulaCatch(self, ctx: ExprParser.ClausulaCatchContext):
        self._apilar_ambito()
        nombre_var = ctx.ID(1).getText()
        tipo_var = ctx.ID(0).getText()
        self._ambito_actual().declarar(nombre_var, tipo_var)

    def exitClausulaCatch(self, ctx: ExprParser.ClausulaCatchContext):
        self._desapilar_ambito()

    def enterClausulaFinally(self, ctx: ExprParser.ClausulaFinallyContext):
        self._apilar_ambito()

    def exitClausulaFinally(self, ctx: ExprParser.ClausulaFinallyContext):
        self._desapilar_ambito()

    # Validación de tipos con literales

    def _verificar_asignacion_literal(self, ctx, tipo_declarado, expr_ctx):
        """Valida la asignación de un literal a un tipo declarado."""
        texto = expr_ctx.getText()
        literal_ctx = None
        try:
            literal_ctx = expr_ctx.primario().literal()
        except Exception:
            literal_ctx = None

        if literal_ctx is None:
            return

        if literal_ctx.LITERAL_ENTERO():
            tipo_lit = "int"
        elif literal_ctx.LITERAL_FLOTANTE():
            tipo_lit = "double"
        elif literal_ctx.LITERAL_CADENA():
            tipo_lit = "String"
        elif literal_ctx.LITERAL_CARACTER():
            tipo_lit = "char"
        elif literal_ctx.LITERAL_BOOL():
            tipo_lit = "boolean"
        elif literal_ctx.LITERAL_NULO():
            tipo_lit = "null"
        else:
            return

        if tipo_lit == "null":
            return

        compatible = (
            tipo_declarado == tipo_lit
            or (tipo_declarado in _TIPOS_NUMERICOS and tipo_lit in _TIPOS_NUMERICOS)
        )
        if not compatible:
            self._error(
                ctx,
                f"Tipos incompatibles: se declaró '{tipo_declarado}' pero se asignó '{tipo_lit}' ({texto}).",
            )
