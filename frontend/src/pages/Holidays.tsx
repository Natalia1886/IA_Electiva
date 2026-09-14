import { FormEvent, useEffect, useMemo, useState } from "react";
import { apiDelete, apiGet, apiPatch, apiPost } from "../api/client";
import { Holiday, HolidayPayload, Product } from "../api/types";

const VARIABLE_LABELS: Record<string, string> = {
  easter: "Semana Santa (Pascua)",
  corpus_christi: "Corpus Christi",
};

const FACTOR_PRESETS = [
  { label: "Baja", value: 1.2 },
  { label: "Media", value: 1.5 },
  { label: "Alta", value: 2.0 },
];

function factorLabel(f: number): string {
  if (f >= 2.0) return "alta";
  if (f > 1.3) return "media";
  return "baja";
}

interface HolidayForm {
  name: string;
  variable_date_code: string;
  day: string;
  month: string;
  start_date: string;
  end_date: string;
  expected_demand_factor: string;
  description: string;
  product_ids: number[];
}

interface FormErrors {
  name?: string;
  factor?: string;
  dates?: string;
  day?: string;
}

function ProductNames({ ids, products }: { ids: number[]; products: Product[] }) {
  const byId = useMemo(() => new Map(products.map((p) => [p.id, p])), [products]);
  const names = ids.length
    ? ids.map((id) => byId.get(id)?.name ?? byId.get(id)?.code ?? `#${id}`)
    : ["Sin productos"];
  return <span className="hint">{names.join(", ")}</span>;
}

export default function Holidays() {
  const [holidays, setHolidays] = useState<Holiday[] | null>(null);
  const [products, setProducts] = useState<Product[]>([]);

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [modal, setModal] = useState<"new" | "edit" | null>(null);
  const [editing, setEditing] = useState<Holiday | null>(null);
  const [confirmDeactivate, setConfirmDeactivate] = useState<Holiday | null>(null);

  const load = async () => {
    try {
      setHolidays(await apiGet<Holiday[]>("/holidays"));
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    let active = true;
    apiGet<Product[]>("/products")
      .then((p) => active && setProducts(p))
      .catch((e) => active && setError((e as Error).message));
    void load();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!success) return;
    const t = setTimeout(() => setSuccess(null), 4000);
    return () => clearTimeout(t);
  }, [success]);

  const onSubmitted = (msg: string) => {
    setModal(null);
    setEditing(null);
    setSuccess(msg);
    void load();
  };

  const deactivate = async (h: Holiday) => {
    try {
      await apiDelete(`/holidays/${h.id}`);
      setConfirmDeactivate(null);
      setSuccess(`"${h.name}" fue desactivada.`);
      void load();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const renderDates = (h: Holiday) => {
    if (h.variable_date_code && VARIABLE_LABELS[h.variable_date_code]) {
      return VARIABLE_LABELS[h.variable_date_code];
    }
    if (h.start_date) {
      return `${h.start_date}${h.end_date ? ` → ${h.end_date}` : ""}`;
    }
    if (h.day && h.month) return `${h.day} de ${monthName(h.month)}`;
    return "—";
  };

  return (
    <div className="page">
      <div className="page-head">
        <h1>Festividades religiosas</h1>
        <button className="btn btn-primary" onClick={() => { setEditing(null); setModal("new"); }}>+ Nueva festividad</button>
      </div>

      {error && <p className="error">{error}</p>}
      {success && <p className="success">{success}</p>}

      {modal && (
        <HolidayFormModal
          key={editing?.id ?? "new"}
          holiday={editing}
          products={products}
          onClose={() => setModal(null)}
          onSaved={onSubmitted}
        />
      )}

      {confirmDeactivate && (
        <div className="modal-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) setConfirmDeactivate(null); }}>
          <div className="modal">
            <h2>Desactivar festividad</h2>
            <p>
              <strong>«{confirmDeactivate.name}»</strong> dejará de considerarse en las
              recomendaciones de compra y en las fechas próximas.
            </p>
            <p className="hint">No se borra: puedes reactivarla en cualquier momento.</p>
            <div className="modal-actions">
              <button className="btn" onClick={() => setConfirmDeactivate(null)}>Cancelar</button>
              <button className="btn btn-danger" onClick={() => void deactivate(confirmDeactivate)}>Desactivar festividad</button>
            </div>
          </div>
        </div>
      )}

      {!holidays ? (
        <p className="hint">Cargando festividades…</p>
      ) : holidays.length === 0 ? (
        <div className="panel empty-state"><p>Sin festividades registradas.</p></div>
      ) : (
        <table>
          <thead>
            <tr><th>Nombre</th><th>Fechas</th><th>Factor demanda</th><th>Productos asociados</th><th>Estado</th><th>Acciones</th></tr>
          </thead>
          <tbody>
            {holidays.map((h) => (
              <tr key={h.id}>
                <td>{h.name}</td>
                <td>{renderDates(h)}</td>
                <td>
                  <span className={`badge ${h.expected_demand_factor >= 2.0 ? "badge-warn" : h.expected_demand_factor >= 1.5 ? "badge-ok" : ""}`}>
                    {factorLabel(h.expected_demand_factor)} · x{h.expected_demand_factor.toFixed(1)}
                  </span>
                </td>
                <td><ProductNames ids={h.products.map((p) => p.id)} products={products} /></td>
                <td>
                  {h.is_active ? <span className="badge badge-ok">Activa</span> : <span className="badge">Desactivada</span>}
                </td>
                <td>
                  {!h.is_active ? (
                    <button className="btn btn-ghost" onClick={async () => {
                      await apiPatch<Holiday>(`/holidays/${h.id}`, { is_active: true });
                      setSuccess(`"${h.name}" volvió a estar activa.`);
                      void load();
                    }}>Activar</button>
                  ) : (
                    <>
                      <button className="btn btn-ghost" onClick={() => { setEditing(h); setModal("edit"); }}>Editar</button>
                      <button className="btn btn-ghost btn-danger" onClick={() => setConfirmDeactivate(h)}>Desactivar</button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function monthName(m: number): string {
  const names = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
  return names[m - 1] ?? String(m);
}

function HolidayFormModal({
  holiday, products, onClose, onSaved,
}: {
  holiday: Holiday | null;
  products: Product[];
  onClose: () => void;
  onSaved: (msg: string) => void;
}) {
  const [form, setForm] = useState<HolidayForm>(() => ({
    name: holiday?.name ?? "",
    variable_date_code: holiday?.variable_date_code ?? "",
    day: holiday?.day != null ? String(holiday.day) : "",
    month: holiday?.month != null ? String(holiday.month) : "",
    start_date: holiday?.start_date ?? "",
    end_date: holiday?.end_date ?? "",
    expected_demand_factor: holiday ? String(holiday.expected_demand_factor) : "1.5",
    description: holiday?.description ?? "",
    product_ids: holiday?.products.map((p) => p.id) ?? [],
  }));
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const upd = (patch: Partial<HolidayForm>) => setForm((f) => ({ ...f, ...patch }));

  const toggleProduct = (id: number) =>
    upd({ product_ids: form.product_ids.includes(id) ? form.product_ids.filter((x) => x !== id) : [...form.product_ids, id] });

  const validate = (): FormErrors => {
    const errs: FormErrors = {};
    if (!form.name.trim()) errs.name = "El nombre es obligatorio.";

    const factor = Number(form.expected_demand_factor);
    if (form.expected_demand_factor.trim() === "" || Number.isNaN(factor)) errs.factor = "Indica un factor.";
    else if (factor < 1) errs.factor = "El factor debe ser mayor o igual a 1.";

    const hasVariable = form.variable_date_code !== "";
    const day = form.day.trim();
    const month = form.month.trim();
    if ((day !== "" && month === "") || (month !== "" && day === "")) {
      errs.day = "Si indicas día/mes, debes completar ambos.";
    }
    if (
      !hasVariable && day === "" && month === "" && form.start_date === ""
    ) {
      errs.dates = "Indica una fecha: fija (día/mes), variable (Pascua/Corpus) o un rango explícito.";
    }
    if (form.start_date && form.end_date && form.end_date < form.start_date) {
      errs.dates = "La fecha de fin no puede ser anterior a la de inicio.";
    }
    return errs;
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const errs = validate();
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;

    setServerError(null);
    setSubmitting(true);
    const payload: HolidayPayload = {
      name: form.name.trim(),
      variable_date_code: form.variable_date_code || null,
      day: form.day.trim() !== "" ? Number(form.day) : null,
      month: form.month.trim() !== "" ? Number(form.month) : null,
      start_date: form.start_date || null,
      end_date: form.end_date || null,
      expected_demand_factor: Number(form.expected_demand_factor),
      description: form.description.trim() || null,
      product_ids: form.product_ids,
    };
    try {
      if (holiday) {
        await apiPatch<Holiday>(`/holidays/${holiday.id}`, payload);
        onSaved(`Festividad "${payload.name}" actualizada.`);
      } else {
        await apiPost<Holiday>("/holidays", payload);
        onSaved(`Festividad "${payload.name}" creada.`);
      }
    } catch (err) {
      setServerError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="modal modal-lg">
        <h2>{holiday ? "Editar festividad" : "Nueva festividad"}</h2>
        <form onSubmit={submit} noValidate>
          <div className="form-grid">
            <label>Nombre
              <input value={form.name} onChange={(e) => upd({ name: e.target.value })} />
              {errors.name && <span className="error">{errors.name}</span>}
            </label>
            <label>Fecha variable
              <select value={form.variable_date_code} onChange={(e) => upd({ variable_date_code: e.target.value })}>
                <option value="">Fija o rango de fechas</option>
                {Object.entries(VARIABLE_LABELS).map(([code, label]) => (
                  <option key={code} value={code}>{label}</option>
                ))}
              </select>
            </label>
            <label>Día (fecha fija)
              <input type="number" min={1} max={31} value={form.day} onChange={(e) => upd({ day: e.target.value })} />
              {errors.day && <span className="error">{errors.day}</span>}
            </label>
            <label>Mes (fecha fija)
              <input type="number" min={1} max={12} value={form.month} onChange={(e) => upd({ month: e.target.value })} />
            </label>
            <label>Fecha de inicio (temporada)
              <input type="date" value={form.start_date} onChange={(e) => upd({ start_date: e.target.value })} />
            </label>
            <label>Fecha de fin (temporada)
              <input type="date" value={form.end_date} onChange={(e) => upd({ end_date: e.target.value })} />
              {errors.dates && <span className="error">{errors.dates}</span>}
            </label>
          </div>

          <label>Factor de demanda esperado
            <div className="chips" style={{ alignItems: "center" }}>
              {FACTOR_PRESETS.map((p) => (
                <label key={p.label} className="chip">
                  <input
                    type="radio"
                    name="factor-preset"
                    checked={Number(form.expected_demand_factor) === p.value}
                    onChange={() => upd({ expected_demand_factor: String(p.value) })}
                  />
                  {p.label} (x{p.value})
                </label>
              ))}
              <input
                type="number"
                step="0.1"
                min={1}
                value={form.expected_demand_factor}
                onChange={(e) => upd({ expected_demand_factor: e.target.value })}
                style={{ width: 110 }}
              />
            </div>
            {errors.factor && <span className="error">{errors.factor}</span>}
          </label>

          <label>Descripción
            <textarea value={form.description} onChange={(e) => upd({ description: e.target.value })} />
          </label>

          <fieldset>
            <legend>Productos asociados (múltiples)</legend>
            <div className="chips">
              {products.map((p) => (
                <label key={p.id} className="chip">
                  <input type="checkbox" checked={form.product_ids.includes(p.id)} onChange={() => toggleProduct(p.id)} />
                  {p.code} · {p.name}
                </label>
              ))}
            </div>
          </fieldset>

          {serverError && <p className="error">{serverError}</p>}
          <div className="modal-actions">
            <button type="button" className="btn" onClick={onClose}>Cancelar</button>
            <button className="btn btn-primary" type="submit" disabled={submitting}>
              {submitting ? "Guardando…" : holiday ? "Guardar cambios" : "Crear"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}