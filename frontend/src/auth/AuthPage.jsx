import { useState, useMemo } from "react";
import { useAuth } from "./useAuth";
import styles from "./AuthPage.module.css";

function validateUsername(value) {
  if (value.length < 3) return "Mínimo 3 caracteres.";
  if (value.length > 64) return "Máximo 64 caracteres.";
  if (!/^[a-zA-Z0-9_-]+$/.test(value))
    return "Solo letras, números, guiones y guiones bajos.";
  return null;
}

function validatePassword(value) {
  if (value.length < 8) return "Mínimo 8 caracteres.";
  if (!/[A-Z]/.test(value)) return "Debe contener al menos una mayúscula.";
  if (!/[a-z]/.test(value)) return "Debe contener al menos una minúscula.";
  if (!/[0-9]/.test(value)) return "Debe contener al menos un número.";
  return null;
}

export default function AuthPage() {
  const { login, register } = useAuth();

  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [touched, setTouched] = useState({ username: false, password: false });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isRegister = mode === "register";

  // Validación solo activa en modo registro
  const usernameError =
    isRegister && touched.username ? validateUsername(username) : null;
  const passwordError =
    isRegister && touched.password ? validatePassword(password) : null;

  const canSubmit = useMemo(() => {
    if (!username || !password) return false;
    if (isRegister) {
      return (
        validateUsername(username) === null &&
        validatePassword(password) === null
      );
    }
    return true;
  }, [username, password, isRegister]);

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

  const handleModeToggle = () => {
    setMode(mode === "login" ? "register" : "login");
    setError("");
    setTouched({ username: false, password: false });
  };

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.logo}>
          <span className={styles.logoText}>AmpacityGIS</span>
        </div>

        <h1 className={styles.title}>
          {isRegister ? "Crear cuenta" : "Iniciar sesión"}
        </h1>
        <p className={styles.subtitle}>
          {isRegister
            ? "Empieza a calcular rates estáticos estacionales"
            : "Accede a tus líneas y casos de estudio"}
        </p>

        <form className={styles.form} onSubmit={handleSubmit}>
          {/* Usuario */}
          <div className={styles.field}>
            <label htmlFor="username">Usuario</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onBlur={() => setTouched((t) => ({ ...t, username: true }))}
              placeholder="mi_usuario"
              required
              autoFocus
              minLength={3}
              maxLength={64}
              className={usernameError ? styles.inputError : ""}
            />
            {usernameError && (
              <p className={styles.fieldError}>{usernameError}</p>
            )}
          </div>

          {/* Contraseña */}
          <div className={styles.field}>
            <label htmlFor="password">Contraseña</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onBlur={() => setTouched((t) => ({ ...t, password: true }))}
              placeholder="••••••••"
              required
              minLength={isRegister ? 8 : 1}
              className={passwordError ? styles.inputError : ""}
            />
            {passwordError && (
              <p className={styles.fieldError}>{passwordError}</p>
            )}
            {/* Pista de requisitos solo en registro, antes de tocar el campo */}
            {isRegister && !touched.password && (
              <p className={styles.hint}>
                Mínimo 8 caracteres, una mayúscula, una minúscula y un número.
              </p>
            )}
          </div>

          {/* Error de la API */}
          {error && <p className={styles.error}>{error}</p>}

          <button
            className={styles.submit}
            type="submit"
            disabled={loading || !canSubmit}
          >
            {loading ? "Cargando..." : isRegister ? "Crear usuario" : "Entrar"}
          </button>
        </form>

        <p className={styles.toggle}>
          {isRegister ? "¿Ya tienes usuario?" : "¿No tienes usuario?"}{" "}
          <button className={styles.toggleBtn} onClick={handleModeToggle}>
            {isRegister ? "Inicia sesión" : "Regístrate"}
          </button>
        </p>
      </div>
    </div>
  );
}
