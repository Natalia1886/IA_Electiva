import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  Category,
  Holiday,
  Product,
} from "../api/types";
import {
  ProductPayload,
  fetchReferenceData,
  listProducts,
  createProduct,
  updateProduct,
  deactivateProduct,
  reactivateProduct,
  serverFieldErrors,
  ServerFieldErrors,
  stockStatusOf,
} from "../api/productosApi";
import { useAuth } from "../auth/AuthContext";
import styles from "./ProductosPage.module.css";

const fmtCOP = (n: number) => n.toLocaleString("es-CO", { style: "currency", currency: "COP" });
const fmtNum = (n: number) => n.toLocaleString("es-MX");

const PAGE_SIZES = [10, 20, 50];

interface Toast {
  id: number;
  kind: "success" | "error";
  text: string;
}

const PAGE_SIZE = 10;

export default function ProductosPage() {
  const { isAdmin } = useAuth();
  const [products, setProducts] = useState<Product[] | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [holidays, setHolidays] = useState<Holiday[]>([]);

  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [lowOnly, setLowOnly] = useState(false);

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(PAGE_SIZE);

  const [error, setError] = useState<string | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [editor, setEditor] = useState<{ product: Product | null } | null>(null);
  const [confirmTarget, setConfirmTarget] = useState<Product | null>(null);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const toastSeq = useRef(1);

  const pushToast = (kind: Toast["kind"], text: string) => {
    const id = toastSeq.current++;
    setToasts((t) => [...t, { id, kind, text }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 5000);
  };

  const load = async (query: string, cat: string, low: boolean) => {
    try {
      setProducts(
        await listProducts({
          search: query,
          categoryId: cat ? Number(cat) : null,
          lowOnly: low,
        })
      );
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    let active = true;
    fetchReferenceData()
      .then(({ categories, holidays }) => {
        if (!active) return;
        setCategories(categories);
        setHolidays(holidays);
      })
      .catch((e) => active && setError((e as Error).message));
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      void load(search, categoryFilter, lowOnly);
      setPage(1);
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [search, categoryFilter, lowOnly]);

  const totalPages = Math.max(1, Math.ceil((products?.length ?? 0) / pageSize));
  const safePage = Math.min(page, totalPages);
  const pageItems = useMemo(() => {
    if (!products) return [];
    const from = (safePage - 1) * pageSize;
    return products.slice(from, from + pageSize);
  }, [products, safePage, pageSize]);

  const totals = useMemo(() => {
    const active = products?.filter((p) => p.is_active) ?? [];
    const out = active.filter((p) => stockStatusOf(p) === "out_of_stock").length;
    const low = active.filter((p) => stockStatusOf(p) === "low").length;
    return { total: active.length, low, out };
  }, [products]);

  const refresh = () => void load(search, categoryFilter, lowOnly);

  const onSaved = (msg: string) => {
    setEditor(null);
    pushToast("success", msg);
    refresh();
  };

  const deactivate = async (p: Product) => {
    try {
      await deactivateProduct(p.id);
      setConfirmTarget(null);
      pushToast("success", `"${p.name}" quedó desactivado. Sus datos se conservan.`);
      refresh();
    } catch (e) {
      setConfirmTarget(null);
      pushToast("error", (e as Error).message);
    }
  };

  const reactivate = async (p: Product) => {
    try {
      await reactivateProduct(p.id);
      pushToast("success", `"${p.name}" volvió a estar disponible para la venta.`);
      refresh();
    } catch (e) {
      pushToast("error", (e as Error).message);
    }
  };

  return (
    <div className={styles.page}>
      <header className={styles.head}>
        <div>
          <h1 className={styles.title}>Catálogo de productos</h1>
          <p className={styles.subtitle}>
            {products
              ? `${totals.total} producto${totals.total === 1 ? "" : "s"} · ${totals.low} con stock bajo · ${totals.out} agotado${totals.out === 1 ? "" : "s"}`
              : "Gestiona el inventario de tu tienda"}
          </p>
        </div>
        {isAdmin && (
          <div className={styles.headActions}>
            <button className={`${styles.btn} ${styles.btnPrimary}`} onClick={() => setEditor({ product: null })}>
              + Nuevo producto
            </button>
          </div>
        )}
      </header>

      <div className={styles.toolbar}>
        <input
          className={styles.input}
          placeholder="Buscar por nombre o código…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className={styles.select} value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
          <option value="">Todas las categorías</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
        <label className={styles.check}>
          <input type="checkbox" checked={lowOnly} onChange={(e) => setLowOnly(e.target.checked)} />
          Solo stock bajo
        </label>
      </div>

      {error && (
        <div className={styles.banner} role="alert">
          No se pudieron cargar los productos.
          <button className={`${styles.btn} ${styles.btnGhost}`} onClick={refresh}>
            Reintentar
          </button>
        </div>
      )}

      {editor && (
        <EditorDrawer
          product={editor.product}
          categories={categories}
          holidays={holidays}
          onClose={() => setEditor(null)}
          onSaved={onSaved}
        />
      )}

      {confirmTarget && (
        <ConfirmModal
          product={confirmTarget}
          onCancel={() => setConfirmTarget(null)}
          onConfirm={() => void deactivate(confirmTarget)}
        />
      )}

      {!products ? (
        <div className={styles.loading}>
          <span className={styles.spinner} aria-hidden />
          Cargando productos…
        </div>
      ) : pageItems.length === 0 ? (
        <div className={styles.empty}>
          {search || categoryFilter || lowOnly
            ? "No hay productos que coincidan con los filtros aplicados."
            : "Aún no hay productos en el catálogo. Agrega el primero con «Nuevo producto»."}
        </div>
      ) : (
        <>
          <div className={styles.card}>
            <table className={styles.table}>
              <thead className={styles.thead}>
                <tr>
                  <th>Código</th>
                  <th>Producto</th>
                  <th>Categoría</th>
                  <th>Precio</th>
                  <th>Existencia</th>
                  <th>Mínimo</th>
                  <th>Estado</th>
                  {isAdmin && <th style={{ textAlign: "right" }}>Acciones</th>}
                </tr>
              </thead>
              <tbody className={styles.tbody}>
                {pageItems.map((p, i) => (
                  <tr key={p.id} className={`${styles.trow}${i === pageItems.length - 1 ? ` ${styles.trowLast}` : ""}`}>
                    <td className={styles.codeCell}>{p.code}</td>
                    <td className={styles.nameCell}>{p.name}</td>
                    <td>{p.category_name ?? "—"}</td>
                    <td className={styles.priceCell}>{fmtCOP(p.price)}</td>
                    <td className={styles.stockCell}>{fmtNum(p.stock)}</td>
                    <td className={styles.minCell}>{fmtNum(p.min_stock)}</td>
                    <td>
                      <StockBadge product={p} />
                    </td>
                    {isAdmin && (
                      <td className={styles.actionsCell}>
                        {p.is_active ? (
                          <>
                            <button className={`${styles.btn} ${styles.btnGhost}`} onClick={() => setEditor({ product: p })}>
                              Editar
                            </button>
                            <button className={`${styles.btn} ${styles.btnDanger}`} onClick={() => setConfirmTarget(p)}>
                              Desactivar
                            </button>
                          </>
                        ) : (
                          <button className={`${styles.btn} ${styles.btnLink}`} onClick={() => void reactivate(p)}>
                            Activar de nuevo
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className={styles.pager}>
            <span className={styles.pagerInfo}>
              {products.length === 0 ? 0 : (safePage - 1) * pageSize + 1}–
              {Math.min(safePage * pageSize, products.length)} de {products.length}
            </span>
            <select className={styles.select} value={pageSize} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}>
              {PAGE_SIZES.map((s) => (
                <option key={s} value={s}>{s} por página</option>
              ))}
            </select>
            <button className={`${styles.btn} ${styles.btnGhost}`} disabled={safePage <= 1} onClick={() => setPage(safePage - 1)}>
              ‹ Anterior
            </button>
            <span className={styles.pagerInfo}>Página {safePage} de {totalPages}</span>
            <button className={`${styles.btn} ${styles.btnGhost}`} disabled={safePage >= totalPages} onClick={() => setPage(safePage + 1)}>
              Siguiente ›
            </button>
          </div>
        </>
      )}

      {toasts.length > 0 && (
        <div className={styles.toasts} aria-live="polite">
          {toasts.map((t) => (
            <div key={t.id} className={`${styles.toast} ${t.kind === "success" ? styles.toastSuccess : styles.toastError}`}>
              <span className={styles.toastDot} aria-hidden />
              {t.text}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function StockBadge({ product }: { product: Product }) {
  if (!product.is_active) {
    return <span className={`${styles.badge} ${styles.badgeNeutral}`}>Desactivado</span>;
  }
  const status = stockStatusOf(product);
  if (status === "out_of_stock") {
    return <span className={`${styles.badge} ${styles.badgeDanger}`}>Agotado</span>;
  }
  if (status === "low") {
    return <span className={`${styles.badge} ${styles.badgeWarn}`}>Stock bajo</span>;
  }
  return <span className={`${styles.badge} ${styles.badgeOk}`}>Stock normal</span>;
}

/* ── Formulario en panel lateral (drawer) ──────────────────── */

interface EditorForm {
  code: string;
  name: string;
  description: string;
  categoryId: number | null;
  price: string;
  cost: string;
  stock: string;
  minStock: string;
  active: boolean;
  holidayIds: number[];
}

type EditorFieldKey = keyof EditorForm;
type EditorErrors = Partial<Record<EditorFieldKey, string>>;

function EditorDrawer({
  product,
  categories,
  holidays,
  onClose,
  onSaved,
}: {
  product: Product | null;
  categories: Category[];
  holidays: Holiday[];
  onClose: () => void;
  onSaved: (msg: string) => void;
}) {
  const [form, setForm] = useState<EditorForm>(() => ({
    code: product?.code ?? "",
    name: product?.name ?? "",
    description: product?.description ?? "",
    categoryId: product?.category_id ?? null,
    price: product?.price != null ? String(product.price) : "",
    cost: product?.cost != null ? String(product.cost) : "",
    stock: product?.stock != null ? String(product.stock) : "0",
    minStock: product?.min_stock != null ? String(product.min_stock) : "0",
    active: product?.is_active ?? true,
    holidayIds: product?.holidays.map((h) => h.id) ?? [],
  }));
  const [clientErrors, setClientErrors] = useState<EditorErrors>({});
  const [serverErrors, setServerErrors] = useState<ServerFieldErrors>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const upd = (patch: Partial<EditorForm>) => setForm((f) => ({ ...f, ...patch }));
  const toggleHoliday = (id: number) =>
    upd({ holidayIds: form.holidayIds.includes(id) ? form.holidayIds.filter((h) => h !== id) : [...form.holidayIds, id] });

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const validate = (): EditorErrors => {
    const errs: EditorErrors = {};
    if (!form.code.trim()) errs.code = "Escribe un código para identificar el producto.";
    if (!form.name.trim()) errs.name = "Escribe el nombre del producto.";

    const price = Number(form.price);
    if (form.price.trim() === "" || Number.isNaN(price)) errs.price = "Escribe el precio de venta.";
    else if (price < 0) errs.price = "El precio no puede ser negativo.";

    if (form.cost.trim() !== "") {
      const cost = Number(form.cost);
      if (Number.isNaN(cost)) errs.cost = "Escribe un costo válido.";
      else if (cost < 0) errs.cost = "El costo no puede ser negativo.";
    }

    const stock = Number(form.stock);
    if (form.stock.trim() === "" || Number.isNaN(stock) || !Number.isInteger(stock))
      errs.stock = "La cantidad disponible debe ser un número entero.";
    else if (stock < 0) errs.stock = "La cantidad disponible no puede ser negativa.";

    const min = Number(form.minStock);
    if (form.minStock.trim() === "" || Number.isNaN(min) || !Number.isInteger(min))
      errs.minStock = "Debe ser un número entero.";
    else if (min < 0) errs.minStock = "No puede ser negativo.";

    return errs;
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const errs = validate();
    setClientErrors(errs);
    setServerErrors({});
    setServerError(null);
    if (Object.keys(errs).length > 0) return;

    const payload: ProductPayload = {
      code: form.code.trim(),
      name: form.name.trim(),
      description: form.description.trim() || null,
      category_id: form.categoryId,
      price: Number(form.price),
      cost: form.cost.trim() === "" ? null : Number(form.cost),
      stock: Number(form.stock),
      min_stock: Number(form.minStock),
      is_active: form.active,
      holiday_ids: form.holidayIds,
    };

    setSubmitting(true);
    try {
      if (product) {
        await updateProduct(product.id, payload);
        onSaved(`Los cambios de "${payload.name}" se guardaron.`);
      } else {
        await createProduct(payload);
        onSaved(`"${payload.name}" se agregó al catálogo.`);
      }
    } catch (err) {
      const fields = serverFieldErrors(err);
      if (Object.keys(fields).length > 0) setServerErrors(fields);
      else setServerError(err instanceof Error ? err.message : "Ocurrió un error al guardar.");
    } finally {
      setSubmitting(false);
    }
  };

  const serverKeyMap: Partial<Record<keyof ServerFieldErrors, EditorFieldKey>> = {
    code: "code",
    name: "name",
    category_id: "categoryId",
    price: "price",
    cost: "cost",
    stock: "stock",
    min_stock: "minStock",
    is_active: "active",
  };

  const fieldError = (key: EditorFieldKey): string | undefined => {
    if (clientErrors[key]) return clientErrors[key];
    const serverKey = Object.keys(serverErrors) as (keyof ServerFieldErrors)[];
    const found = serverKey.find((sk) => serverKeyMap[sk] === key);
    return found ? serverErrors[found] : undefined;
  };

  return (
    <>
      <div className={styles.backdrop} onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }} />
      <aside className={styles.drawer} role="dialog" aria-modal="true" aria-label={product ? "Editar producto" : "Nuevo producto"}>
        <header className={styles.drawerHeader}>
          <div>
            <h2 className={styles.drawerTitle}>{product ? "Editar producto" : "Nuevo producto"}</h2>
            <p className={styles.drawerSub}>
              {product ? `Código ${product.code} · revisa y guarda los cambios` : "Llena los datos para agregarlo al catálogo"}
            </p>
          </div>
          <button className={styles.closeBtn} onClick={onClose} aria-label="Cerrar">×</button>
        </header>

        <form className={styles.drawerBody} onSubmit={submit} noValidate>
          <div className={styles.formGrid}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="pp-code">Código</label>
              <input id="pp-code" value={form.code} onChange={(e) => upd({ code: e.target.value })} />
              {fieldError("code") && <span className={styles.fieldError}>{fieldError("code")}</span>}
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="pp-name">Nombre del producto</label>
              <input id="pp-name" value={form.name} onChange={(e) => upd({ name: e.target.value })} />
              {fieldError("name") && <span className={styles.fieldError}>{fieldError("name")}</span>}
            </div>
            <div className={`${styles.field} ${styles.full}`}>
              <label className={styles.label} htmlFor="pp-category">Categoría</label>
              <select id="pp-category" value={form.categoryId ?? ""} onChange={(e) => upd({ categoryId: e.target.value ? Number(e.target.value) : null })}>
                <option value="">Sin categoría</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
              {fieldError("categoryId") && <span className={styles.fieldError}>{fieldError("categoryId")}</span>}
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="pp-price">Precio de venta</label>
              <input id="pp-price" type="number" step="0.01" min="0" value={form.price} onChange={(e) => upd({ price: e.target.value })} />
              {fieldError("price") && <span className={styles.fieldError}>{fieldError("price")}</span>}
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="pp-cost">Costo</label>
              <input id="pp-cost" type="number" step="0.01" min="0" value={form.cost} onChange={(e) => upd({ cost: e.target.value })} />
              {fieldError("cost") && <span className={styles.fieldError}>{fieldError("cost")}</span>}
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="pp-stock">Cantidad disponible</label>
              <input id="pp-stock" type="number" step="1" min="0" value={form.stock} onChange={(e) => upd({ stock: e.target.value })} />
              {fieldError("stock") && <span className={styles.fieldError}>{fieldError("stock")}</span>}
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="pp-min">Avisarme cuando queden menos de</label>
              <input id="pp-min" type="number" step="1" min="0" value={form.minStock} onChange={(e) => upd({ minStock: e.target.value })} />
              {fieldError("minStock") && <span className={styles.fieldError}>{fieldError("minStock")}</span>}
            </div>

            <div className={styles.switchRow}>
              <span className={styles.switchText}>
                <span className={styles.switchLabel}>Disponible para la venta</span>
                <span className={styles.switchHint}>
                  Al desactivarlo deja de venderse, pero se conservan sus datos.
                </span>
                {fieldError("active") && <span className={styles.fieldError}>{fieldError("active")}</span>}
              </span>
              <button
                type="button"
                role="switch"
                aria-checked={form.active}
                aria-label="Disponible para la venta"
                className={`${styles.track}${form.active ? ` ${styles.trackOn}` : ""}`}
                onClick={() => upd({ active: !form.active })}
              >
                <span className={`${styles.thumb}${form.active ? ` ${styles.thumbOn}` : ""}`} />
              </button>
            </div>

            <div className={`${styles.field} ${styles.full}`}>
              <label className={styles.label} htmlFor="pp-desc">Descripción</label>
              <textarea id="pp-desc" value={form.description} onChange={(e) => upd({ description: e.target.value })} />
            </div>

            <div className={`${styles.field} ${styles.full}`}>
              <label className={styles.label}>Festividades asociadas</label>
              <div className={styles.chips}>
                {holidays.length === 0 && (
                  <span className={styles.drawerSub} style={{ color: "var(--muted)" }}>Sin festividades registradas.</span>
                )}
                {holidays.map((h) => (
                  <label key={h.id} className={styles.chip}>
                    <input
                      type="checkbox"
                      checked={form.holidayIds.includes(h.id)}
                      onChange={() => toggleHoliday(h.id)}
                    />
                    {h.name}
                  </label>
                ))}
              </div>
            </div>
          </div>

          {serverError && (
            <p className={styles.fieldError} style={{ marginTop: "1rem", fontSize: "0.9rem" }}>{serverError}</p>
          )}
        </form>

        <footer className={styles.drawerFooter}>
          <button className={`${styles.btn} ${styles.btnGhost}`} onClick={onClose}>Cancelar</button>
          <button className={`${styles.btn} ${styles.btnPrimary}`} onClick={submit} disabled={submitting}>
            {submitting ? "Guardando…" : product ? "Guardar cambios" : "Crear producto"}
          </button>
        </footer>
      </aside>
    </>
  );
}

/* ── Confirmación de desactivación ──────────────────────────── */

function ConfirmModal({
  product,
  onCancel,
  onConfirm,
}: {
  product: Product;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <>
      <div className={styles.backdrop} style={{ zIndex: 70 }} onMouseDown={(e) => { if (e.target === e.currentTarget) onCancel(); }} />
      <div className={styles.modalCard} role="dialog" aria-modal="true" aria-label="Desactivar producto">
        <h2 className={styles.modalTitle}>Desactivar producto</h2>
        <p className={styles.modalText}>
          <strong>«{product.name}»</strong> dejará de estar disponible para la venta.
        </p>
        <p className={styles.modalHint}>
          No es un borrado: se conservan sus datos y movimientos históricos, y podrás activarlo
          de nuevo en cualquier momento.
        </p>
        <div className={styles.modalActions}>
          <button className={`${styles.btn} ${styles.btnGhost}`} onClick={onCancel}>Cancelar</button>
          <button className={`${styles.btn} ${styles.btnPrimary}`} onClick={onConfirm}>Desactivar producto</button>
        </div>
      </div>
    </>
  );
}