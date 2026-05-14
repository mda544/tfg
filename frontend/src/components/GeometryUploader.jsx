import { useRef, useState } from "react";
import { parseGeoJSON, parseSHP } from "../utils/geometryLoader";
import { parseLineExcel } from "../utils/excelParser";
import styles from "./GeometryUploader.module.css";

export default function GeometryUploader({ onGeometriaCargada }) {
  const inputRef = useRef(null);
  const [estado, setEstado] = useState("idle"); // idle | loading | error
  const [mensaje, setMensaje] = useState("");

  const procesarArchivos = async (files) => {
    const lista = Array.from(files);
    setEstado("loading");
    setMensaje("");

    try {
      let features = [];
      let advertencias = [];

      const geojsonFile = lista.find((f) => /\.(geojson|json)$/i.test(f.name));
      const shpFile = lista.find((f) => /\.shp$/i.test(f.name));
      const dbfFile = lista.find((f) => /\.dbf$/i.test(f.name));
      const excelFile = lista.find((f) => /\.(xlsx|xls)$/i.test(f.name));

      if (geojsonFile) {
        features = await parseGeoJSON(geojsonFile);
      } else if (shpFile) {
        features = await parseSHP(shpFile, dbfFile);
      } else if (excelFile) {
        const resultado = await parseLineExcel(excelFile);
        features = [resultado];
        advertencias = resultado.advertencias ?? [];
        const { sistema_original, zona_utm, n_apoyos } = resultado.propiedades;
        const infoSistema =
          sistema_original === "utm"
            ? ` — UTM zona ${zona_utm}N → WGS84`
            : " — WGS84";
        setMensaje(
          `${n_apoyos} apoyos cargados${infoSistema}` +
            (advertencias.length > 0
              ? ` (${advertencias.length} filas ignoradas)`
              : ""),
        );
      } else {
        throw new Error(
          "Formato no reconocido. Usa .geojson, .json, .shp o .xlsx",
        );
      }

      if (features.length === 0)
        throw new Error("El archivo no contiene geometrías válidas.");

      setEstado("idle");
      setMensaje(
        `${features[0].propiedades?.n_apoyos ?? features.length} apoyos cargados` +
          (advertencias.length > 0
            ? ` (${advertencias.length} filas ignoradas)`
            : ""),
      );

      onGeometriaCargada(features.length === 1 ? features[0] : features);
    } catch (err) {
      setEstado("error");
      setMensaje(err.message);
    }

    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div
      className={`${styles.uploader} ${styles[estado]}`}
      onDrop={(e) => {
        e.preventDefault();
        procesarArchivos(e.dataTransfer.files);
      }}
      onDragOver={(e) => e.preventDefault()}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".geojson,.json,.shp,.dbf,.xlsx,.xls"
        multiple
        style={{ display: "none" }}
        onChange={(e) => procesarArchivos(e.target.files)}
      />
      <span className={styles.icon}>
        {estado === "loading" ? "⋯" : estado === "error" ? "✕" : "↑"}
      </span>
      <p className={styles.label}>Arrastra un .geojson, .shp o .xlsx aquí</p>
      {mensaje && (
        <p
          className={`${styles.mensaje} ${estado === "error" ? styles.mensajeError : styles.mensajeOk}`}
        >
          {mensaje}
        </p>
      )}
      <p className={styles.hint}>
        Excel: columnas X (longitud) e Y (latitud) en WGS84
      </p>
    </div>
  );
}
