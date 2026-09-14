import { FormEvent, useEffect, useState } from "react";
import { apiGet, apiPatch, apiPost } from "../api/client";
import { Role, User } from "../api/types";

export default function Users() {
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    username: "",
    full_name: "",
    email: "",
    password: "",
    role: "salesperson" as Role,
  });

  const load = async () => {
    try {
      setUsers(await apiGet<User[]>("/users"));
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const create = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await apiPost<User>("/users", { ...form, email: form.email || null });
      await load();
      setForm({ username: "", full_name: "", email: "", password: "", role: "salesperson" });
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const toggleActive = async (u: User) => {
    try {
      await apiPatch<User>(`/users/${u.id}`, { is_active: !u.is_active });
      await load();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <div className="page">
      <h1>Usuarios</h1>
      {error && <p className="error">{error}</p>}

      <div className="panel">
        <h2>Nuevo usuario</h2>
        <form onSubmit={create}>
          <div className="form-grid">
            <label>Usuario<input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required /></label>
            <label>Nombre completo<input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required /></label>
            <label>Email<input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
            <label>Contraseña<input type="password" minLength={6} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required /></label>
            <label>Rol
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as Role })}>
                <option value="salesperson">Vendedor</option>
                <option value="admin">Administrador</option>
              </select>
            </label>
          </div>
          <button className="btn btn-primary" type="submit">Crear usuario</button>
        </form>
      </div>

      <table>
        <thead><tr><th>Usuario</th><th>Nombre</th><th>Rol</th><th>Estado</th><th>Acciones</th></tr></thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>{u.username}</td>
              <td>{u.full_name}</td>
              <td><span className={`badge ${u.role === "admin" ? "badge-admin" : "badge-seller"}`}>{u.role === "admin" ? "Administrador" : "Vendedor"}</span></td>
              <td>{u.is_active ? <span className="badge badge-ok">Activo</span> : <span className="badge badge-danger">Inactivo</span>}</td>
              <td><button className="btn btn-ghost" onClick={() => toggleActive(u)}>{u.is_active ? "Desactivar" : "Activar"}</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}