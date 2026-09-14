import { ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { Role } from "../api/types";

interface NavEntry {
  to: string;
  label: string;
  roles: Role[];
}

function NavIcon({ path }: { path: string }) {
  const icons: Record<string, JSX.Element> = {
    "/dashboard": (
      <svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
    ),
    "/home": (
      <svg viewBox="0 0 24 24"><path d="M3 12l9-8 9 8"/><path d="M5 10v10h5v-6h4v6h5V10"/></svg>
    ),
    "/sales": (
      <svg viewBox="0 0 24 24"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
    ),
    "/summary": (
      <svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
    ),
    "/products": (
      <svg viewBox="0 0 24 24"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
    ),
    "/inventory": (
      <svg viewBox="0 0 24 24"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><path d="M3.27 6.96 12 12.01l8.73-5.05M12 22.08V12"/></svg>
    ),
    "/recommendations": (
      <svg viewBox="0 0 24 24"><path d="M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2z"/><line x1="9" y1="21" x2="15" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
    ),
    "/holidays": (
      <svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
    ),
    "/users": (
      <svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
    ),
    "/profile": (
      <svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
    ),
  };

  return icons[path] ?? null;
}

// The menu is GENERATED per role: entries whose `roles` array does not include the
// current role are filtered out, so restricted links never exist in the DOM.
const NAV_ITEMS: NavEntry[] = [
  { to: "/dashboard", label: "Panel", roles: ["admin"] },
  { to: "/home", label: "Inicio", roles: ["salesperson"] },
  { to: "/sales", label: "Ventas", roles: ["admin", "salesperson"] },
  { to: "/summary", label: "Resumen diario", roles: ["admin", "salesperson"] },
  { to: "/products", label: "Productos", roles: ["admin", "salesperson"] },
  { to: "/inventory", label: "Inventario", roles: ["admin", "salesperson"] },
  { to: "/recommendations", label: "Recomendaciones", roles: ["admin"] },
  { to: "/holidays", label: "Festividades", roles: ["admin"] },
  { to: "/users", label: "Usuarios", roles: ["admin"] },
  { to: "/profile", label: "Mi perfil", roles: ["admin", "salesperson"] },
];

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();

  const items = NAV_ITEMS.filter((item) => item.roles.includes(user?.role ?? "salesperson"));

  const onLogout = () => {
    logout();
    navigate("/login");
  };

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `nav-link${isActive ? " active" : ""}`;

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark" aria-hidden>M</span>
          <div>
            <strong>Milan</strong>
            <span className="brand-sub">Inventario y Ventas</span>
          </div>
        </div>
        <nav>
          {items.map((item) => (
            <NavLink key={item.to} to={item.to} className={linkClass}>
              <NavIcon path={item.to} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <NavLink to="/profile" className="nav-link footer-user" title="Mi perfil">
            <span className="user-avatar" aria-hidden>{user?.full_name?.charAt(0)}</span>
            <span className="user-name">{user?.full_name}</span>
          </NavLink>
          <span className={`role-badge ${user?.role}`}>
            {isAdmin ? "Administrador" : "Vendedor"}
          </span>
          <button className="nav-link logout-btn" onClick={onLogout}>
            <svg viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
            <span>Cerrar sesión</span>
          </button>
        </div>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}