# APIM VI — Test Financiero Inteligente 💸🤖
Un mini test financiero hecho con Python, Streamlit, Pytorch que clasifica tu perfil y te da planes accionables.
El sistema principal corre, guarda datos y aprende.
La sección “Dojo” incluye elementos demo solo para explicar el proceso.

# ¿Qué hace hoy?
- Captura hábitos financieros del usuario (ahorro, compras impulsivas, registro de gastos, fondo de emergencia).
- Score APIM (V2): se calcula con reglas a partir de tus hábitos (más score = mejores hábitos).
- En la seccion toques de ia(dojo), saldran dos datos:
   * Señal del Dojo (demo): salida numérica interna de la red. No es una decisión.
   * Medidor de cercanía (demo): indica qué tan bien respondió .
- Muestra planes accionables (3 acciones hoy, plan de 7 días, 30 días).
- Guarda historial completo de ejecuciones y feedback del usuario.
- Ejecuta un modelo PyTorch (V3) en shadow mode:
  - Predice sin afectar la clasificación principal.
  - Guarda probabilidades, confidence y errores.
- Calcula métricas offline para comparar V2 vs V3.

# Toques de IA (Dojo)
- Demo (NumPy)
- Dense (capas densas): combinan las entradas (ahorro, impulsivas, registro, fondo) para producir una salida interna.
- ReLU (activación): recorta valores negativos a 0 para dejar pasar solo señal útil.
- Forward pass: la red procesa las entradas y genera una salida numérica.
- Señal del Dojo (demo): la salida interna de la red (no decide tu perfil).
- Medidor de cercanía (demo): un número de referencia para visualizar “qué tan alineada” estuvo la salida (menor = mejor).

# V3 (PyTorch, shadow mode)
- Dataset + DataLoader: convierten el historial en batches para entrenamiento.
- Red (nn.Linear + ReLU): arquitectura simple para clasificar perfiles.
- Loss (CrossEntropyLoss): mide qué tan mal predice.
- Optimizer (Adam): ajusta pesos para mejorar con el tiempo.
- Softmax + confidence: convierte la salida en probabilidades y nivel de confianza.
- Shadow mode: V3 predice y se registra, pero no cambia el resultado final (V2 decide).

# Como correrlo en tu terminal 
  - Clonas el repositorio con tu maquina
  - Entra a la carpeta del proyecto (cd apim-vi)
  - Crea un entorno virtual
  - Activa tu entorno virtual
  - Instala las dependencias
  - Ejecuta la aplicación (streamlit run app.py)
