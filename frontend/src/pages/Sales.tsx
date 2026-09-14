import { FormEvent, useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "../api/client";
import { PaymentMethod, PAYMENT_LABELS, Product, Sale } from "../api/types";
import { useAuth } from "../auth/AuthContext";

const fmt = (n: number) => n.toLocaleString("es-CO", { style: "currency", currency: "COP" });

const localToday = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

interface CartLine {
  product_id: number;
  quantity: number;
}

export default function Sales() {
  const { user } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [sales, setSales] = useState<Sale[]>([]);
  const [cart, setCart] = useState<CartLine[]>([]);
  const [search, setSearch] = useState("");
  const [saleDate, setSaleDate] = useState(localToday());
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("cash");
  const [note, setNote] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [stockWarn, setStockWarn] = useState<string | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [confirmed, setConfirmed] = useState<Sale | null>(null);

  const load = async () => {
    try {
      const [p, s] = await Promise.all([
        apiGet<Product[]>("/products"),
        apiGet<Sale[]>("/sales?limit=10"),
      ]);
      setProducts(p);
      setSales(s);
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const productOf = (id: number) => products.find((p) => p.id === id);

  const inCartQty = (id: number) =>
    cart.filter((l) => l.product_id === id).reduce((acc, l) => acc + l.quantity, 0);

  const remaining = (id: number) => (productOf(id)?.stock ?? 0) - inCartQty(id);

  const results = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return [];
    return products
      .filter((p) => p.name.toLowerCase().includes(q) || p.code.toLowerCase().includes(q))
      .slice(0, 8);
  }, [search, products]);

  // The grand total is derived live from the cart: any change to a product or
  // quantity recomputes it in the same render, so it can never desync.
  const total = cart.reduce((acc, l) => {
    const p = productOf(l.product_id);
    return acc + (p ? p.price * l.quantity : 0);
  }, 0);

  const addToCart = (p: Product) => {
    setStockWarn(null);
    if (p.stock <= 0) {
      setStockWarn(`"${p.name}" está agotado y no puede venderse.`);
      return;
    }
    setCart((prev) => {
      const existing = prev.find((l) => l.product_id === p.id);
      const inPrev = prev.filter((l) => l.product_id === p.id).reduce((a, l) => a + l.quantity, 0);
      if (!existing) return [...prev, { product_id: p.id, quantity: 1 }];
      const available = p.stock - (inPrev - existing.quantity);
      if (existing.quantity >= available) {
        setStockWarn(`"${p.name}" ya tiene en el carrito todo el stock disponible (${p.stock}).`);
        return prev;
      }
      return prev.map((l) =>
        l.product_id === p.id ? { ...l, quantity: Math.min(l.quantity + 1, available) } : l
      );
    });
  };

  const setQty = (i: number, raw: string) => {
    const qty = Math.floor(Number(raw));
    if (!Number.isFinite(qty)) return;
    const p = productOf(cart[i].product_id);
    if (!p) return;
    const other = inCartQty(p.id) - cart[i].quantity;
    const available = p.stock - other;
    if (qty > available) {
      setStockWarn(`"${p.name}": solo hay ${available} unidades disponibles.`);
    } else if (qty >= 1) {
      setStockWarn(null);
    }
    const applied = Math.max(1, Math.min(qty, available));
    setCart((prev) => prev.map((l, idx) => (idx === i ? { ...l, quantity: applied } : l)));
  };

  const removeLine = (i: number) => setCart((prev) => prev.filter((_, idx) => idx !== i));

  const openConfirm = () => {
    setError(null);
    if (cart.length === 0) {
      setError("Agrega al menos un producto al carrito.");
      return;
    }
    for (const l of cart) {
      const p = productOf(l.product_id);
      if (!p) continue;
      const available = p.stock - (inCartQty(p.id) - l.quantity);
      if (l.quantity > available) {
        setError(`"${p.name}": stock insuficiente (disponible ${available}).`);
        return;
      }
    }
    setConfirmOpen(true);
  };

  const submitSale = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const sale = await apiPost<Sale>("/sales", {
        sale_date: saleDate,
        items: cart.map((l) => ({ product_id: l.product_id, quantity: l.quantity })),
        note: note.trim() || undefined,
        payment_method: paymentMethod,
      });
      setConfirmed(sale);
      setConfirmOpen(false);
      setCart([]);
      setNote("");
      await load();
    } catch (err) {
      setError((err as Error).message);
      setConfirmOpen(false);
    } finally {
      setSubmitting(false);
    }
  };

  const resetCart = () => {
    setConfirmed(null);
    setCart([]);
    setNote("");
    setStockWarn(null);
  };

  return (
    <div className="page">
      <div className="page-head">
        <h1>Nueva venta</h1>
        <span className="hint">{user?.full_name}</span>
      </div>

      <div className="sales-layout">
      <div className="panel search-panel">
        <h3 style={{ marginTop: 0 }}>Buscar producto</h3>
        <input
          placeholder="Escribe el nombre o código del producto…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          autoFocus
        />
        {results.length > 0 && (
          <table>
            <thead><tr><th>Código</th><th>Producto</th><th>Precio</th><th>Stock</th><th></th></tr></thead>
            <tbody>
              {results.map((p) => (
                <tr key={p.id}>
                  <td>{p.code}</td>
                  <td>{p.name}</td>
                  <td>{fmt(p.price)}</td>
                  <td>
                    {remaining(p.id) <= 0 ? (
                      <span className="badge badge-danger">Agotado</span>
                    ) : p.stock <= p.min_stock ? (
                      <span className="badge badge-warn">Quedan {remaining(p.id)}</span>
                    ) : (
                      <span>{remaining(p.id)}</span>
                    )}
                  </td>
                  <td>
                    <button
                      className="btn"
                      onClick={() => addToCart(p)}
                      disabled={remaining(p.id) <= 0 || p.stock === 0}
                    >
                      Agregar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {search.trim() && results.length === 0 && products.length > 0 && (
          <p className="hint">Sin resultados para «{search}».</p>
        )}
      </div>

      <div className="panel cart-panel">
        <h3 style={{ marginTop: 0 }}>Carrito</h3>
        {stockWarn && <p className="error">{stockWarn}</p>}
        {error && <p className="error">{error}</p>}
        {cart.length === 0 ? (
          <div className="empty-state">
            <p>El carrito está vacío. Busca un producto para agregarlo.</p>
          </div>
        ) : (
          <form onSubmit={submitSale}>
            <div className="form-grid narrow">
              <label>Fecha de venta
                <input type="date" value={saleDate} onChange={(e) => setSaleDate(e.target.value)} required />
              </label>
              <label>Forma de pago
                <select value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}>
                  {(Object.keys(PAYMENT_LABELS) as PaymentMethod[]).map((pm) => (
                    <option key={pm} value={pm}>{PAYMENT_LABELS[pm]}</option>
                  ))}
                </select>
              </label>
            </div>

            <table>
              <thead>
                <tr><th>Producto</th><th>Precio</th><th>Cantidad</th><th>Subtotal</th><th></th></tr>
              </thead>
              <tbody>
                {cart.map((l, i) => {
                  const p = productOf(l.product_id);
                  const other = inCartQty(l.product_id) - l.quantity;
                  const available = (p?.stock ?? 0) - other;
                  return (
                    <tr key={l.product_id}>
                      <td>{p?.name}</td>
                      <td>{p ? fmt(p.price) : "—"}</td>
                      <td>
                        <input
                          type="number"
                          min={1}
                          max={available}
                          value={l.quantity}
                          onChange={(e) => setQty(i, e.target.value)}
                        />
                      </td>
                      <td>{p ? fmt(p.price * l.quantity) : "—"}</td>
                      <td>
                        <button type="button" className="btn btn-ghost btn-danger" onClick={() => removeLine(i)}>✕</button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            <div className="sale-footer">
              <label className="note-field">Nota
                <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Opcional" />
              </label>
              <div className="total-box">
                Total: <strong>{fmt(total)}</strong>
              </div>
            </div>

            <div className="modal-actions" style={{ justifyContent: "flex-end" }}>
              <button type="button" className="btn" onClick={() => setCart([])}>Vaciar carrito</button>
              <button type="button" className="btn btn-primary big" onClick={openConfirm}>
                Confirmar venta
              </button>
            </div>

            {confirmOpen && (
              <div className="modal-backdrop">
                <div className="modal">
                  <h2>Confirmar venta</h2>
                  <table>
                    <thead><tr><th>Producto</th><th>Cant.</th><th>Subtotal</th></tr></thead>
                    <tbody>
                      {cart.map((l) => {
                        const p = productOf(l.product_id);
                        return (
                          <tr key={l.product_id}>
                            <td>{p?.name}</td>
                            <td>{l.quantity}</td>
                            <td>{p ? fmt(p.price * l.quantity) : "—"}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                  <p className="hint">
                    Fecha: {saleDate} · Pago: {PAYMENT_LABELS[paymentMethod]}
                  </p>
                  <div className="total-box">Total: <strong>{fmt(total)}</strong></div>
                  <div className="modal-actions">
                    <button type="button" className="btn" onClick={() => setConfirmOpen(false)}>Volver al carrito</button>
                    <button type="submit" className="btn btn-primary" disabled={submitting}>
                      {submitting ? "Registrando…" : "Confirmar y registrar"}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </form>
        )}
      </div>
      </div>

      {confirmed && (
        <div className="modal-backdrop">
          <div className="modal">
            <h2>✓ Venta registrada</h2>
            <p>
              La venta <strong>{confirmed.sale_number}</strong> fue registrada
              correctamente. El stock ya fue descontado automáticamente.
            </p>
            <div className="cards" style={{ gridTemplateColumns: "1fr 1fr" }}>
              <div className="card"><span className="card-label">Total</span><span className="card-value">{fmt(confirmed.total)}</span></div>
              <div className="card"><span className="card-label">Pago</span><span className="card-value">{PAYMENT_LABELS[confirmed.payment_method as PaymentMethod] ?? confirmed.payment_method}</span></div>
            </div>
            <p className="hint">{confirmed.item_count} línea{s(confirmed.item_count)} · {confirmed.sale_date}</p>
            <div className="modal-actions">
              <button className="btn" onClick={() => setConfirmed(null)}>Cerrar</button>
              <button className="btn btn-primary" onClick={resetCart}>Nueva venta</button>
            </div>
          </div>
        </div>
      )}

      <h2>Ventas recientes</h2>
      {sales.length === 0 ? (
        <p className="hint">Aún no hay ventas registradas.</p>
      ) : (
        <div className="sale-list">
          {sales.map((s) => (
            <div key={s.id} className="sale-row">
              <div>
                <strong>{s.sale_number}</strong> · {s.sale_date} ·{" "}
                {PAYMENT_LABELS[s.payment_method as PaymentMethod] ?? s.payment_method} ·{" "}
                {s.source === "digitized" ? "digitalizada" : "manual"}
              </div>
              <div>{s.items.map((i) => `${i.product_name} ×${i.quantity}`).join(", ")}</div>
              <div className="sale-total">{fmt(s.total)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function s(n: number): string {
  return n === 1 ? "" : "s";
}