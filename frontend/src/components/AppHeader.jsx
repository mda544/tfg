export default function AppHeader({ username, onLogout }) {
  return (
    <header className="app-header">
      <div className="header-brand">
        <h1>AmpacityGIS</h1>
      </div>
      <div className="header-user">
        <span>{username}</span>
        <button className="btn-logout" onClick={onLogout}>
          Cerrar sesión
        </button>
      </div>
    </header>
  );
}