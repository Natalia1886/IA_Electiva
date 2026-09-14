import { ApiValidationError, apiDelete, apiGet, apiPatch, apiPost } from "./client";
import { Category, Holiday, Product } from "./types";

/**
 * Servicio centralizado del recurso "productos".
 * Todas las llamadas a la API pasan por aquí; la UI nunca llama a fetch directamente.
 */

export interface ProductPayload {
  code: string;
  name: string;
  description: string | null;
  category_id: number | null;
  price: number;
  cost: number | null;
  stock: number;
  min_stock: number;
  is_active: boolean;
  holiday_ids: number[];
}

export type ProductFieldKey =
  | "code"
  | "name"
  | "description"
  | "category_id"
  | "price"
  | "cost"
  | "stock"
  | "min_stock"
  | "is_active"
  | "holiday_ids";

export type ServerFieldErrors = Partial<Record<ProductFieldKey, string>>;

export interface ProductListQuery {
  search?: string;
  categoryId?: number | null;
  lowOnly?: boolean;
}

/** Categorías y festividades necesarias para el formulario de producto. */
export async function fetchReferenceData(): Promise<{ categories: Category[]; holidays: Holiday[] }> {
  const [categories, holidays] = await Promise.all([
    apiGet<Category[]>("/categories"),
    apiGet<Holiday[]>("/holidays"),
  ]);
  return { categories, holidays };
}

export async function listProducts(query: ProductListQuery = {}): Promise<Product[]> {
  const params = new URLSearchParams({ include_inactive: "true" });
  if (query.search) params.set("search", query.search);
  if (query.categoryId) params.set("category_id", String(query.categoryId));
  if (query.lowOnly) params.set("low_stock", "true");
  return apiGet<Product[]>(`/products?${params.toString()}`);
}

export async function createProduct(payload: ProductPayload): Promise<Product> {
  return apiPost<Product>("/products", {
    code: payload.code,
    name: payload.name,
    description: payload.description,
    category_id: payload.category_id,
    price: payload.price,
    cost: payload.cost,
    stock: payload.stock,
    min_stock: payload.min_stock,
    holiday_ids: payload.holiday_ids,
  });
}

export async function updateProduct(id: number, payload: ProductPayload): Promise<Product> {
  return apiPatch<Product>(`/products/${id}`, {
    code: payload.code,
    name: payload.name,
    description: payload.description,
    category_id: payload.category_id,
    price: payload.price,
    cost: payload.cost,
    stock: payload.stock,
    min_stock: payload.min_stock,
    is_active: payload.is_active,
    holiday_ids: payload.holiday_ids,
  });
}

/** Desactiva el producto: nunca lo borra del sistema. */
export async function deactivateProduct(id: number): Promise<void> {
  await apiDelete(`/products/${id}`);
}

export async function reactivateProduct(id: number): Promise<Product> {
  return apiPost<Product>(`/products/${id}/reactivate`);
}

/** Extrae los mensajes de validación del backend agrupados por campo. */
export function serverFieldErrors(err: unknown): ServerFieldErrors {
  if (err instanceof ApiValidationError) return err.fields as ServerFieldErrors;
  return {};
}

/** Estado visual de stock calculado en el frontend comparando existencia vs. mínimo. */
export type StockStatus = "out_of_stock" | "low" | "normal";

export function stockStatusOf(p: Pick<Product, "stock" | "min_stock">): StockStatus {
  if (p.stock <= 0) return "out_of_stock";
  if (p.stock <= p.min_stock) return "low";
  return "normal";
}