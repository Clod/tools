# Gestión de Constantes y Traducciones de Sentiance

Este directorio contiene herramientas para traducir las constantes técnicas del SDK de Sentiance al castellano y asegurar que el diccionario local esté sincronizado con la última documentación oficial.

## Contenido del Directorio

### 1. Diccionario de Traducción (`traductor_constantes.js`)
Es el archivo principal que centraliza todas las traducciones de la plataforma.
*   **Qué contiene**:
    *   Diccionarios para: `TransportMode`, `EventType`, `OccupantRole`, `SemanticTime`, `VenueType`, `SegmentCategory`, `DetectionStatus`, entre otros.
    *   **Funciones Helper**: Incluye funciones como `translateSentianceConstant`, `translateEvent` y `translateUserContext` para facilitar la traducción de objetos complejos devueltos por el SDK.
*   **Propósito**: Se utiliza para mostrar información amigable al usuario final en lugar de términos técnicos en inglés (ej: "Bicicleta" en lugar de `BICYCLE`).

### 2. Validador de Constantes (`find_missing_constants.js`)
Un script de utilidad para el mantenimiento del diccionario.
*   **Qué hace**: 
    1. Escanea el archivo `traductor_constantes.js` para extraer todas las constantes soportadas actualmente.
    2. Analiza los archivos markdown en la carpeta de documentación (`scraped_site`).
    3. Busca palabras en mayúsculas (estilo constantes) en los documentos y las compara con el diccionario local.
    4. Reporta cualquier constante encontrada en la documentación que no esté definida en el traductor.
*   **Propósito**: Asegurar que no nos falte ninguna traducción de nuevos segmentos o modos de transporte que Sentiance haya añadido recientemente a su SDK.

## Instrucciones de Ejecución

### Cómo verificar si faltan constantes
Para ejecutar el script de validación, necesitas tener Node.js instalado:

```bash
node constantes/find_missing_constants.js
```

### Cómo añadir nuevas traducciones
Si el validador reporta constantes faltantes:
1. Abre `traductor_constantes.js`.
2. Busca la categoría correspondiente (ej: `SEGMENT_TYPE_TRANSLATIONS`).
3. Añade la nueva constante y su traducción siguiendo el formato existente.
4. Vuelve a ejecutar el validador para confirmar que ya no hay discrepancias.

## Ejemplo de Integración en Código

```javascript
import { translateUserContext } from './constantes/traductor_constantes.js';

// ... obtener userContext del SDK ...
const contextoEnCastellano = translateUserContext(userContext);
console.log(contextoEnCastellano.semanticTime); // "Media mañana" en lugar de "LATE_MORNING"
```
