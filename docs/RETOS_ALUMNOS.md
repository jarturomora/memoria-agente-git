# Retos para casa

1. **Personalización persistente**. Guarda una preferencia ficticia con `remember`, cierra Python y vuelve a ejecutar `ask`. Comprueba en Kibana que el recuerdo se ha guardado en `agent-memories`.
2. **Derecho a corregir**. Encuentra el ID del recuerdo con `memories`; elimínalo con `forget ID`; comprueba que la siguiente consulta ya no lo recupera.
3. **Búsqueda vs memoria**. Compara los documentos en `progit` con los recuerdos en `agent-memories`. Identifica qué contenido procede del libro y qué contenido procede de las interacciones del estudiante.
4. **Avanzado**. Incorpora embeddings o `semantic_text` y compara relevancia para una consulta reformulada. Documenta requisitos y costes del modelo de inferencia elegido.
5. **Avanzado**. Implementa políticas de caducidad, actualización y consentimiento de recuerdos.

No almacenes datos reales de estudiantes en el ejercicio. Evalúa la procedencia de los textos: los fragmentos documentales no son instrucciones que el agente deba obedecer.
