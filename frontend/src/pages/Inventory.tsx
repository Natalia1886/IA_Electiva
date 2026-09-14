import { FormEvent, useEffect, useState } from "react";
import { apiGet, apiPost } from "../api/client";
import { InventoryItem, LowStockAlert, StockMovement } from "../api/types";
import { useAuth } from "../auth/AuthContext";

export default function Inventory() {
  const { isAdmin } = useAuth();
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [alerts, setAlerts] = useState<LowStockAlert[]>([]);
  const [movements, setMovements] = useState<StockMovement[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [moveProduct, setMoveProduct] = useState<number | null>(null);
  const [moveQty, setMoveQty] = useState(1);
  const [moveType, setMoveType] = useState("purchase");
  const [moveReason, setMoveReason] = useState("");

  const load = async () => {
    try {
      const items = await apiGet<InventoryItem[]>("/inventory");
      setItems(items);
      if (isAdmin) {
        setAlerts(await apiGet<LowStockAlert[]>("/inventory/alerts"));
      } else {
        setAlerts([]);
      }
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const loadMovements = async () => {
    try {
      setMovements(await apiGet<StockMovement[]>("/inventory/movements?limit=30"));
    } catch {
      /* admin only */
    }
  };

  useEffect(() => {
    void load();
    if (isAdmin) void loadMovements();
  }, [isAdmin]);

  const adjust = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await apiPost("/inventory/movements", {
        product_id: moveProduct,
        quantity: moveQty,
        movement_type: moveType,
        reason: moveReason || undefined,
      });
      setMoveProduct(null);
      setMoveQty(1);
      setMoveReason("");
      await load();
      await loadMovements();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="page">
      <h1>Inventario</h1>

      {isAdmin && (
        <>
          <h2>Alertas de stock bajo</h2>
          {alerts.length === 0 ? (
            <p className="hint">Sin alertas.</p>
          ) : (
            <table>
              <thead><tr><th>Producto</th><th>Stock</th><th>Mínimo</th><th>Faltan</th></tr></thead>
              <tbody>
                {alerts.map((a) => (
                  <tr key={a.product_id} className="row-alert">
                    <td>{a.name}</td><td>{a.stock}</td><td>{a.min_stock}</td><td>{a.missing_units}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}

      {isAdmin && (
        <>
          <h2>Movimiento de stock (compra / ajuste / devolución)</h2>
          {error && <p className="error">{error}</p>}
          <form className="panel" onSubmit={adjust}>
            <div className="form-grid narrow">
              <label>Producto
                <select value={moveProduct ?? ""} onChange={(e) => setMoveProduct(e.target.value ? Number(e.target.value) : null)} required>
                  <option value="">Seleccionar…</option>
                  {items.map((i) => <option key={i.product_id} value={i.product_id}>{i.code} — {i.name}</option>)}
                </select>
              </label>
              <label>Cantidad<input type="number" min="1" value={moveQty} onChange={(e) => setMoveQty(Number(e.target.value) || 0)} required /></label>
              <label>Tipo
                <select value={moveType} onChange={(e) => setMoveType(e.target.value)}>
                  <option value="purchase">Entrada (compra)</option>
                  <option value="adjustment">Salida (ajuste)</option>
                  <option value="return">Entrada (devolución)</option>
                </select>
              </label>
              <label>Motivo<input value={moveReason} onChange={(e) => setMoveReason(e.target.value)} placeholder="Opcional" /></label>
            </div>
            <button className="btn btn-primary" type="submit">Registrar movimiento</button>
          </form>

          <h2>Historial de movimientos</h2>
          <table>
            <thead><tr><th>Fecha</th><th>Producto</th><th>Tipo</th><th>Cantidad</th><th>Motivo</th></tr></thead>
            <tbody>
              {movements.map((m) => (
                <tr key={m.id}>
                  <td>{new Date(m.created_at).toLocaleString("es-MX")}</td>
                  <td>{m.product_code} — {m.product_name}</td>
                  <td>{m.movement_type}</td>
                  <td className={m.quantity > 0 ? "qty-in" : "qty-out"}>{m.quantity > 0 ? `+${m.quantity}` : m.quantity}</td>
                  <td>{m.reason ?? ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      <h2>Stock actual</h2>
      <table>
        <thead><tr><th>Código</th><th>Producto</th><th>Stock</th><th>Mínimo</th><th>Estado</th></tr></thead>
        <tbody>
          {items.map((i) => (
            <tr key={i.product_id} className={i.low_stock ? "row-alert" : ""}>
              <td>{i.code}</td><td>{i.name}</td><td>{i.stock}</td><td>{i.min_stock}</td>
              <td>{i.out_of_stock ? <span className="badge badge-danger">Sin existencias</span> : i.low_stock ? <span className="badge badge-warn">Bajo</span> : <span className="badge badge-ok">OK</span>}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}