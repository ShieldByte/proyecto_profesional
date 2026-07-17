"""
Validación de archivos para el analizador.
"""

from dataclasses import dataclass

EXTENSION_VALIDA = ".java"

# Palabras clave de otros lenguajes para detectar contenido no válido.
_PISTAS_EXTRANJERAS = {
    "def ": "Python (def)",
    "import numpy": "Python",
    "print(\"": "posible Python/C",
    "SELECT ": "SQL",
    "FROM ": "SQL",
    "<?php": "PHP",
    "#!/bin/": "script de shell",
    "function ": "JavaScript",
    "console.log": "JavaScript",
}


@dataclass
class ResultadoValidacion:
    ok: bool
    ayudante: str  # "java" | "ninguno"
    motivo: str


def validar_archivo(nombre_archivo: str, contenido: str) -> ResultadoValidacion:
    # Validar extensión
    if not nombre_archivo.lower().endswith(EXTENSION_VALIDA):
        return ResultadoValidacion(
            ok=False,
            ayudante="ninguno",
            motivo=(
                f"La extensión de '{nombre_archivo}' no es '{EXTENSION_VALIDA}'."
            ),
        )

    if not contenido.strip():
        return ResultadoValidacion(
            ok=False,
            ayudante="ninguno",
            motivo="El archivo esta vacio; no hay nada que analizar.",
        )

    # Validar contenido (fingerprint)
    for pista, lenguaje in _PISTAS_EXTRANJERAS.items():
        if pista in contenido:
            return ResultadoValidacion(
                ok=False,
                ayudante="ninguno",
                motivo=(
                    f"El contenido del archivo parece ser de {lenguaje} y no de Java."
                ),
            )

    # Verificar estructura mínima de Java (class o interface)
    if "class " not in contenido and "interface " not in contenido:
        return ResultadoValidacion(
            ok=False,
            ayudante="ninguno",
            motivo=(
                "No se encontró ninguna declaración 'class' o 'interface'."
            ),
        )

    return ResultadoValidacion(ok=True, ayudante="java", motivo="Contenido reconocido como Java.")
