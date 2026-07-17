"""
Interfaz del analizador Expr.g4.
"""

import streamlit as st

import validacion
import ayudante_java

st.set_page_config(page_title="Analizador Expr.g4", layout="wide")

st.title("Analizador Léxico, Sintáctico y Semántico — Expr.g4")
st.caption(
    "Basado en la investigación de Reglas Sintácticas y Semánticas "
    "(Lenguajes y Autómatas II) — subconjunto orientado a objetos de Java."
)

archivo_subido = st.file_uploader("Sube un archivo .java", type=None)

if archivo_subido is not None:
    bytes_crudos = archivo_subido.read()
    try:
        contenido = bytes_crudos.decode("utf-8")
    except UnicodeDecodeError:
        st.error("El archivo no es texto plano UTF-8; no se puede analizar.")
        st.stop()

    resultado = validacion.validar_archivo(archivo_subido.name, contenido)

    if not resultado.ok:
        st.error(f"Archivo no procesado: {resultado.motivo}")
        st.info(
            "Este proyecto solo implementa el analizador de **Expr.g4**."
        )
        st.stop()

    st.success(f"Archivo '{archivo_subido.name}' reconocido como Java. Analizando...")

    with st.expander("Código fuente", expanded=False):
        st.code(contenido, language="java")

    analisis = ayudante_java.analizar(contenido)

    pestana_lexica, pestana_sintactica, pestana_semantica = st.tabs(
        ["1. Léxico", "2. Sintáctico", "3. Semántico"]
    )

    with pestana_lexica:
        st.subheader("Tokens reconocidos")
        st.write(f"Total de tokens: {len(analisis['tokens'])}")
        st.dataframe(analisis['tokens'], use_container_width=True)

    with pestana_sintactica:
        st.subheader("Errores léxicos / sintácticos")
        if analisis["errores_lexicos_sintacticos"]:
            for error in analisis["errores_lexicos_sintacticos"]:
                st.error(error)
        else:
            st.success("Sin errores léxicos ni sintácticos. Estructura del programa correcta.")
            with st.expander("Árbol de análisis (texto)"):
                st.code(analisis["arbol"])

    with pestana_semantica:
        st.subheader("Validación semántica")
        if analisis["errores_lexicos_sintacticos"]:
            st.warning(
                "No se ejecutó la validación semántica porque el archivo "
                "tiene errores léxicos/sintácticos previos. Corrígelos primero."
            )
        elif analisis["errores_semanticos"]:
            for error in analisis["errores_semanticos"]:
                st.error(error)
        else:
            st.success("Sin errores semánticos detectados.")

        if analisis["advertencias_semanticas"]:
            st.subheader("Advertencias")
            for advertencia in analisis["advertencias_semanticas"]:
                st.warning(advertencia)
else:
    st.info("Esperando un archivo .java para comenzar el análisis.")
