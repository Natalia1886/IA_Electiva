import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet } from "../api/client";
import { Sale } from "../api/types";
import { useAuth } from "../auth/AuthContext";

const fmt = (n: number) => n.toLocaleString("es-CO", { style: "currency", currency: "COP" });

const localToday = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

const ACTIONS = [
  { to: "/sales", title: "Registrar venta", text: "Captura una venta: el stock se descuenta automáticamente." },
  { to: "/products", title: "Consultar productos", text: "Revisa precios, stock y disponibilidad del catálogo." },
];

export default function SalesHome() {
  const { user } = useAuth();
  const [sales, setSales] = useState<Sale[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    (async () => {
      try {
        const mine = await apiGet<Sale[]>(`/sales?salesperson_id=${user.id}&limit=100`);
        if (!cancelled) setSales(mine);
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [user]);

  const todayStr = localToday();
  const todaySales = (sales ?? []).filter((s) => s.sale_date.toString().startsWith(todayStr));
  const todayValue = todaySales.reduce((acc, s) => acc + s.total, 0);
  const todayUnits = (sales ?? [])
    .filter((s) => s.sale_date.toString().startsWith(todayStr))
    .reduce((acc, s) => acc + s.items.reduce((a, i) => a + i.quantity, 0), 0);
  const lastSales = (sales ?? []).slice(0, 10);

  const today = new Date().toLocaleDateString("es-MX", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="page">
      <div className="page-head">
        <h1>Hola, {user?.full_name}</h1>
        <span className="hint">{today}</span>
      </div>

      <div className="cards">
        <div className="card"><span className="card-label">Ventas de hoy</span><span className="card-value">{fmt(todayValue)}</span></div>
        <div className="card"><span className="card-label">Operaciones de hoy</span><span className="card-value">{todaySales.length}</span></div>
        <div className="card"><span className="card-label">Artículos vendidos hoy</span><span className="card-value">{todayUnits}</span></div>
      </div>

      <h2>Acciones rápidas</h2>
      <div className="cards">
        {ACTIONS.map((a) => (
          <Link key={a.to} to={a.to} className="card action-card" style={{ textDecoration: "none" }}>
            <span className="card-value">{a.title}</span>
            <span className="card-label">{a.text}</span>
          </Link>
        ))}
      </div>

      <h2>Mis ventas</h2>
      {loading ? (
        <p className="hint">Cargando tus ventas…</p>
      ) : error ? (
        <p className="error">{error}</p>
      ) : !sales || sales.length === 0 ? (
        <div className="panel empty-state">
          <p>Aún no has registrado ventas.</p>
          <Link className="btn btn-primary" to="/sales">Registrar mi primera venta</Link>
        </div>
      ) : (
        <>
          <table>
            <thead>
              <tr><th>Venta</th><th>Fecha</th><th>Artículos</th><th>Total</th><th>Fuente</th></tr>
            </thead>
            <tbody>
              {lastSales.map((s) => (
                <tr key={s.id}>
                  <td>{s.sale_number ?? `Venta #${s.id}`}</td>
                  <td>{s.sale_date.toString().slice(0, 10)}</td>
                  <td>{s.item_count}</td>
                  <td>{fmt(s.total)}</td>
                  <td>{s.source === "digitized" ? "Digitalizada" : "Manual"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="hint">
            Mostrando las últimas {lastSales.length} ·{" "}
            <Link to="/sales">ver historial completo</Link>
          </p>
        </>
      )}
    </div>
  );
}