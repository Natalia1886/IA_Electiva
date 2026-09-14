import { Role } from "./api/types";

export const ADMIN_HOME = "/dashboard";
export const SALESPERSON_HOME = "/home";

export function homeFor(role: Role | undefined): string {
  return role === "admin" ? ADMIN_HOME : SALESPERSON_HOME;
}

export const ADMIN_ONLY_PATHS = ["/dashboard", "/users", "/recommendations", "/holidays"];