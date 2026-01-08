import streamlit as st
import apim.dojo as dojo
from apim.core import clasificar, recomendaciones
from apim.dojo import demo_forward_pass, train_on_startup
from apim.dojo import predict_v3
from apim.storage import save_shadow
from apim.storage import save_run, save_feedback

# Para Genio / Jefe NO mostramos el botón, pero igual lo guardamos por si lo piden
def debe_mostrar_principios(persona: str) -> bool:
    return persona not in ["Jefe de jefes", "Genio financiero"]

# Configuracion basica 
st.set_page_config(page_title="APIM VI", page_icon="💸", layout="centered")
st.title("APIM VI - Test Financiero Inteligente")

# Formulario
with st.form("form_apim"):
    st.subheader("Ingresa tus respuestas")

    ahorro_pct = st.slider("¿Qué % de tu ingreso ahorras al mes?", 0, 50, 10)
    compras_imp = st.number_input("Compras impulsivas por semana", min_value=0, max_value=50, value=1, step=1)
    registra = st.checkbox("Registro mis gastos (aunque sea en notas)")
    fondo_meses = st.slider("Fondo de emergencia (meses cubiertos)", 0, 12, 3)

    submitted = st.form_submit_button("Clasificar")


# Al clasificar calculamos y guardamos en sesión + historial JSON
if submitted:
    respuestas = {
        "ahorro_mensual_pct": int(ahorro_pct),
        "compras_impulsivas_sem": int(compras_imp),
        "registra_gastos": bool(registra),
        "fondo_emergencia_meses": int(fondo_meses),
    }
# Clasificacion principal y recomendaciones personalizadas
    result = clasificar(respuestas)
    reco = recomendaciones(result.persona, respuestas)

# Guardamos todo en sesion 
    st.session_state["respuestas"] = respuestas
    st.session_state["result"] = result
    st.session_state["reco"] = reco
    st.session_state["active_section"] = None

    # Guardamos corrida una sola vez
    run_id = save_run(respuestas, result)
    st.session_state["run_id"] = run_id

    # Prediccion silenciosa V3 en modo shadow
    try:
        v3_pred = predict_v3(respuestas)
        save_shadow(run_id, result.persona, v3_pred)
    except Exception:
        pass


# Resultados
if "result" in st.session_state:
    result = st.session_state["result"]
    reco = st.session_state["reco"]
    respuestas = st.session_state["respuestas"]
    run_id = st.session_state.get("run_id", "")

    st.subheader("Tu perfil")
    st.write(result.persona)
    st.caption(result.resumen)

    st.subheader("Score APIM")
    st.write(result.score)

    # Demo del Dojo explicativo y visual
    with st.expander("🤖 Toques de IA (Dojo)", expanded=False):
        salida, medidor = demo_forward_pass(respuestas)
        st.write("Señal del Dojo (demo):")
        st.code(str(salida))
        st.write(f"Medidor de cercanía (demo): **{medidor:.4f}**")


    # Botones de acciones/planes
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔥 Acciones hoy", use_container_width=True):
            st.session_state["active_section"] = "hoy"

    with col2:
        if st.button("🗓️ Plan 7 días", use_container_width=True):
            st.session_state["active_section"] = "7"

    with col3:
        if st.button("📆 Plan 30 días", use_container_width=True):
            st.session_state["active_section"] = "30"

    if debe_mostrar_principios(result.persona):
        if st.button(" Principios (base)"):
            st.session_state["active_section"] = "principios"
           
    if st.session_state.get("active_section") is None:
        st.caption("Elige un botón arriba para ver el plan 👆")

    # Acciones y planes especificos
    st.markdown("## Recomendaciones accionables")
    active = st.session_state.get("active_section")
    if active is None:
        pass
    elif active == "hoy":
        st.markdown("### 3 acciones inmediatas (hoy):")
        for a in reco["acciones_inmediatas"]:
            st.markdown(f"- {a}")
    elif active == "7":
        st.markdown("### Plan para los próximos 7 días:")
        for p in reco["plan_7_dias"]:
            st.markdown(f"- {p}")
    elif active == "30":
        st.markdown("### Plan para los próximos 30 días:")
        for p in reco["plan_30_dias"]:
            st.markdown(f"- {p}")
    elif active == "principios":
        st.markdown("### Principios financieros en los que se basa todo esto:")
        for pr in reco["principios"]:
            st.markdown(f"- {pr}")

    # Enfoque recomendado
    with st.expander(" Enfoque recomendado (según puntos débiles detectados)", expanded=True):
        for e in reco["enfoque"]:
            st.markdown(f"- {e}")

    # Feedback del usuario
    st.markdown("---")
    st.subheader("✍️ Feedback rápido")

    rating = st.slider("¿Qué tan útil fue este resultado?", 1, 5, 4)
    comentario = st.text_input("Comentario opcional (1 línea):", "")

    if st.button("Guardar feedback"):
        if run_id:
            save_feedback(run_id, rating, comentario)
            st.success(" ✅ Gracias por tu respuesta")
        else:
            st.warning("Primero clasifica para generar un run_id.")

