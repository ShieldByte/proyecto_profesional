grammar Expr;

// Gramática para el lenguaje Expr.g4.

// Reglas Sintácticas

unidadCompilacion
    : declPaquete? declImportacion* declTipo* EOF
    ;

declPaquete
    : 'package' nombreCalificado ';'
    ;

declImportacion
    : 'import' nombreCalificado ('.' '*')? ';'
    ;

nombreCalificado
    : ID ('.' ID)*
    ;

declTipo
    : declClase
    | declInterfaz
    ;

// Clases

declClase
    : modificadores? 'class' ID ('extends' ID)? ('implements' listaId)? cuerpoClase
    ;

listaId
    : ID (',' ID)*
    ;

cuerpoClase
    : '{' declMiembro* '}'
    ;

declMiembro
    : declCampo
    | declConstructor
    | declMetodo
    ;

declCampo
    : modificadores? tipo ID ('=' expresion)? ';'
    ;

declConstructor
    : modificadores? ID '(' listaParametros? ')' bloque
    ;

declMetodo
    : modificadores? (tipo | 'void') ID '(' listaParametros? ')' ('throws' listaId)? (bloque | ';')
    ;

listaParametros
    : parametro (',' parametro)*
    ;

parametro
    : tipo ID
    ;

modificadores
    : modificador+
    ;

modificador
    : 'public' | 'private' | 'protected' | 'static' | 'final' | 'abstract'
    ;

// Interfaces

declInterfaz
    : modificadores? 'interface' ID ('extends' listaId)? cuerpoInterfaz
    ;

cuerpoInterfaz
    : '{' declMiembroInterfaz* '}'
    ;

declMiembroInterfaz
    : tipo? 'void'? ID '(' listaParametros? ')' ';'   # firmaMetodoInterfaz
    | tipo ID '=' expresion ';'                       # constanteInterfaz
    ;

// Tipos

tipo
    : tipoPrimitivo ('[' ']')*
    | ID ('[' ']')*
    ;

tipoPrimitivo
    : 'int' | 'double' | 'float' | 'long' | 'short' | 'byte' | 'char' | 'boolean' | 'String'
    ;

// Sentencias

bloque
    : '{' sentencia* '}'
    ;

sentencia
    : bloque                                            # sentenciaBloque
    | declVarLocal ';'                                 # sentenciaDeclVar
    | ifSentencia                                           # sentenciaIf
    | forSentencia                                          # sentenciaFor
    | whileSentencia                                        # sentenciaWhile
    | doWhileSentencia                                      # sentenciaDoWhile
    | trySentencia                                          # sentenciaTry
    | 'throw' expresion ';'                                 # sentenciaThrow
    | 'return' expresion? ';'                                # sentenciaReturn
    | 'break' ';'                                       # sentenciaBreak
    | 'continue' ';'                                    # sentenciaContinue
    | expresion ';'                                          # sentenciaExpr
    | ';'                                                # sentenciaVacia
    ;

declVarLocal
    : tipo ID ('=' expresion)?
    ;

ifSentencia
    : 'if' '(' expresion ')' sentencia ('else' sentencia)?
    ;

forSentencia
    : 'for' '(' (declVarLocal | expresion)? ';' expresion? ';' expresion? ')' sentencia
    ;

whileSentencia
    : 'while' '(' expresion ')' sentencia
    ;

doWhileSentencia
    : 'do' sentencia 'while' '(' expresion ')' ';'
    ;

trySentencia
    : 'try' bloque (clausulaCatch+ clausulaFinally? | clausulaFinally)
    ;

clausulaCatch
    : 'catch' '(' ID ID ')' bloque
    ;

clausulaFinally
    : 'finally' bloque
    ;

// Expresiones

expresion
    : primario                                          # expresionPrimaria
    | expresion '.' ID                                       # expresionAccesoCampo
    | expresion '.' ID '(' listaArgs? ')'                       # expresionLlamadaMetodo
    | ID '(' listaArgs? ')'                                # expresionLlamada
    | 'new' ID '(' listaArgs? ')'                          # expresionNuevoObjeto
    | 'new' tipoPrimitivo '[' expresion ']'                   # expresionNuevoArreglo
    | expresion '[' expresion ']'                                  # expresionAccesoArreglo
    | ('+' | '-' | '!') expresion                             # expresionUnaria
    | expresion ('++' | '--')                                 # expresionPostfija
    | expresion ('*' | '/' | '%') expresion                        # expresionMulDiv
    | expresion ('+' | '-') expresion                              # expresionSumaResta
    | expresion ('<' | '>' | '<=' | '>=') expresion                 # expresionRelacional
    | expresion ('==' | '!=') expresion                             # expresionIgualdad
    | expresion '&&' expresion                                     # expresionY
    | expresion '||' expresion                                     # expresionO
    | <assoc=right> ID ('=' | '+=' | '-=' | '*=' | '/=') expresion   # expresionAsignacion
    ;

listaArgs
    : expresion (',' expresion)*
    ;

primario
    : '(' expresion ')'
    | literal
    | 'this'
    | 'super'
    | ID
    ;

literal
    : LITERAL_ENTERO
    | LITERAL_FLOTANTE
    | LITERAL_CADENA
    | LITERAL_CARACTER
    | LITERAL_BOOL
    | LITERAL_NULO
    ;

// Reglas Léxicas

// Palabras reservadas
CLASE       : 'class';
INTERFAZ   : 'interface';
EXTIENDE     : 'extends';
IMPLEMENTA  : 'implements';
PUBLICO      : 'public';
PRIVADO     : 'private';
PROTEGIDO   : 'protected';
ESTATICO      : 'static';
FINAL       : 'final';
ABSTRACTO    : 'abstract';
VACIO        : 'void';
NUEVO         : 'new';
RETORNO      : 'return';
SI          : 'if';
SINO        : 'else';
PARA         : 'for';
MIENTRAS       : 'while';
HACER          : 'do';
ROMPER       : 'break';
CONTINUAR    : 'continue';
INTENTAR         : 'try';
CAPTURAR       : 'catch';
FINALMENTE     : 'finally';
LANZAR       : 'throw';
LANZA      : 'throws';
ESTE        : 'this';
PADRE       : 'super';
IMPORTAR      : 'import';
PAQUETE     : 'package';

// Literales booleanos y nulo
LITERAL_BOOL : 'true' | 'false';
LITERAL_NULO : 'null';

// Identificadores
ID
    : [a-zA-Z_$] [a-zA-Z0-9_$]*
    ;

// Literales
LITERAL_ENTERO
    : [0-9]+
    ;

LITERAL_FLOTANTE
    : [0-9]+ '.' [0-9]+
    ;

LITERAL_CADENA
    : '"' ( SEC_ESC | ~["\\\r\n] )* '"'
    ;

LITERAL_CARACTER
    : '\'' ( SEC_ESC | ~['\\\r\n] ) '\''
    ;

fragment SEC_ESC
    : '\\' ('n' | 't' | 'r' | '"' | '\'' | '\\')
    ;

// Operadores
ASIGNAR      : '=';
ASIGNAR_MAS : '+=';
ASIGNAR_MENOS: '-=';
ASIGNAR_MUL  : '*=';
ASIGNAR_DIV  : '/=';
IGUAL          : '==';
DIFERENTE         : '!=';
MENOR_IGUAL          : '<=';
MAYOR_IGUAL          : '>=';
MENOR          : '<';
MAYOR          : '>';
Y         : '&&';
O          : '||';
NO         : '!';
INCREMENTO         : '++';
DECREMENTO         : '--';
MAS        : '+';
MENOS       : '-';
MUL        : '*';
DIV        : '/';
MOD        : '%';

// Delimitadores
PARENTESIS_IZQ      : '(';
PARENTESIS_DER      : ')';
LLAVE_IZQ      : '{';
LLAVE_DER      : '}';
CORCHETE_IZQ      : '[';
CORCHETE_DER      : ']';
PUNTO_Y_COMA        : ';';
COMA       : ',';
PUNTO         : '.';

// Comentarios y espacios en blanco
COMENTARIO_LINEA  : '//' ~[\r\n]* -> skip;
COMENTARIO_BLOQUE : '/*' .*? '*/' -> skip;
ESPACIO            : [ \t\r\n]+ -> skip;

// Error léxico
CARACTER_ERROR : . ;
