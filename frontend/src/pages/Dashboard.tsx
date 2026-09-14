import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet } from "../api/client";
import { Dashboard, InventoryItem, Recommendation } from "../api/types";

const fmt = (n: number) => n.toLocaleString("es-CO", { style: "currency", currency: "COP" });

const statusBadge = (status: InventoryItem["stock_status"]) =>
  status === "out_of_stock" ? (
    <span className="badge badge-danger">Agotado</span>
  ) : (
    <span className="badge badge-warn">Bajo</span>
  );

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [inventory, setInventory] = useState<InventoryItem[] | null>(null);
  const [recs, setRecs] = useState<Recommendation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [d, inv, r] = await Promise.all([
          apiGet<Dashboard>("/reports/dashboard"),
          apiGet<InventoryItem[]>("/inventory"),
          apiGet<Recommendation>("/ai/recommendations"),
        ]);
        if (cancelled) return;
        setDashboard(d);
        setInventory(inv);
        setRecs(r);
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="page">
        <h1>Panel administrativo</h1>
        <p className="hint">Cargando indicadores…</p>
      </div>
    );
  }

  if (error) return <p className="error">{error}</p>;
  if (!dashboard || !inventory) return <p className="error">No se pudieron cargar los indicadores.</p>;

  const today = new Date().toLocaleDateString("es-MX", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  const outOfStock = inventory.filter((i) => i.stock_status === "out_of_stock");
  const lowStock = inventory.filter((i) => i.stock_status === "low");
  const alertItems = [...outOfStock, ...lowStock];
  const weekHasSales = dashboard.week_trend.some((d) => d.total > 0);
  const maxTotal = Math.max(...dashboard.week_trend.map((d) => d.total), 1);
  const suggestedUnits = recs ? recs.items.reduce((acc, i) => acc + i.suggested_quantity, 0) : 0;
  const holidayHits = recs ? recs.items.filter((i) => i.upcoming_holiday).length : 0;

  return (
    <div className="page">
      <div className="page-head">
        <h1>Panel administrativo</h1>
        <span className="hint">{today}</span>
      </div>

      <div className="cards">
        <div className="card kpi">
          <span className="stat-icon"><svg viewBox="0 0 24 24"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg></span>
          <span className="card-label">Ingresos del día</span>
          <span className="card-value">{fmt(dashboard.today_sales_value)}</span>
        </div>
        <div className="card kpi">
          <span className="stat-icon"><svg viewBox="0 0 24 24"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg></span>
          <span className="card-label">Operaciones hoy</span>
          <span className="card-value">{dashboard.today_transactions}</span>
        </div>
        <div className="card kpi">
          <span className="stat-icon"><svg viewBox="0 0 24 24"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg></span>
          <span className="card-label">Artículos vendidos hoy</span>
          <span className="card-value">{dashboard.today_units}</span>
        </div>
        <div className="card kpi">
          <span className="stat-icon"><svg viewBox="0 0 24 24"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></span>
          <span className="card-label">Stock bajo</span>
          <span className="card-value">{lowStock.length}</span>
        </div>
        <div className="card kpi">
          <span className="stat-icon"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg></span>
          <span className="card-label">Agotados</span>
          <span className="card-value">{outOfStock.length}</span>
        </div>
        <div className="card kpi">
          <span className="stat-icon"><svg viewBox="0 0 24 24"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg></span>
          <span className="card-label">Valor de inventario</span>
          <span className="card-value">{fmt(dashboard.total_stock_value)}</span>
        </div>
      </div>

      {dashboard.today_sales_value === 0 && dashboard.today_transactions === 0 && (
        <div className="panel empty-state">
          <p>No hay ventas registradas hoy.</p>
        </div>
      )}

      <h2>Ventas · últimos 7 días</h2>
      {weekHasSales ? (
        <div className="bars">
          {dashboard.week_trend.map((d) => (
            <div key={d.date} className="bar-col">
              <div
                className="bar"
                style={{ height: `${(d.total / maxTotal) * 100}%` }}
                title={`${d.date}: ${fmt(d.total)} · ${d.transactions} ventas`}
                data-value={fmt(d.total)}
              />
              <span className="bar-label">{d.date.slice(8)}</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="panel empty-state">
          <p>No hay ventas registradas en los últimos 7 días.</p>
        </div>
      )}

      <div className="grid-2">
        <div>
          <h2>Productos más vendidos · 30 días</h2>
          {dashboard.top_products_30d.length === 0 ? (
            <p className="hint">Aún no hay suficientes ventas para calcular el top.</p>
          ) : (
            <table>
              <thead>
                <tr><th>Producto</th><th>Uds.</th><th>Valor</th></tr>
              </thead>
              <tbody>
                {dashboard.top_products_30d.map((p) => (
                  <tr key={p.product_id}>
                    <td>{p.name}</td>
                    <td>{p.units_sold}</td>
                    <td>{fmt(p.total_value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <div>
          <h2>Alertas de stock</h2>
          {alertItems.length === 0 ? (
            <p className="hint">No hay productos en riesgo de stock.</p>
          ) : (
            <table>
              <thead>
                <tr><th>Producto</th><th>Stock</th><th>Mínimo</th><th>Estado</th></tr>
              </thead>
              <tbody>
                {alertItems.map((i) => (
                  <tr key={i.product_id} className={i.stock_status === "out_of_stock" ? "row-alert" : undefined}>
                    <td>{i.name}</td>
                    <td>{i.stock}</td>
                    <td>{i.min_stock}</td>
                    <td>{statusBadge(i.stock_status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <h2>Recomendaciones de compra</h2>
      {recs && recs.items.length > 0 ? (
        <div className="panel">
          <div className="rec-head">
            <span className="hint">Basadas en stock actual y demanda de los últimos 30 días</span>
            <Link className="btn btn-ghost" to="/recommendations">Ver detalle</Link>
          </div>
          <div className="cards">
            <div className="card"><span className="card-label">Productos sugeridos</span><span className="card-value">{recs.items.length}</span></div>
            <div className="card"><span className="card-label">Unidades sugeridas</span><span className="card-value">{suggestedUnits}</span></div>
            <div className="card"><span className="card-label">Para próxima celebración</span><span className="card-value">{holidayHits}</span></div>
          </div>
        </div>
      ) : (
        <p className="hint">Sin recomendaciones en este momento.</p>
      )}
    </div>
  );
}