import { FormEvent, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ADMIN_ONLY_PATHS, homeFor } from "../navigation";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname;

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const me = await login(username, password);
      const home = homeFor(me.role);
      // Never bounce a role into a screen that role cannot access.
      const target =
        from && !(me.role !== "admin" && ADMIN_ONLY_PATHS.includes(from)) ? from : home;
      navigate(target, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-brand">
        <div className="brand">
          <span className="brand-mark" aria-hidden>M</span>
          <div>
            <strong>Milan</strong>
            <span className="brand-sub">Inventario y Ventas</span>
          </div>
        </div>
        <h2>Sistema de gestión de artículos religiosos</h2>
        <p>Control de inventario, ventas y recomendaciones inteligentes para tu tienda.</p>
        <ul>
          <li>Registro rápido de ventas con carrito y descuento de stock automático</li>
          <li>Digitalización de cuadernos de ventas asistida por IA</li>
          <li>Recomendaciones de compra basadas en demanda y festividades</li>
        </ul>
      </div>
      <form className="login-card" onSubmit={onSubmit}>
        <h1>Iniciar sesión</h1>
        <label>
          Usuario
          <input value={username} onChange={(e) => setUsername(e.target.value)} autoFocus required />
        </label>
        <label>
          Contraseña
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </label>
        {error && <p className="error">{error}</p>}
        <button className="btn btn-primary" disabled={loading}>
          {loading ? "Ingresando…" : "Iniciar sesión"}
        </button>
        <p className="hint">Demo: admin / admin123 · vendedor / vendedor123</p>
      </form>
    </div>
  );
}