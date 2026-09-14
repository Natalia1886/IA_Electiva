export type Role = "admin" | "salesperson";

export interface User {
  id: number;
  username: string;
  email: string | null;
  full_name: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export interface Category {
  id: number;
  name: string;
  description: string | null;
  is_active: boolean;
}

export interface HolidayProductRef {
  id: number;
  code: string;
  name: string;
}

export interface Holiday {
  id: number;
  name: string;
  day: number | null;
  month: number | null;
  variable_date_code: string | null;
  start_date: string | null;
  end_date: string | null;
  expected_demand_factor: number;
  description: string | null;
  is_active: boolean;
  products: HolidayProductRef[];
}

export interface HolidayPayload {
  name: string;
  day?: number | null;
  month?: number | null;
  variable_date_code?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  expected_demand_factor: number;
  description?: string | null;
  is_active?: boolean;
  product_ids: number[];
}

export interface Product {
  id: number;
  code: string;
  name: string;
  description: string | null;
  category_id: number | null;
  category_name?: string | null;
  price: number;
  cost: number | null;
  stock: number;
  min_stock: number;
  is_active: boolean;
  holidays: Holiday[];
  low_stock: boolean;
}

export interface SaleItem {
  id: number;
  product_id: number;
  product_name: string | null;
  product_code: string | null;
  quantity: number;
  unit_price: number;
  subtotal: number;
}

export type PaymentMethod = "cash" | "card" | "transfer";

export const PAYMENT_LABELS: Record<PaymentMethod, string> = {
  cash: "Efectivo",
  card: "Tarjeta",
  transfer: "Transferencia",
};

export interface Sale {
  id: number;
  sale_number: string | null;
  sale_date: string;
  total: number;
  status: string;
  source: string;
  payment_method: string;
  salesperson_id: number | null;
  salesperson_name: string | null;
  digitization_id: number | null;
  created_at: string;
  items: SaleItem[];
  item_count: number;
}

export interface SaleItemIn {
  product_id: number;
  quantity: number;
  unit_price?: number;
}

export interface SaleCreatePayload {
  sale_date: string;
  items: SaleItemIn[];
  payment_method: PaymentMethod;
  digitization_id?: number | null;
}

export interface DailySummary {
  date: string;
  total_value: number;
  transaction_count: number;
  units_sold: number;
  products_count: number;
  items: { product_id: number; code: string; name: string; units_sold: number; total_value: number }[];
  top_products: { product_id: number; code: string; name: string; units_sold: number; total_value: number }[];
}

export interface StockMovement {
  id: number;
  product_id: number;
  product_name: string | null;
  product_code: string | null;
  quantity: number;
  movement_type: string;
  reason: string | null;
  reference_sale_id: number | null;
  user_id: number | null;
  created_at: string;
}

export type StockStatus = "normal" | "low" | "out_of_stock";

export interface InventoryItem {
  product_id: number;
  code: string;
  name: string;
  category_name: string | null;
  stock: number;
  min_stock: number;
  stock_status: StockStatus;
  low_stock: boolean;
  out_of_stock: boolean;
}

export interface LowStockAlert extends InventoryItem {
  missing_units: number;
}

export interface Dashboard {
  today: string;
  today_sales_value: number;
  today_transactions: number;
  today_units: number;
  week_trend: { date: string; total: number; transactions: number }[];
  low_stock_products: LowStockAlert[];
  total_products: number;
  total_stock_value: number;
  top_products_30d: { product_id: number; code: string; name: string; units_sold: number; total_value: number }[];
}

export interface RecommendationItem {
  product_id: number;
  code: string;
  name: string;
  current_stock: number;
  min_stock: number;
  sold_last_30_days: number;
  upcoming_holiday: string | null;
  segment: string | null;
  estimated_demand: number;
  suggested_quantity: number;
  reason: string | null;
  rationale: string;
}

export interface Recommendation {
  generated_for: string;
  source: string;
  items: RecommendationItem[];
  summary: string | null;
}