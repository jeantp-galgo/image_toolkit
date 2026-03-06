Analiza estas imágenes de una motocicleta para un marketplace.

---

## SISTEMA DE REFERENCIA: EL ENCUADRE

Para clasificar el ángulo, usa siempre la posición de dos elementos dentro del encuadre (lo que se ve en la imagen):
- **FARO**: la óptica delantera / luz frontal de la moto.
- **COLA**: la parte trasera, donde está la luz roja trasera y el asiento.

Nunca uses "izquierdo/derecho de la moto" como referencia — usa siempre izquierdo/derecho del ENCUADRE.

El espectro de ángulos posibles, de frente a trasera:

  front → 3q-front-left / 3q-front-right → side-left / side-right → 3q-rear → rear

---

## DESCRIPCIÓN DE CADA ÁNGULO

Usa EXACTAMENTE uno de estos valores para "angle":

### "3q-front-right" — ÁNGULO PRINCIPAL DEL MARKETPLACE

VERIFICACIÓN ELIMINATORIA — haz esta pregunta ANTES de cualquier otra cosa:
  ¿El faro está en el lado DERECHO del encuadre? Si la respuesta es NO → STOP. No es "3q-front-right".
  Si el faro está en el lado IZQUIERDO del encuadre, es "3q-front-left" o "front", NUNCA "3q-front-right".

El faro está en el lado DERECHO del encuadre y se ve ligeramente de frente (no está pegado al borde derecho — está algo hacia el centro, con parte de la careta frontal visible). El cuerpo completo de la moto se extiende hacia la izquierda del encuadre.

Características visuales — TODAS deben cumplirse:
  1. El faro está en el tercio DERECHO del encuadre, visible de frente (se le ve la cara).
  2. El cuerpo lateral de la moto ocupa la mayor parte del encuadre (eje horizontal visible).
  3. La rueda trasera es claramente visible en el lado izquierdo del encuadre.
  4. La COLA (luz trasera roja) NO domina ni se proyecta hacia el espectador.
  5. La perspectiva frontal es leve: si el faro y la horquilla delantera ocupan más del 35% del ancho total de la moto en la imagen, el ángulo es demasiado frontal — usa "front".

Distinción clave con "side-left":
  - En "3q-front-right": el faro está algo hacia el centro del encuadre y se le ve la cara (la careta frontal es visible).
  - En "side-left": el faro está pegado al borde derecho del encuadre y apenas se le ve la cara — es puro perfil.

### "3q-front-left"
Igual que "3q-front-right" pero en espejo: el faro está en el tercio IZQUIERDO del encuadre con perspectiva frontal leve, y el cuerpo se extiende hacia la derecha.
VERIFICACIÓN: Si el faro está en el lado IZQUIERDO del encuadre y se ve la careta frontal → es "3q-front-left", NUNCA "3q-front-right".
Orientación incorrecta para el marketplace.

### "side-left"
El faro está en el borde DERECHO del encuadre (o muy cerca). La cola está en el borde IZQUIERDO. El eje de la moto es horizontal. El cuerpo de la moto llena el encuadre de lado a lado.

Diagnóstico rápido:
  - ¿El faro está pegado al borde derecho del encuadre? → Candidato a side-left.
  - ¿La cola NO se proyecta hacia el espectador (no hay profundidad trasera visible)? → Confirma side-left.
  - ¿Hay leve inclinación y se ve algo del motor/escape desde el costado? → Aún puede ser side-left si la cola no se abre hacia el espectador.

Nota: imágenes de carrusel 360 raramente son perfectamente perpendiculares. Si el faro está al borde derecho y la cola al borde izquierdo aunque se vea ligeramente inclinado, es side-left.

### "side-right"
Igual que "side-left" pero en espejo: el faro está en el borde IZQUIERDO del encuadre y la cola en el borde DERECHO. El eje de la moto es horizontal.

Diagnóstico rápido:
  - ¿El faro está pegado al borde IZQUIERDO del encuadre? → Candidato a side-right.
  - ¿La cola NO se proyecta hacia el espectador? → Confirma side-right.

### "3q-rear"
La COLA (luz trasera roja, guardabarro trasero) se proyecta visiblemente hacia el espectador — hay profundidad trasera visible. El faro puede asomarse en un extremo del encuadre pero no domina. Se ve la zona trasera de la moto "abriéndose" hacia la cámara.

Distinción clave con "side-left" / "side-right":
  - En side: la cola está de LADO, al borde del encuadre, sin proyectarse hacia el espectador.
  - En 3q-rear: la cola se ABRE hacia el espectador — ves la parte interna del guardabarro trasero, el escape de frente, o la luz trasera claramente iluminando hacia la cámara.

### "front"
El faro está CENTRADO en el encuadre (o casi centrado). Las dos ruedas se superponen visualmente o la rueda trasera no se ve. El frente de la moto domina toda la imagen.

### "rear"
La luz trasera roja está CENTRADA en el encuadre. Las dos ruedas se superponen o la delantera no se ve. La parte trasera domina toda la imagen.

### "detail"
Acercamiento (close-up) a una parte específica: motor, tablero, llanta, manubrio, escape, etc. La moto completa NO está en el encuadre.

### "other"
No encaja en ninguna categoría anterior.

---

## CAMPOS A DEVOLVER POR IMAGEN

Para CADA imagen, devuelve los campos EN ESTE ORDEN:
- "reasoning": antes de clasificar, escribe UNA frase que indique explícitamente en qué lado del encuadre está el FARO. Esto determina el ángulo. Ejemplo: "Faro en borde DERECHO del encuadre, cola en borde izquierdo." — Si el faro está a la IZQUIERDA, el ángulo NO puede ser 3q-front-right.
- "filename": nombre del archivo
- "angle": uno de los valores definidos arriba (exactamente como está escrito)
- "quality_score": entero del 1 al 10, evaluando: nitidez, centrado de la moto, iluminación uniforme, moto completa dentro del encuadre (sin cortes en ruedas o extremos)
- "is_recommended": true o false — si esta imagen aporta valor único al listing

---

## CRITERIOS PARA is_recommended

- "3q-front-right": SIEMPRE true. Pueden existir varias (distintos colores del mismo modelo) y todas se recomiendan.
- "3q-front-left": SIEMPRE false. Orientación incorrecta para el marketplace.
- "side-left" y "side-right" en conjunto: recomienda MÁXIMO UNA imagen entre ambos tipos.
  Elige la de mayor quality_score. En caso de empate, prefiere la más perpendicular (faro más pegado al borde del encuadre).
  Razón: el comprador solo necesita ver un perfil lateral.
- "3q-rear": MÁXIMO UNA, la de mayor quality_score.
- "front" y "rear": MÁXIMO UNA de cada tipo, solo si aporta información visual que las otras vistas no cubren.
- "detail": MÁXIMO DOS, solo si son nítidas y muestran partes distintas de la moto.
- Ante la duda entre dos imágenes similares del mismo ángulo, SIEMPRE descarta la de menor quality_score.
- El listing ideal tiene: todas las 3q-front-right + 1 side + 1 3q-rear. Máximo 6-7 imágenes totales recomendadas.

---

## FORMATO DE RESPUESTA

Responde SOLO con un JSON array. Sin markdown, sin texto adicional, sin explicaciones.

Ejemplo:
[{"reasoning": "Faro en borde DERECHO del encuadre, cola en borde izquierdo, vista lateral con leve perspectiva frontal.", "filename": "img1.jpg", "angle": "3q-front-right", "quality_score": 9, "is_recommended": true}]
