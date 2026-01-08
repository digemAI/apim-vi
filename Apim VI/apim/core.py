from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List

# Estructura final que usa la app (Streamlit)
@dataclass
class Result:
    persona: str
    score: int
    resumen: str

# 1) Clasificador Principal (V1)
def clasificar(respuestas: Dict[str, Any]) -> Result:
    score = 0
 # Extraemos valores 
    ahorro_pct = respuestas.get("ahorro_mensual_pct", 0)         
    compras_imp = respuestas.get("compras_impulsivas_sem", 0)    
    registra = respuestas.get("registra_gastos", False)          
    fondo_meses = respuestas.get("fondo_emergencia_meses", 0)     

# Ahorro: premiamos ahorrar al menos 10% y mas todavía si >= 20%    
    if ahorro_pct >= 10:
        score += 3
    if ahorro_pct >= 20:
        score += 2

# Impulsivas: penalizamos si compras por impulso son frecuentes
    if compras_imp >= 3:
        score -= 3
    if compras_imp >= 7:
        score -= 2

# Registro de gastos: premiamos si registras (porque controlas)
    if registra:
        score += 2

# Fondo de emergencia: premiamos un fondo >= 3 meses y más si >= 6
    if fondo_meses >= 3:
        score += 3
    if fondo_meses >= 6:
        score += 2

# Mapeo a persona
    if score <= 0:
        persona = "Comprador impulsivo"
        resumen = "Tienes potencia, pero el dinero se te va en ráfagas. Vamos a domar eso."
    elif 1 <= score <= 4:
        persona = "Ahorrador disciplinado"
        resumen = "Vas bien: constancia y dedicación, los dos ajustes con los que subes de liga."
    elif 5 <= score <= 7:
        persona = "Genio financiero"
        resumen = "Decides bien y sostienes hábitos. Siempre encontraras oportunidades."
    else:
        persona = "Jefe de jefes"
        resumen = "Control total. Eres el villano final"

    return Result(persona=persona, score=score, resumen=resumen)

# 2) Detector de debilidades (V2)
def detectar_debilidades(respuestas: Dict[str, Any]) -> List[str]:
    debilidades: List[str] = []

# Convertimos a tipos seguros 
    ahorro = int(respuestas.get("ahorro_mensual_pct", 0))                  
    impulsivas = int(respuestas.get("compras_impulsivas_sem", 0))          
    registra = bool(respuestas.get("registra_gastos", False))             
    fondo = float(respuestas.get("fondo_emergencia_meses", 0))             

# Umbrales simples ajustables
    if impulsivas >= 3:
        debilidades.append("impulsivas")

    if not registra:
        debilidades.append("sin_registro")

# Aquí consideramos “sin fondo” si es < 1 mes
    if fondo < 1:
        debilidades.append("sin_fondo")

 # Consideramos bajo ahorro si < 10%
    if ahorro < 10:
        debilidades.append("bajo_ahorro")

    return debilidades

# 3) Recomendaciones (V2)
def recomendaciones(persona: str, respuestas: Dict[str, Any]) -> Dict[str, Any]:
    """
    V2 recomendaciones basadas en tus notas de educacion financiera:
    - Pagate a ti primero / Ahorra 10–20%
    - Regla 48h para compras
    - 2 preguntas antes de gastar
    - Cuentas con destinos (10% juego, 10% libertad financiera, etc.)
    - Efecto compuesto: pequeñas decisiones + constancia + tiempo
    """
 # Primero detectamos debilidades para enfoque personalizado
    deb = detectar_debilidades(respuestas)

# Reglas por persona
    por_persona: Dict[str, Dict[str, List[str]]] = {
        "Comprador impulsivo": {
            "acciones_inmediatas": [
                "Aplica la regla de las 48 horas: no compres nada mayor a X monto sin dejar pasar 2 días.",
                "Antes de comprar hazte 2 preguntas: 1) ¿Esto me hace mas rico o mas pobre? 2) ¿Lo quiero de verdad o solo para sentirme mejor?",
                "Paga en efectivo siempre que puedas: duele más entregar billetes que deslizar la tarjeta.",
            ],
            "plan_7_dias": [
                "Día 1: Anota TODO lo que gastas (aunque sea en la app de notas).",
                "Día 2: Identifica 3 gastos 100% emocionales y elimínalos esta semana.",
                "Día 3: Pon un tope de gasto ‘por antojo’ y respétalo.",
                "Día 4: Activa la regla de 48h en compras online/carrito.",
                "Día 5: Revisa tu lista de gastos y marca cuáles te acercan o alejan de tus metas.",
                "Día 6: Repite las 2 preguntas antes de cualquier gasto no esencial.",
                "Día 7: Mira cuánto habrías gastado sin control y cuánto te ahorraste.",
            ],
            "plan_30_dias": [
                "Define un % fijo para ahorro (mínimo 10%) y pásalo a otra cuenta al cobrar.",
                "Empieza a construir un fondo de emergencia: meta inicial = 1 mes de gastos básicos.",
                "Elige 1 meta clara (deuda, viaje, inversión inicial) y destina parte del ahorro directo a esa meta.",
            ],
        },
        "Ahorrador disciplinado": {
            "acciones_inmediatas": [
                "Formaliza ‘págate a ti primero’: separa al menos el 10% de tu ingreso apenas cae.",
                "Revisa tus gastos y elimina 1 suscripción o gasto que ya no tenga sentido.",
                "Define por escrito tu meta principal (ej. fondo 3 meses / primera inversión / salir de deuda concreta).",
            ],
            "plan_7_dias": [
                "Día 1: Haz un resumen simple: ingresos, gastos fijos, gastos variables.",
                "Día 2: Ajusta tu % de ahorro y deja un monto definido para ‘jugar y divertirse’ (10%).",
                "Día 3: Abre (o etiqueta) una cuenta para ‘libertad financiera’ (10% cuando se pueda).",
                "Día 4: Identifica deudas caras y planea adelantarlas con parte de tus excedentes.",
                "Día 5: Revisa si tus gastos reflejan lo que de verdad te importa.",
                "Día 6: Ajusta topes de gasto por categoría (hogar, comida, ocio).",
                "Día 7: Evalúa la semana: ¿qué hábito te dio más control? Duplícalo la próxima.",
            ],
            "plan_30_dias": [
                "Apunta a ahorrar entre 10–20% de tu ingreso total.",
                "Logra un primer hito de fondo de emergencia (1 mes de gastos básicos).",
                "Aprende 1 cosa nueva de educación financiera por semana (libro, podcast, artículo) y aplícala.",
            ],
        },
        "Genio financiero": {
            "acciones_inmediatas": [
                "Pon por escrito tus porcentajes objetivo: necesidades, juego, libertad financiera, largo plazo, donativos.",
                "Revisa comisiones e impuestos de tus productos actuales y elimina lo que drene más de lo que aporta.",
                "Elige 1 vehículo de inversión simple (ej. fondo indexado de bajo costo) y define un monto mensual automático.",
            ],
            "plan_7_dias": [
                "Día 1: Haz un miniestado financiero personal (activos, pasivos, ingresos, gastos).",
                "Día 2: Clasifica tus gastos entre déficit (recorte) y excedente (para invertir).",
                "Día 3: Ajusta tu presupuesto para que exista excedente INTENCIONAL cada mes.",
                "Día 4: Define tu mezcla entre ingreso ganado, de portafolio y pasivo a largo plazo.",
                "Día 5: Revisa si tus decisiones siguen el efecto compuesto: pequeñas mejoras + constancia.",
                "Día 6: Evalúa riesgos y seguros (protege lo que ya construiste).",
                "Día 7: Documenta aprendizajes y decide 1 mejora para el próximo mes.",
            ],
            "plan_30_dias": [
                "Consolida un fondo de emergencia de al menos 1–3 meses.",
                "Arranca o refuerza una estrategia de inversión diversificada enfocada en el largo plazo.",
                "Crea un espacio semanal fijo para revisar números (ej. domingo 20 minutos) y tomar decisiones frías.",
            ],
        },
        "Jefe de jefes": {
            "acciones_inmediatas": [
                "Alinea tus decisiones de dinero con tu ‘para qué’ profundo (no solo con el número).",
                "Define 1 gran objetivo (ej. libertad financiera X año) y 2 métricas que vas a monitorear.",
                "Sistema: documenta tu flujo de dinero (qué entra, qué sale, qué construye activos).",
            ],
            "plan_7_dias": [
                "Día 1: Revisa si tu tiempo está alineado con producir, proteger, presupuestar, apalancar y aprender.",
                "Día 2: Pregunta: ¿estoy construyendo activos o solo sosteniendo gastos bonitos?",
                "Día 3: Ajusta tus flujos para que los pasivos se paguen con activos, no con salario.",
                "Día 4: Diseña 1 sistema de ingreso adicional (negocio, proyecto, skill).",
                "Día 5: Evalúa tu círculo: ¿con quién hablas de dinero y qué mentalidad traen?",
                "Día 6: Ajusta tu plan según tu energía, no según modas.",
                "Día 7: Revisa si lo que estás haciendo te acerca a la vida que quieres, no solo al número que quieres.",
            ],
            "plan_30_dias": [
                "Refuerza al menos 1 activo real (negocio, bienes raíces, activos en papel, propiedad intelectual).",
                "Define un plan anual: metas, hitos trimestrales y chequeos mensuales.",
                "Integra la educación financiera como hábito estable, no como ‘racha’.",
            ],
        },
    }

# Si llega una persona desconocida, caemos a "Ahorrador disciplinado"
    bloque = por_persona.get(persona, por_persona["Ahorrador disciplinado"])

# Principios generales que aplican para todos
    principios: List[str] = [
        "Págate a ti primero: reserva una parte para ti antes de pagar a otros.",
        "Pequeñas elecciones acertadas + constancia + tiempo = diferencia radical (efecto compuesto).",
        "Antes de gastar pregúntate: ¿esto me hace más rico o más pobre? ¿Lo quiero de verdad o solo para sentirme mejor?",
        "Nunca tomes decisiones de dinero importantes desde la emoción del momento.",
        "Usa el dinero como herramienta para la vida que quieres, no como medidor de tu valor.",
    ]

# Enfoque personalizado segun debilidades detectadas
    enfoque: List[str] = []
    if "impulsivas" in deb:
        enfoque.append("Tu punto débil son las compras impulsivas: aplica la regla de 48h y las 2 preguntas antes de gastar.")
    if "sin_registro" in deb:
        enfoque.append("No estás registrando tus gastos: 7 días de registro total te van a abrir los ojos.")
    if "sin_fondo" in deb:
        enfoque.append("No tienes fondo de emergencia: meta mínima, 1 mes de gastos básicos lo antes posible.")
    if "bajo_ahorro" in deb:
        enfoque.append("Tu nivel de ahorro es bajo: empieza con 5–10% y ve subiendo en cuanto puedas.")

 # Si no se detectó nada, lo dejamos en optimizacion
    if not enfoque:
        enfoque.append("No se detectan puntos débiles críticos: ahora toca optimizar y sostener lo que ya haces bien.")

    return {
        "acciones_inmediatas": bloque["acciones_inmediatas"],
        "plan_7_dias": bloque["plan_7_dias"],
        "plan_30_dias": bloque["plan_30_dias"],
        "principios": principios,
        "enfoque": enfoque,
    }
