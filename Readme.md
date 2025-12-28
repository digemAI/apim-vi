# APIM VI — Test Financiero Inteligente 💸🤖
Un mini test financiero hecho con Python y Streamlit, que clasifica tu perfil y te da planes accionables.
Incluye un “Dojo” (demo de red neuronal básica con NumPy) para mostrar conceptos de redes neuronales desde código.

# ¿Qué hace hoy?
- Captura respuestas (hábitos financieros)
- Clasifica tu perfil (v1)
- Muestra:
  - 3 acciones para hoy
  - Plan 7 días
  - Plan 30 días
  - (Opcional) principios base

# Toques de IA (Dojo)
Hoy el proyecto incluye un “Dojo” de red neuronal sencilla hecha con NumPy:
- Capas densas (Dense) (conectan todas tus entradas con varias “neuronas” para combinar señales y sacar una salida)
- Pesos + sesgos (weights + bias) para ajustar decisiones
- Activación ReLU (filtra lo que no sirve)
- Forward pass (procesa tus respuestas y genera una salida)
- Un “medidor de qué tan cerca estuvo” la salida (para explicar el concepto de mejora futura)

No entrena aún. Es una demo

# ¿Qué será después con PyTorch?
Aquí es cuando "Dojo" cobra vida: una red que sí aprende con la práctica.

- Backpropagation (backward) *(la red revisa en qué parte del camino se equivocó y qué necesita ajustar.)

- Loss real (una medida clara de qué tan lejos estuvo del resultado ideal.)

- Optimizer (el entrenador que ajusta los pesos):
    Adam - ajusta de forma simple y directa, paso a paso.
    SGD - ajusta de manera más fina y estable, usando “memoria” del recorrido.

- Historial de respuestas (para que se adapte a la persona que lo usa y mejore con el tiempo)

En palabras simples: con PyTorch, el Dojo deja de ser un póster bonito y se vuelve película

# Como correrlo en tu terminal 
  - Clonas el repositorio con tu maquina
  - Entra a la carpeta del proyecto (cd apim-vi)
  - Crea un entorno virtua
  - Activa tu entorno virtual
  - Instala las dependencias
  - Ejecuta la aplicación (streamlit run app.py)


