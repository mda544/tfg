/**
 * @typedef {Object} GeoPointDTO
 * @property {number} lat
 * @property {number} lon
 */

// Autenticación

/**
 * @typedef {Object} RegisterRequestDTO
 * @property {string} username
 * @property {string} password
 */

/**
 * @typedef {Object} LoginRequestDTO
 * @property {string} username
 * @property {string} password
 */

/**
 * @typedef {Object} TokenResponseDTO
 * @property {string} access_token
 * @property {string} token_type
 * @property {string} user_id
 * @property {string} username
 */

// Conductores

/**
 * @typedef {Object} ConductorCreateDTO
 * @property {string}  name
 * @property {string}  [description]
 * @property {number}  diameter_mm
 * @property {number}  r_ac_75_ohm_km
 * @property {number}  r_ac_25_ohm_km
 * @property {number}  [emissivity]
 * @property {number}  [absorptivity]
 * @property {number}  [max_temp_c]
 */

/**
 * @typedef {Object} ConductorResponseDTO
 * @property {string}  id
 * @property {string}  name
 * @property {string}  [description]
 * @property {number}  diameter_mm
 * @property {number}  r_ac_75_ohm_km
 * @property {number}  r_ac_25_ohm_km
 * @property {number}  emissivity
 * @property {number}  absorptivity
 * @property {number}  max_temp_c
 * @property {string}  created_at
 * @property {string}  updated_at
 */

/** @param {ConductorCreateDTO} c @returns {ConductorCreateDTO} */
export function buildConductorCreateDTO(c) {
  return {
    name:           c.name,
    description:    c.description ?? null,
    diameter_mm:    c.diameter_mm,
    r_ac_75_ohm_km: c.r_ac_75_ohm_km,
    r_ac_25_ohm_km: c.r_ac_25_ohm_km,
    emissivity:     c.emissivity   ?? 0.5,
    absorptivity:   c.absorptivity ?? 0.5,
    max_temp_c:     c.max_temp_c   ?? 90.0,
  };
}

/**
 * Subconjunto de campos del conductor para el payload de cálculo de rates.
 * @typedef {Object} ConductorDTO
 * @property {number} diameter_mm
 * @property {number} r_ac_75_ohm_km
 * @property {number} r_ac_25_ohm_km
 * @property {number} emissivity
 * @property {number} absorptivity
 * @property {number} max_temp_c
 */

/** @param {ConductorDTO} c @returns {ConductorDTO} */
export function buildConductorDTO(c) {
  return {
    diameter_mm:    c.diameter_mm,
    r_ac_75_ohm_km: c.r_ac_75_ohm_km,
    r_ac_25_ohm_km: c.r_ac_25_ohm_km,
    emissivity:     c.emissivity   ?? 0.5,
    absorptivity:   c.absorptivity ?? 0.5,
    max_temp_c:     c.max_temp_c,
  };
}

// Cálculo de rates  POST /rates

/**
 * @typedef {Object} MeteoScenarioDTO
 * @property {string} season          
 * @property {number} temp_amb_c
 * @property {number} wind_speed_ms
 * @property {number} wind_angle_deg
 * @property {number} solar_radiation_wm2
 */

/**
 * @typedef {Object} RateCalculationRequestDTO
 * @property {GeoPointDTO[]}      coordinates
 * @property {ConductorDTO}       conductor
 * @property {MeteoScenarioDTO[]} scenarios
 * @property {number}             segment_step_m
 * @property {boolean}            use_real_spans
 * @property {boolean}            use_dem
 */

/**
 * @param {string} season
 * @param {{ temp: number, viento: number, angulo: number, radiacion: number }} s
 * @returns {MeteoScenarioDTO}
 */
export function buildMeteoScenarioDTO(season, s) {
  return {
    season,
    temp_amb_c:          s.temp,
    wind_speed_ms:       s.viento,
    wind_angle_deg:      s.angulo,
    solar_radiation_wm2: s.radiacion,
  };
}

// Respuesta de rates

/**
 * @typedef {Object} AppliedScenarioDTO
 * @property {number} temp_amb_c
 * @property {number} wind_speed_ms
 * @property {number} solar_radiation_wm2
 */

/**
 * @typedef {Object} SegmentDetailDTO
 * @property {number}            ampacity_a
 * @property {number}            qc_wm
 * @property {number}            qr_wm
 * @property {number}            qs_wm
 * @property {number}            r_tc_ohm_m
 * @property {string}            conv_mode
 * @property {number}            elevation_m
 * @property {AppliedScenarioDTO} scenario
 */

/**
 * @typedef {Object} SegmentResultDTO
 * @property {string}                          segment_id
 * @property {number}                          length_km
 * @property {number}                          elevation_m
 * @property {GeoPointDTO}                     mid_point
 * @property {GeoPointDTO}                     start_point
 * @property {GeoPointDTO}                     end_point
 * @property {Object.<string, number>}         rates
 * @property {Object.<string, SegmentDetailDTO>} details
 * @property {number}                          design_rate_a
 */

/**
 * @typedef {Object} RouteInfoDTO
 * @property {number}   length_km
 * @property {number}   n_points
 * @property {string}   elevation_source
 * @property {string}   segment_mode
 * @property {number}   min_elevation_m
 * @property {number}   max_elevation_m
 * @property {number}   avg_elevation_m
 * @property {Object}   [bbox]
 * @property {Object[]} [long_spans]
 * @property {Object[]} [self_intersects]
 */

/**
 * @typedef {Object} RateCalculationResponseDTO
 * @property {string}                    id
 * @property {number}                    n_segments
 * @property {ConductorDTO}              conductor
 * @property {SegmentResultDTO[]}        segments
 * @property {number}                    design_rate_a
 * @property {Object.<string, number>}   rates_by_season
 * @property {RouteInfoDTO}              route_info
 * @property {string[]}                  warnings
 */

// Clima  GET /climate/percentiles

/**
 * @typedef {Object} SeasonalPercentilesDTO
 * @property {number} temp_p10_c
 * @property {number} temp_p50_c
 * @property {number} temp_p90_c
 * @property {number} wind_p10_ms
 * @property {number} wind_p50_ms
 * @property {number} wind_p90_ms
 * @property {number} radiation_p50_wm2
 * @property {number} radiation_p90_wm2
 * @property {number} n_hours
 * @property {string} source
 * @property {string} years_covered
 */

/**
 * @typedef {Object} ClimatePercentilesResponseDTO
 * @property {string}                                source
 * @property {GeoPointDTO}                           point
 * @property {Object.<string, SeasonalPercentilesDTO>} percentiles
 */

// Elevación  GET /elevation

/**
 * @typedef {Object} ElevationResponseDTO
 * @property {number} lat
 * @property {number} lon
 * @property {number} elevation_m
 */

// Líneas

/**
 * @typedef {Object} LineCreateDTO
 * @property {string}       name
 * @property {string}       [description]
 * @property {GeoPointDTO[]} coordinates
 */

/**
 * @typedef {Object} LineResponseDTO
 * @property {string}  id
 * @property {string}  name
 * @property {string}  [description]
 * @property {number}  [length_km]
 * @property {Object}  geometry_geojson
 * @property {string}  created_at
 * @property {string}  updated_at
 */

/** @param {LineCreateDTO} l @returns {LineCreateDTO} */
export function buildLineCreateDTO(l) {
  return {
    name:        l.name,
    description: l.description ?? null,
    coordinates: l.coordinates.map(({ lat, lon }) => ({ lat, lon })),
  };
}

// Casos de estudio

/**
 * @typedef {Object} StudyCaseCreateDTO
 * @property {string}              name
 * @property {string}              [description]
 * @property {string}              line_id
 * @property {string}              conductor_id
 * @property {number}              [segment_step_m]
 * @property {boolean}             [use_real_spans]
 * @property {boolean}             [use_dem]
 * @property {MeteoScenarioDTO[]}  [scenarios]
 */

/**
 * @typedef {Object} StudyCaseResponseDTO
 * @property {string}  id
 * @property {string}  name
 * @property {string}  [description]
 * @property {string}  line_id
 * @property {string}  conductor_id
 * @property {number}  segment_step_m
 * @property {boolean} use_real_spans
 * @property {boolean} use_dem
 * @property {Object[]} scenarios
 * @property {string}  created_at
 * @property {string}  updated_at
 */

/** @param {StudyCaseCreateDTO} sc @returns {StudyCaseCreateDTO} */
export function buildStudyCaseCreateDTO(sc) {
  return {
    name:           sc.name,
    description:    sc.description    ?? null,
    line_id:        sc.line_id,
    conductor_id:   sc.conductor_id,
    segment_step_m: sc.segment_step_m ?? 500.0,
    use_real_spans: sc.use_real_spans  ?? false,
    use_dem:        sc.use_dem         ?? true,
    scenarios:      sc.scenarios?.map((s) =>
      buildMeteoScenarioDTO(s.season, s)
    ) ?? null,
  };
}