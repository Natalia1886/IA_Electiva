import { useEffect, useState } from "react";
import { apiGet } from "../api/client";
import { Recommendation } from "../api/types";

export default function Recommendations() {
  const [data, setData] = useState<Recommendation | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setData(null);
    setError(null);
    apiGet<Recommendation>("/ai/recommendations")
      .then(setData)
      .catch((e) => setError(e.message));
  };

  useEffect(() => {
    void load();
  }, []);

  return (
    <div className="page">
      <div className="page-head">
        <h1>Recomendaciones de compra</h1>
        <button className="btn btn-primary" onClick={load}>Generar de nuevo</button>
      </div>

      <p className="hint">
        Basadas en el modelo de segmentación de demanda entrenado con el historial de ventas digitalizadas, cruzado con
        inventario, stock mínimo y festividades religiosas próximas.
      </p>

      {error && <p className="error">{error}</p>}
      {!data && !error && <p>Cargando…</p>}

      {data && (
        <>
          <div className="panel">
            <strong>Origen:</strong> {data.source} · <strong>Generado:</strong> {data.generated_for}
            {data.summary && <p className="hint">{data.summary}</p>}
          </div>

          {data.items.map((i) => (
            <div key={i.product_id} className="rec-card">
              <div className="rec-head">
                <span className="rec-name">{i.code} — {i.name}</span>
                <span className="rec-qty">Comprar: <strong>{i.suggested_quantity}</strong></span>
              </div>
              <div className="rec-meta">
                Stock actual: <strong>{i.current_stock}</strong> · Mínimo: {i.min_stock} ·
                Vendidos 30d: {i.sold_last_30_days} · Demanda estimada: <strong>{i.estimated_demand}</strong>
                {i.segment && <span className="badge badge-admin">Segmento: {i.segment}</span>}
                {i.upcoming_holiday && <span className="badge badge-holiday">Próxima festividad: {i.upcoming_holiday}</span>}
              </div>
              {i.reason && <p className="rec-reason">Por qué: {i.reason}</p>}
              <p className="rec-rationale">{i.rationale}</p>
            </div>
          ))}

          {data.items.length === 0 && <p className="hint">Ningún producto requiere reposición.</p>}
        </>
      )}
    </div>
  );
}