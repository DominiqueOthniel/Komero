const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type ApiError = {
  detail?: string | { msg: string }[];
};

export class ApiClientError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("komero_token");
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem("komero_token", token);
  else localStorage.removeItem("komero_token");
}

async function parseError(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as ApiError;
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) return data.detail.map((d) => d.msg).join(", ");
    return response.statusText;
  } catch {
    return response.statusText;
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  auth = false,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (auth) {
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    throw new ApiClientError(await parseError(response), response.status);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function login(email: string, password: string) {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  return apiFetch<{ access_token: string; token_type: string }>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
}

export async function register(payload: {
  name: string;
  email: string;
  password: string;
  phone?: string;
}) {
  return apiFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type Store = {
  id: string;
  owner_id: string;
  name: string;
  slug: string;
  description: string | null;
  logo_url: string | null;
  currency: string;
  phone: string | null;
  whatsapp_number: string | null;
  primary_color: string;
  status: string;
};

export type Product = {
  id: string;
  store_id: string;
  name: string;
  description: string | null;
  price: string;
  compare_price: string | null;
  stock_quantity: number;
  sku: string | null;
  category_id: string | null;
  status: string;
  images: { id: string; image_url: string; position: number }[];
  variants: {
    id: string;
    name: string;
    value: string;
    stock_quantity: number;
    price: string | null;
  }[];
};

export type DashboardStats = {
  total_sales: string;
  orders_count: number;
  products_count: number;
  customers_count: number;
  pending_orders: number;
};

export type Sale = {
  id: string;
  store_id: string;
  public_code: string;
  currency: string;
  total_amount: string;
  item_count: number;
  customer_name: string | null;
  status: string;
  created_at: string;
  items: {
    id: string;
    name: string;
    quantity: number;
    unit_price: string;
    total_price: string;
    product_id: string | null;
  }[];
  receipt: {
    id: string;
    number: string;
    customer_name: string | null;
    created_at: string;
    verification_url: string | null;
  } | null;
};

export type PublicReceipt = {
  number: string;
  store_name: string;
  store_phone: string | null;
  sale_code: string;
  customer_name: string | null;
  currency: string;
  total_amount: string;
  created_at: string;
  sale_date: string;
  items: {
    id: string;
    name: string;
    quantity: number;
    unit_price: string;
    total_price: string;
    product_id: string | null;
  }[];
  verification_url: string;
};

export function formatXaf(amount: string | number) {
  const value = typeof amount === "string" ? Number(amount) : amount;
  return new Intl.NumberFormat("fr-CM", {
    style: "currency",
    currency: "XAF",
    maximumFractionDigits: 0,
  }).format(value || 0);
}

export function formatXafShort(amount: string | number) {
  const value = typeof amount === "string" ? Number(amount) : amount;
  return `${new Intl.NumberFormat("fr-CM", { maximumFractionDigits: 0 }).format(value || 0)} F`;
}
