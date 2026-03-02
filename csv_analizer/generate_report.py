import json
import os

with open('../ike_tables.json', 'r', encoding='utf-8') as f:
    ike_schema = json.load(f)

report_md = '# Comparación: Documento IKE vs Datos en Sentiance\n\n'
report_md += 'Este documento detalla qué información requerida por el **Documento de Exportación de Datos IKE** se encuentra actualmente disponible en los payloads que envía Sentiance.\n\n'
report_md += '> [!NOTE]\n> Entendemos que el Documento IKE es agnóstico al motor de BD. Sin embargo, Sentiance estructura la información a su propia manera (a través de los objetos `transportEvent` o `safetyScores`). Este reporte busca mapear los conceptos IKE contra los datos reales emitidos por el SDK Móvil de Sentiance para identificar vacíos o discrepancias estructurales.\n\n'

mapping_dict = {
    'modo_transporte': 'transportMode',
    'comienzo': 'startTime / startTimeEpoch',
    'fin': 'endTime / endTimeEpoch',
    'duracion': 'durationInSeconds',
    'velocidad_maxima': 'topSpeed',
    'distancia_m': 'distance',
    'polyline': 'waypoints (array)', 
    'puntos_recorrido': 'waypoints',
    'ubicacion_inicio': 'startLocation / waypoints[0]',
    'ubicacion_fin': 'endLocation / waypoints[-1]',
    'maxima_velocidad': 'topSpeed',
    'ocupante': 'occupantRole',
    'legal': 'legalScore',
    'suavidad': 'smoothScore',
    'atencion': 'focusScore',
    'promedio': 'overallScore',
    'concentracion': 'callWhileMovingScore',
    'aceleracion_fuerte': 'harshAccelerationScore / hardAccelerationPenalty',
    'frenado_fuerte': 'harshBrakingScore / hardBrakingPenalty',
    'curvas_fuertes': 'harshTurningScore / harshTurnPenalty',
    'anticipacion': 'anticipationScore',
    'celular_fijo': 'phoneHandlingScore',
    'eventos_fuertes': 'speedingScore / speedingPenalty',
    'aceleracion': 'hardAccelerations (Lista)',
    'frenado': 'hardBrakings (Lista)',
    'curvas': 'harshTurns (Lista)',
    'llamados': 'phoneCalls (Lista)',
    'pantalla': 'screenTouches (Lista)',
    'exceso_de_velocid ad': 'speeding (Lista)'
}

for table_def in ike_schema:
    title = table_def['title']
    report_md += f'## 📋 {title}\n\n'
    report_md += '| Campo IKE | Equivalente Sentiance | Estado | Observaciones |\n'
    report_md += '|---|---|---|---|\n'
    
    for row in table_def['rows'][1:]:
        col_name = row[0].strip()
        if col_name == '' and len(row) > 1: col_name = row[1].strip()
        if not col_name: continue
        
        sent_key = mapping_dict.get(col_name, col_name)
        
        # Hardcoded logic based on the payload analysis
        if col_name in ['usuario', 'viaje']:
            status = '✅ Disponible'
            loc = f'Se mapea a `user_id` / `trip_id` en la BD y payload.'
        elif col_name == 'correlacion':
            status = '⚠️ Diferente'
            loc = 'Sentiance no utiliza ID correlaciones por métrica; agrupa todos los puntajes bajo un mismo `tripId`.'
        elif col_name == 'metrica':
            status = '⚠️ Diferente'
            loc = 'El SDK envía un objeto unificado `safetyScores` con todos los puntajes (ej: `legalScore: 0.8`), no filas de llave-valor separadas.'
        elif col_name in ['aceleracion', 'frenado', 'curvas', 'celular_fijo', 'llamados', 'pantalla', 'exceso_de_velocid ad'] and ('EVENTOS' in title):
            status = '❌ No Disponible por Defecto'
            loc = 'El SDK insertado en la app transmite las penalizaciones/scores globales numéricas, **pero NO la lista detallada de coordenadas (lat/lon) por cada evento brusco** dentro del payload estándar de viaje. Requeriría habilitar endpoints adicionales de la API de Sentiance ("Detailed Trip Events").'
        elif col_name == 'polyline':
            status = '⚠️ Requiere Transformación'
            loc = 'Sentiance entrega la lista de `waypoints` (coordenadas brutas). El string codificado de polyline exigido por IKE debe generarse en backend interconectando estos puntos.'
        elif col_name in ['ubicacion_inicio', 'ubicacion_fin']:
            status = '✅ Derivable'
            loc = 'Se puede interpolar leyendo el primer y último objeto del array de `waypoints` si no viene el campo explícito.'
        elif col_name == 'puntaje' and 'PUNTAJES PK' in title:
             status = '⚠️ Diferente'
             loc = 'Los valores numéricos vienen estructurados dentro del objeto JSON `safetyScores`.'
        elif col_name == 'actualizacion':
             status = '✅ Disponible'
             loc = 'Asignable vía `lastUpdateTimeEpoch` del payload original.'
        elif 'Score' in sent_key or 'Penalty' in sent_key or sent_key in ['transportMode', 'startTimeEpoch', 'endTimeEpoch', 'durationInSeconds', 'occupantRole', 'distance', 'waypoints', 'topSpeed']:
             status = '✅ Disponible'
             loc = 'Se documenta de forma nativa en el JSON regular del viaje (en `transportEvent` o `safetyScores`).'
        else:
             status = '❓ A Revisar'
             loc = f'No se ha observado consistentemente en las payloads extraídas; depende de configuraciones específicas del SDK para incluir `{sent_key}`.'
                
        report_md += f'| `{col_name}` | `{sent_key}` | {status} | {loc} |\n'
    report_md += '\n'

output_path = '/Users/claudiograsso/Documents/Sentiance/tools/Reporte_IKE_vs_Sentiance.md'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(report_md)
print(f'Generated Clean Report: {output_path}')
