import { useState } from "react";
import { useAuth } from "./useAuth";
import styles from "./AuthPage.module.css";

export default function AuthPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "login") await login(username, password);
      else await register(username, password);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}>⚡</span>
          <span className={styles.logoText}>AmpacityGIS</span>
        </div>

        <h1 className={styles.title}>
          {mode === "login" ? "Iniciar sesión" : "Crear cuenta"}
        </h1>
        <p className={styles.subtitle}>
          {mode === "login"
            ? "Accede a tus líneas y casos de estudio"
            : "Empieza a calcular rates estáticos estacionales"}
        </p>

        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={styles.field}>
            <label htmlFor="username">Usuario</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="mi_usuario"
              required
              autoFocus
              minLength={3}
              maxLength={64}
            />
          </div>

          <div className={styles.field}>
            <label htmlFor="password">Contraseña</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              minLength={6}
            />
          </div>

          {error && <p className={styles.error}>{error}</p>}

          <button className={styles.submit} type="submit" disabled={loading}>
            {loading
              ? "Cargando..."
              : mode === "login"
                ? "Entrar"
                : "Crear usuario"}
          </button>
        </form>

        <p className={styles.toggle}>
          {mode === "login" ? "¿No tienes usuario?" : "¿Ya tienes usuario?"}{" "}
          <button
            className={styles.toggleBtn}
            onClick={() => {
              setMode(mode === "login" ? "register" : "login");
              setError("");
            }}
          >
            {mode === "login" ? "Regístrate" : "Inicia sesión"}
          </button>
        </p>
      </div>
    </div>
  );
}
