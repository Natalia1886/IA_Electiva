import { useEffect, useState } from "react";
import { apiGet } from "../api/client";
import { DailySummary } from "../api/types";

const fmt = (n: number) => n.toLocaleString("es-CO", { style: "currency", currency: "COP" });

export default function DailySummaryPage() {
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [data, setData] = useState<DailySummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setData(null);
    apiGet<DailySummary>(`/sales/daily/${date}`)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [date]);

  return (
    <div className="page">
      <div className="page-head">
        <h1>Resumen diario</h1>
        <label>Fecha<input type="date" value={date} onChange={(e) => setDate(e.target.value)} /></label>
      </div>

      {error && <p className="error">{error}</p>}
      {!data && !error && <p>Cargando…</p>}

      {data && (
        <>
          <div className="cards">
            <div className="card"><span className="card-label">Ventas del día</span><span className="card-value">{fmt(data.total_value)}</span></div>
            <div className="card"><span className="card-label">Operaciones</span><span className="card-value">{data.transaction_count}</span></div>
            <div className="card"><span className="card-label">Artículos vendidos</span><span className="card-value">{data.units_sold}</span></div>
            <div className="card"><span className="card-label">Productos distintos</span><span className="card-value">{data.products_count}</span></div>
          </div>

          <h2>Productos vendidos ({data.date})</h2>
          <table>
            <thead><tr><th>Código</th><th>Producto</th><th>Unidades</th><th>Valor</th></tr></thead>
            <tbody>
              {data.items.map((i) => (
                <tr key={i.product_id}><td>{i.code}</td><td>{i.name}</td><td>{i.units_sold}</td><td>{fmt(i.total_value)}</td></tr>
              ))}
              {data.items.length === 0 && (
                <tr><td colSpan={4}>Sin ventas registradas para este día.</td></tr>
              )}
            </tbody>
          </table>

          <h2>Más vendidos</h2>
          <div className="top-list">
            {data.top_products.map((p, i) => (
              <div key={p.product_id} className="top-item">
                <span className="top-rank">{i + 1}</span>
                <span className="top-name">{p.name}</span>
                <span>{p.units_sold} uds</span>
                <span className="top-value">{fmt(p.total_value)}</span>
              </div>
            ))}
            {data.top_products.length === 0 && <p className="hint">Sin datos.</p>}
          </div>
        </>
      )}
    </div>
  );
}