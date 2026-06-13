import streamlit as st
import re
import random

# 1. Función para leer y procesar el archivo de texto
def cargar_preguntas(ruta_archivo):
    with open(ruta_archivo, 'r', encoding='utf-8') as file:
        texto = file.read()

    patron = r"Materia:\s*(.*?)\s*Unidad:\s*(.*?)\s*Pregunta:\s*(.*?)\s*A\)\s*(.*?)\s*B\)\s*(.*?)\s*C\)\s*(.*?)\s*D\)\s*(.*?)\s*Respuesta:\s*(A|B|C|D)"
    matches = re.findall(patron, texto, re.IGNORECASE | re.DOTALL)
    
    preguntas = []
    for match in matches:
        preguntas.append({
            "materia": match[0].strip(),
            "unidad": match[1].strip(),
            "pregunta": match[2].strip(),
            "opciones": {
                "A": f"A) {match[3].strip()}",
                "B": f"B) {match[4].strip()}",
                "C": f"C) {match[5].strip()}",
                "D": f"D) {match[6].strip()}"
            },
            "respuesta_correcta": match[7].strip().upper()
        })
    return preguntas

# 2. Configuración de la página
st.set_page_config(page_title="Mi App de Estudio", layout="centered")
st.title("📚 Mi App de Test Interactivo")

# 3. Cargar datos
try:
    todas_las_preguntas = cargar_preguntas("TestNotebook.txt")
except FileNotFoundError:
    st.error("No se encontró el archivo 'TestNotebook.txt'. Asegúrate de que esté en la misma carpeta que este script.")
    st.stop()

if not todas_las_preguntas:
    st.warning("No se pudieron extraer preguntas del archivo. Verifica el formato.")
    st.stop()

# 4. Menú lateral (Filtros de Materia y Unidad)
st.sidebar.header("⚙️ Configuración del Test")

materias_disponibles = sorted(list(set([p["materia"] for p in todas_las_preguntas])))
materia_seleccionada = st.sidebar.selectbox("Elige la Materia:", materias_disponibles)

unidades_disponibles = sorted(list(set([p["unidad"] for p in todas_las_preguntas if p["materia"] == materia_seleccionada])))
unidad_seleccionada = st.sidebar.selectbox("Elige la Unidad:", unidades_disponibles)

preguntas_filtradas = [p for p in todas_las_preguntas if p["materia"] == materia_seleccionada and p["unidad"] == unidad_seleccionada]

# NUEVO: Selector de cantidad de preguntas
st.sidebar.markdown("---")
max_preguntas = len(preguntas_filtradas)

opciones_cantidad = ["Todas"] + [n for n in [5, 10, 15, 20, 30, 50, 100] if n < max_preguntas]
cantidad_seleccionada = st.sidebar.selectbox(
    f"Número de preguntas (Máx: {max_preguntas}):",
    options=opciones_cantidad,
    key="cantidad_preguntas"
)

# 5. Lógica del Test y Estado de la Sesión
if 'indice' not in st.session_state:
    st.session_state.indice = 0
if 'puntuacion' not in st.session_state:
    st.session_state.puntuacion = 0
if 'respondido' not in st.session_state:
    st.session_state.respondido = False
if 'filtro_actual' not in st.session_state:
    st.session_state.filtro_actual = (None, None, None)
if 'preguntas_mezcladas' not in st.session_state:
    st.session_state.preguntas_mezcladas = []

# Si se cambia materia, unidad o la cantidad de preguntas, reiniciamos y mezclamos
configuracion_actual = (materia_seleccionada, unidad_seleccionada, cantidad_seleccionada)

if st.session_state.filtro_actual != configuracion_actual:
    st.session_state.indice = 0
    st.session_state.puntuacion = 0
    st.session_state.respondido = False
    st.session_state.filtro_actual = configuracion_actual
    
    # Copiamos y barajamos el mazo completo de la unidad
    copia_preguntas = preguntas_filtradas.copy()
    random.shuffle(copia_preguntas)
    
    # Recortamos la lista según lo que haya elegido el usuario
    if cantidad_seleccionada != "Todas":
        copia_preguntas = copia_preguntas[:int(cantidad_seleccionada)]
        
    st.session_state.preguntas_mezcladas = copia_preguntas
    st.rerun()

lista_actual = st.session_state.preguntas_mezcladas

# 6. Interfaz del Test
if len(lista_actual) > 0:
    if st.session_state.indice < len(lista_actual):
        pregunta_actual = lista_actual[st.session_state.indice]
        
        st.subheader(f"Pregunta {st.session_state.indice + 1} de {len(lista_actual)}")
        st.write(f"**{pregunta_actual['pregunta']}**")
        
        # Guardar la selección del usuario
        opcion_elegida = st.radio("Selecciona tu respuesta:", 
                                  options=["A", "B", "C", "D"], 
                                  format_func=lambda x: pregunta_actual['opciones'][x],
                                  key=f"radio_{st.session_state.indice}",
                                  disabled=st.session_state.respondido)
        
        # Botón para comprobar
        if not st.session_state.respondido:
            if st.button("Comprobar respuesta", type="primary"):
                st.session_state.respondido = True
                if opcion_elegida == pregunta_actual['respuesta_correcta']:
                    st.session_state.puntuacion += 1
                st.rerun()
        else:
            # Mostrar resultado de la pregunta
            es_correcta = opcion_elegida == pregunta_actual['respuesta_correcta']
            if es_correcta:
                st.success("¡Correcto! ✅")
            else:
                st.error(f"Incorrecto ❌. La respuesta correcta era la **{pregunta_actual['respuesta_correcta']}**.")
            
            # Botón para continuar
            if st.button("Siguiente pregunta"):
                st.session_state.indice += 1
                st.session_state.respondido = False
                st.rerun()
                
        # Mostrar puntuación actual
        st.progress((st.session_state.indice) / len(lista_actual))
        st.write(f"Puntuación actual: **{st.session_state.puntuacion}** aciertos")

    else:
        # Pantalla final de la unidad
        st.balloons()
        st.header("¡Has terminado el test!")
        nota_final = (st.session_state.puntuacion / len(lista_actual)) * 10
        st.write(f"Tuviste **{st.session_state.puntuacion}** aciertos de **{len(lista_actual)}**.")
        st.subheader(f"Tu nota es: {nota_final:.2f} / 10")
        
        if st.button("Repetir este test"):
            st.session_state.indice = 0
            st.session_state.puntuacion = 0
            st.session_state.respondido = False
            
            # Al repetir, volvemos a barajar y recortar
            copia_preguntas = preguntas_filtradas.copy()
            random.shuffle(copia_preguntas)
            if cantidad_seleccionada != "Todas":
                copia_preguntas = copia_preguntas[:int(cantidad_seleccionada)]
            st.session_state.preguntas_mezcladas = copia_preguntas
            
            st.rerun()
else:
    st.info("No hay preguntas disponibles para esta combinación de configuración.")