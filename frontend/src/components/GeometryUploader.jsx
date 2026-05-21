import { useRef, useState } from "react";
import { parseGeoJSON, parseSHP } from "../utils/geometryLoader";
import { parseLineExcel } from "../utils/excelParser";
import styles from "./GeometryUploader.module.css";

export default function GeometryUploader({ onRouteLoaded }) {
  const inputRef = useRef(null);
  const [status, setStatus] = useState("idle"); // idle | loading | error
  const [message, setMessage] = useState("");

  const processFiles = async (files) => {
    const fileList = Array.from(files);
    setStatus("loading");
    setMessage("");

    try {
      let features = [];
      let warnings = [];

      const geojsonFile = fileList.find((f) =>
        /\.(geojson|json)$/i.test(f.name),
      );
      const shpFile = fileList.find((f) => /\.shp$/i.test(f.name));
      const dbfFile = fileList.find((f) => /\.dbf$/i.test(f.name));
      const excelFile = fileList.find((f) => /\.(xlsx|xls)$/i.test(f.name));

      if (geojsonFile) {
        features = await parseGeoJSON(geojsonFile);
      } else if (shpFile) {
        features = await parseSHP(shpFile, dbfFile);
      } else if (excelFile) {
        const parsed = await parseLineExcel(excelFile);
        features = [parsed];
        warnings = parsed.advertencias ?? [];
        const { sistema_original, zona_utm, n_apoyos } = parsed.propiedades;
        const systemInfo =
          sistema_original === "utm"
            ? ` — UTM zona ${zona_utm}N → WGS84`
            : " — WGS84";
        setMessage(
          `${n_apoyos} apoyos cargados${systemInfo}` +
            (warnings.length > 0
              ? ` (${warnings.length} filas ignoradas)`
              : ""),
        );
      } else {
        throw new Error(
          "Formato no reconocido. Usa .geojson, .json, .shp o .xlsx",
        );
      }

      if (features.length === 0)
        throw new Error("El archivo no contiene geometrías válidas.");

      setStatus("idle");
      setMessage(
        `${features[0].propiedades?.n_apoyos ?? features.length} apoyos cargados` +
          (warnings.length > 0 ? ` (${warnings.length} filas ignoradas)` : ""),
      );

      onRouteLoaded(features.length === 1 ? features[0] : features);
    } catch (err) {
      setStatus("error");
      setMessage(err.message);
    }

    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div
      className={`${styles.uploader} ${styles[status]}`}
      onDrop={(e) => {
        e.preventDefault();
        processFiles(e.dataTransfer.files);
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
        onChange={(e) => processFiles(e.target.files)}
      />
      <span className={styles.icon}>
        {status === "loading" ? "⋯" : status === "error" ? "✕" : "↑"}
      </span>
      <p className={styles.label}>Arrastra un .geojson, .shp o .xlsx aquí</p>
      {message && (
        <p
          className={`${styles.mensaje} ${status === "error" ? styles.mensajeError : styles.mensajeOk}`}
        >
          {message}
        </p>
      )}
      <p className={styles.hint}>
        Excel: columnas X (longitud) e Y (latitud) en WGS84
      </p>
    </div>
  );
}
