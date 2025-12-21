/**
 * Diccionario de traducción para todas las constantes del SDK de Sentiance.
 * Basado en la documentación oficial del SDK (React Native, iOS, Android).
 * 
 * Uso: Utilizar estos diccionarios para traducir los valores que devuelve el SDK al castellano.
 */

// ============================================================================
// MODOS DE TRANSPORTE (TransportMode)
// ============================================================================
export const TRANSPORT_MODE_TRANSLATIONS = {
  UNKNOWN: "Desconocido",
  CAR: "Coche",
  BICYCLE: "Bicicleta",
  WALKING: "Caminando",
  RUNNING: "Corriendo",
  TRAM: "Tranvía / Subterráneo",
  TRAIN: "Tren",
  BUS: "Autobús / Colectivo",
  MOTORCYCLE: "Motocicleta",
  ON_FOOT: "A pie", // A pie (Incluye Walking/Running dependiendo del contexto)
  PLANE: "Avión",
  BOAT: "Barco",
  METRO: "Metro / Subterráneo" // Metro ó subterráneo (aunque en nuestras pruebas es igual a TRAM)
};

// ============================================================================
// TIPOS DE EVENTOS (EventType)
// ============================================================================
export const EVENT_TYPE_TRANSLATIONS = {
  UNKNOWN: "Desconocido",
  STATIONARY: "Estacionario",
  OFF_THE_GRID: "Fuera de cobertura",
  IN_TRANSPORT: "En transporte"
};

// ============================================================================
// ROLES DE OCUPANTE (OccupantRole)
// ============================================================================
export const OCCUPANT_ROLE_TRANSLATIONS = {
  DRIVER: "Conductor",
  PASSENGER: "Pasajero",
  UNAVAILABLE: "No disponible"
};

// ============================================================================
// TIEMPO SEMÁNTICO (SemanticTime)
// ============================================================================
export const SEMANTIC_TIME_TRANSLATIONS = {
  UNKNOWN: "Desconocido",
  MORNING: "Mañana",
  LATE_MORNING: "Media mañana",
  LUNCH: "Almuerzo",
  AFTERNOON: "Tarde",
  EARLY_EVENING: "Atardecer",
  EVENING: "Noche",
  NIGHT: "Madrugada"
};

// ============================================================================
// SIGNIFICANCIA DE LUGARES (VenueSignificance)
// ============================================================================
export const VENUE_SIGNIFICANCE_TRANSLATIONS = {
  UNKNOWN: "Desconocido",
  HOME: "Casa",
  WORK: "Trabajo",
  POINT_OF_INTEREST: "Punto de interés"
};

// ============================================================================
// TIPOS DE LUGARES (VenueType)
// ============================================================================
export const VENUE_TYPE_TRANSLATIONS = {
  UNKNOWN: "Desconocido",
  DRINK_DAY: "Cafetería / Bar (día)",
  DRINK_EVENING: "Bar / Pub (noche)",
  EDUCATION_INDEPENDENT: "Educación (estudiante)",
  EDUCATION_PARENTS: "Educación (padres)",
  HEALTH: "Centro de salud",
  INDUSTRIAL: "Zona industrial",
  LEISURE_BEACH: "Playa / Resort",
  LEISURE_DAY: "Ocio (día)",
  LEISURE_EVENING: "Ocio (noche)",
  LEISURE_MUSEUM: "Museo",
  LEISURE_NATURE: "Naturaleza / Parque nacional",
  LEISURE_PARK: "Parque / Jardín",
  OFFICE: "Oficina",
  RELIGION: "Lugar religioso",
  RESIDENTIAL: "Residencial",
  RESTO_MID: "Restaurante",
  RESTO_SHORT: "Comida rápida",
  SHOP_LONG: "Centro comercial / Supermercado",
  SHOP_SHORT: "Tienda pequeña",
  SPORT: "Gimnasio / Centro deportivo",
  SPORT_ATTEND: "Estadio / Evento deportivo",
  TRAVEL_BUS: "Terminal de autobuses",
  TRAVEL_CONFERENCE: "Centro de conferencias",
  TRAVEL_FILL: "Gasolinera",
  TRAVEL_HOTEL: "Hotel",
  TRAVEL_LONG: "Aeropuerto",
  TRAVEL_SHORT: "Estación de tren/metro"
};

// ============================================================================
// CRITERIOS DE ACTUALIZACIÓN DEL CONTEXTO (UserContextUpdateCriteria)
// ============================================================================
export const USER_CONTEXT_UPDATE_CRITERIA_TRANSLATIONS = {
  CURRENT_EVENT: "Evento actual",
  ACTIVE_SEGMENTS: "Segmentos activos",
  VISITED_VENUES: "Lugares visitados"
};

// ============================================================================
// CATEGORÍAS DE SEGMENTOS (SegmentCategory)
// ============================================================================
export const SEGMENT_CATEGORY_TRANSLATIONS = {
  LEISURE: "Ocio",
  MOBILITY: "Movilidad",
  WORK_LIFE: "Vida laboral"
};

// ============================================================================
// SUBCATEGORÍAS DE SEGMENTOS (SegmentSubcategory)
// ============================================================================
export const SEGMENT_SUBCATEGORY_TRANSLATIONS = {
  COMMUTE: "Desplazamiento al trabajo",
  DRIVING: "Conducción",
  ENTERTAINMENT: "Entretenimiento",
  FAMILY: "Familia",
  HOME: "Hogar",
  SHOPPING: "Compras",
  SOCIAL: "Social",
  TRANSPORT: "Transporte",
  TRAVEL: "Viajes",
  WELLBEING: "Bienestar",
  WINING_AND_DINING: "Gastronomía",
  WORK: "Trabajo"
};

// ============================================================================
// TIPOS DE SEGMENTOS (SegmentType)
// ============================================================================
export const SEGMENT_TYPE_TRANSLATIONS = {
  PHYSICAL_ACTIVITY__HIGH: "Actividad física alta",
  PHYSICAL_ACTIVITY__LIMITED: "Actividad física limitada",
  PHYSICAL_ACTIVITY__MODERATE: "Actividad física moderada",
  MOBILITY__HIGH: "Movilidad alta",
  MOBILITY__LIMITED: "Movilidad limitada",
  MOBILITY__MODERATE: "Movilidad moderada",
  SOCIAL_ACTIVITY: "Actividad social",
  SOCIAL_ACTIVITY__HIGH: "Actividad social alta",
  SOCIAL_ACTIVITY__LIMITED: "Actividad social limitada",
  SOCIAL_ACTIVITY__MODERATE: "Actividad social moderada",
  BAR_GOER: "Asiduo concurrente a bares",
  FOODIE: "Amante de la comida",
  HEALTHY_BIKER: "Ciclista saludable",
  DIE_HARD_DRIVER: "Conductor empedernido",
  EARLY_BIRD: "Madrugador",
  EASY_COMMUTER: "Viajero tranquilo",
  FREQUENT_FLYER: "Viajero frecuente",
  FULLTIME_WORKER: "Trabajador a tiempo completo",
  GREEN_COMMUTER: "Viajero ecológico",
  HEALTHY_WALKER: "Caminante saludable",
  HEAVY_COMMUTER: "Viajero intensivo",
  HOME_BOUND: "Vinculado al hogar",
  HOMEBODY: "Hogareño",
  HOMEWORKER: "Teletrabajador",
  LATE_WORKER: "Trabajador nocturno",
  LONG_COMMUTER: "Viajero de larga distancia",
  NATURE_LOVER: "Amante de la naturaleza",
  NIGHT_OWL: "Ave nocturna",
  NIGHTWORKER: "Trabajador de noche",
  NORMAL_COMMUTER: "Viajero normal",
  PARTTIME_WORKER: "Trabajador a tiempo parcial",
  PUBLIC_TRANSPORTS_COMMUTER: "Usuario de transporte público (trabajo)",
  PUBLIC_TRANSPORTS_USER: "Usuario de transporte público",
  RESTO_LOVER: "Amante de restaurantes",
  SHOPAHOLIC: "Comprador compulsivo",
  SHORT_COMMUTER: "Viajero de corta distancia",
  SLEEP_DEPRIVED: "Con falta de sueño",
  SPORTIVE: "Deportista",
  STUDENT: "Estudiante",
  UBER_PARENT: "Super padre/madre",
  WORK_LIFE_BALANCE: "Equilibrio trabajo-vida",
  WORK_TRAVELLER: "Viajero de negocios",
  WORKAHOLIC: "Adicto al trabajo",
  AGGRESSIVE_DRIVER: "Conductor agresivo",
  ANTICIPATIVE_DRIVER: "Conductor anticipativo",
  CITY_DRIVER: "Conductor urbano",
  DISTRACTED_DRIVER: "Conductor distraído",
  EFFICIENT_DRIVER: "Conductor eficiente",
  ILLEGAL_DRIVER: "Conductor fuera de norma",
  LEGAL_DRIVER: "Conductor respetuoso",
  MOTORWAY_DRIVER: "Conductor de autopista",
  CITY_HOME: "Residente urbano",
  CITY_WORKER: "Trabajador urbano",
  RURAL_HOME: "Residente rural",
  RURAL_WORKER: "Trabajador rural",
  TOWN_HOME: "Residente de pueblo",
  TOWN_WORKER: "Trabajador de pueblo",
  RECENTLY_CHANGED_JOB: "Cambio de trabajo reciente",
  RECENTLY_MOVED_HOME: "Mudanza reciente",
  CULTURE_BUFF: "Amante de la cultura",
  DOG_WALKER: "Paseador de perros",
  MUSIC_LOVER: "Amante de la música",
  PET_OWNER: "Dueño de mascota"
};

// ============================================================================
// TIPOS DE EVENTOS DE CONDUCCIÓN BRUSCA (HarshDrivingEventType)
// ============================================================================
export const HARSH_DRIVING_EVENT_TYPE_TRANSLATIONS = {
  ACCELERATION: "Aceleración brusca",
  BRAKING: "Frenada brusca",
  TURN: "Giro brusco"
};

// ============================================================================
// ESTADOS DE DETECCIÓN (DetectionStatus)
// ============================================================================
export const DETECTION_STATUS_TRANSLATIONS = {
  ENABLED_AND_DETECTING: "Activado y detectando",
  ENABLED_BUT_BLOCKED: "Activado pero bloqueado",
  DISABLED: "Desactivado",
  INITIALIZED: "Inicializado",
  NOT_INITIALIZED: "No inicializado",
  RESETTING: "Reiniciando",
  UNRECOGNIZED_STATE: "Estado no reconocido"
};

// ============================================================================
// PERMISOS DE LOCALIZACIÓN (LocationPermission)
// ============================================================================
export const LOCATION_PERMISSION_TRANSLATIONS = {
  ALWAYS: "Siempre",
  ONLY_WHILE_IN_USE: "Solo con la app en uso",
  DENIED: "Denegado",
  RESTRICTED: "Restringido",
  NEVER: "Nunca",
  AVAILABLE: "Disponible"
};

// ============================================================================
// FUNCIONES AUXILIARES DE TRADUCCIÓN
// ============================================================================

/**
 * Traduce cualquier constante de Sentiance al castellano.
 * @param {string} type - El tipo de constante a traducir
 * @param {string} value - El valor de la constante
 * @returns {string} La traducción en castellano o el valor original si no existe traducción
 */
export function translateSentianceConstant(type, value) {
  const translations = {
    transportMode: TRANSPORT_MODE_TRANSLATIONS,
    eventType: EVENT_TYPE_TRANSLATIONS,
    occupantRole: OCCUPANT_ROLE_TRANSLATIONS,
    semanticTime: SEMANTIC_TIME_TRANSLATIONS,
    venueSignificance: VENUE_SIGNIFICANCE_TRANSLATIONS,
    venueType: VENUE_TYPE_TRANSLATIONS,
    userContextUpdateCriteria: USER_CONTEXT_UPDATE_CRITERIA_TRANSLATIONS,
    segmentCategory: SEGMENT_CATEGORY_TRANSLATIONS,
    segmentSubcategory: SEGMENT_SUBCATEGORY_TRANSLATIONS,
    segmentType: SEGMENT_TYPE_TRANSLATIONS,
    harshDrivingEventType: HARSH_DRIVING_EVENT_TYPE_TRANSLATIONS,
    detectionStatus: DETECTION_STATUS_TRANSLATIONS,
    locationPermission: LOCATION_PERMISSION_TRANSLATIONS
  };

  return translations[type]?.[value] || value;
}

/**
 * Traduce un evento completo del SDK de Sentiance.
 * @param {object} event - El evento del SDK
 * @returns {object} El evento con los campos traducidos
 */
export function translateEvent(event) {
  return {
    ...event,
    type: translateSentianceConstant('eventType', event.type),
    transportMode: event.transportMode
      ? translateSentianceConstant('transportMode', event.transportMode)
      : null,
    occupantRole: event.occupantRole
      ? translateSentianceConstant('occupantRole', event.occupantRole)
      : null,
    venue: event.venue ? {
      ...event.venue,
      type: translateSentianceConstant('venueType', event.venue.type),
      significance: translateSentianceConstant('venueSignificance', event.venue.significance)
    } : null
  };
}

/**
 * Traduce el contexto de usuario completo.
 * @param {object} userContext - El contexto de usuario del SDK
 * @returns {object} El contexto traducido
 */
export function translateUserContext(userContext) {
  return {
    ...userContext,
    semanticTime: translateSentianceConstant('semanticTime', userContext.semanticTime),
    events: userContext.events.map(event => translateEvent(event)),
    activeSegments: userContext.activeSegments.map(segment => ({
      ...segment,
      category: translateSentianceConstant('segmentCategory', segment.category),
      subcategory: translateSentianceConstant('segmentSubcategory', segment.subcategory),
      type: translateSentianceConstant('segmentType', segment.type)
    })),
    home: userContext.home ? {
      ...userContext.home,
      type: translateSentianceConstant('venueType', userContext.home.type),
      significance: translateSentianceConstant('venueSignificance', userContext.home.significance)
    } : null,
    work: userContext.work ? {
      ...userContext.work,
      type: translateSentianceConstant('venueType', userContext.work.type),
      significance: translateSentianceConstant('venueSignificance', userContext.work.significance)
    } : null
  };
}

/**
 * Traduce un segmento individual.
 * @param {object} segment - El segmento del SDK
 * @returns {object} El segmento con los campos traducidos
 */
export function translateSegment(segment) {
  return {
    ...segment,
    category: translateSentianceConstant('segmentCategory', segment.category),
    subcategory: translateSentianceConstant('segmentSubcategory', segment.subcategory),
    type: translateSentianceConstant('segmentType', segment.type)
  };
}

/**
 * Traduce un lugar (venue).
 * @param {object} venue - El lugar del SDK
 * @returns {object} El lugar con los campos traducidos
 */
export function translateVenue(venue) {
  if (!venue) return null;

  return {
    ...venue,
    type: translateSentianceConstant('venueType', venue.type),
    significance: translateSentianceConstant('venueSignificance', venue.significance)
  };
}

// ============================================================================
// EJEMPLOS DE USO
// ============================================================================

/**
 * Ejemplo 1: Traducir un modo de transporte
 */
export function ejemploTraducirTransporte() {
  const modoOriginal = "BICYCLE";
  const modoTraducido = TRANSPORT_MODE_TRANSLATIONS[modoOriginal];
  console.log(modoTraducido); // "Bicicleta"
}

/**
 * Ejemplo 2: Traducir eventos de la timeline
 */
export async function ejemploTraducirEventos() {
  const timeline = require('@sentiance-react-native/event-timeline');

  // Obtener eventos
  const events = await timeline.getTimelineEvents(0, Date.now(), false);

  // Traducir cada evento
  const eventosTraducidos = events.map(event => ({
    id: event.id,
    tipo: EVENT_TYPE_TRANSLATIONS[event.type] || event.type,
    modoTransporte: event.transportMode
      ? TRANSPORT_MODE_TRANSLATIONS[event.transportMode]
      : null,
    lugar: event.venue
      ? VENUE_TYPE_TRANSLATIONS[event.venue.type]
      : null
  }));

  return eventosTraducidos;
}

/**
 * Ejemplo 3: Traducir el contexto de usuario completo
 */
export async function ejemploTraducirContexto() {
  const SentianceUserContext = require('@sentiance-react-native/user-context');

  // Obtener contexto
  const userContext = await SentianceUserContext.requestUserContext();

  // Traducir usando la función helper
  const contextoTraducido = translateUserContext(userContext);

  console.log('Tiempo semántico:', contextoTraducido.semanticTime);
  console.log('Eventos:', contextoTraducido.events);
  console.log('Segmentos activos:', contextoTraducido.activeSegments);

  return contextoTraducido;
}
