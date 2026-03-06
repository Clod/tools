# Regla de Consentimiento Explícito (Acciones de Disco)

1. El agente de IA **NO TIENE PERMITIDO** crear, modificar o borrar archivos en el disco de forma autónoma a menos que el usuario lo haya solicitado explícita y directamente en su último prompt (ej. "Crea este archivo", "Guarda estos cambios", "Aplica el código").
2. Si la IA considera que un archivo nuevo sería útil (como un documento de reglas, un script o un archivo markdown), primero **DEBE explicar su razonamiento y pedir autorización** clara al usuario ("¿Te parece bien si creo el archivo X con este contenido?").
3. Solo se procederá a ejecutar comandos bash (`cp`, `mv`, `echo`, `mkdir`, etc.) o usar herramientas de escritura/edición persistente en disco **después** de obtener un mensaje afirmativo del usuario. 
4. Si el usuario cancela o rechaza la ejecución de un comando en la terminal, la IA debe detener la tarea destructiva y consultar al usuario cómo prefiere proceder.
