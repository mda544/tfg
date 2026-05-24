/**
 * @typedef {Object} GeoPointDTO
 * @property {number} lat
 * @property {number} lon
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
    name: c.name,
    description: c.description ?? null,
    diameter_mm: c.diameter_mm,
    r_ac_75_ohm_km: c.r_ac_75_ohm_km,
    r_ac_25_ohm_km: c.r_ac_25_ohm_km,
    emissivity: c.emissivity ?? 0.5,
    absorptivity: c.absorptivity ?? 0.5,
    max_temp_c: c.max_temp_c ?? 90.0,
  };
}

// Líneas

/**
 * @typedef {Object} LineCreateDTO
 * @property {string}        name
 * @property {string}        [description]
 * @property {GeoPointDTO[]} coordinates
 */

/**
 * @typedef {Object} LineResponseDTO
 * @property {string}  id
 * @property {string}  name
 * @property {string}  [description]
 * @property {number}  [length_km]
 * @property {number}  [n_points]
 * @property {number}  [min_elevation_m]
 * @property {number}  [max_elevation_m]
 * @property {number}  [avg_elevation_m]
 * @property {Object}  geometry_geojson
 * @property {string}  created_at
 * @property {string}  updated_at
 */

// Casos de estudio

/**
 * @typedef {Object} StudyCaseCreateDTO
 * @property {string}  name
 * @property {string}  [description]
 * @property {string}  line_id
 * @property {number}  [segment_step_m]
 * @property {boolean} [use_real_spans]
 * @property {boolean} [use_dem]
 */

/**
 * @typedef {Object} StudyCaseResponseDTO
 * @property {string}  id
 * @property {string}  name
 * @property {string}  [description]
 * @property {string}  line_id
 * @property {number}  segment_step_m
 * @property {boolean} use_real_spans
 * @property {boolean} use_dem
 * @property {string}  created_at
 * @property {string}  updated_at
 */

// WeatherInput

/**
 * @typedef {Object} WeatherInputDTO
 * @property {string} season
 * @property {number} temp_amb_c
 * @property {number} wind_speed_ms
 * @property {number} wind_angle_deg
 * @property {number} solar_radiation_wm2
 */

// Rates entrada

/**
 * @typedef {Object} RateCreateDTO
 * @property {string}            study_case_id
 * @property {string}            conductor_id
 * @property {WeatherInputDTO[]} weather_inputs
 * @property {string}            [climate_source]
 */

// Rates respuesta

/**
 * @typedef {Object} SegmentRatingDTO
 * @property {number} ampacity
 * @property {number} qc_wm
 * @property {number} qr_wm
 * @property {number} qs_wm
 * @property {number} r_tc_ohm_m
 * @property {string} conv_mode
 */

/**
 * @typedef {Object} SegmentResultDTO
 * @property {string}                            segment_id
 * @property {number}                            index
 * @property {number}                            length_km
 * @property {number}                            elevation_m
 * @property {number}                            azimuth_deg
 * @property {GeoPointDTO}                       mid_point
 * @property {GeoPointDTO}                       start_point
 * @property {GeoPointDTO}                       end_point
 * @property {Object.<string, number>}           rates
 * @property {Object.<string, SegmentRatingDTO>} ratings
 * @property {number}                            design_rate
 */

/**
 * @typedef {Object} RateResultResponseDTO
 * @property {string}             id
 * @property {string}             study_case_id
 * @property {number}             n_segments
 * @property {Object}             conductor
 * @property {WeatherInputDTO[]}  weather_inputs
 * @property {string}             climate_source
 * @property {string}             elevation_source
 * @property {number}             rate_summer
 * @property {number}             rate_autumn
 * @property {number}             rate_winter
 * @property {number}             rate_spring
 * @property {number}             design_rate
 * @property {SegmentResultDTO[]} segments
 * @property {string[]}           warnings
 * @property {string}             [created_at]
 */

// Clima

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
 * @property {string}                                  source
 * @property {GeoPointDTO}                             point
 * @property {Object.<string, SeasonalPercentilesDTO>} percentiles
 */
