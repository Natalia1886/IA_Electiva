import { useAuth } from "../auth/AuthContext";

export default function Profile() {
  const { user, isAdmin } = useAuth();

  if (!user) return null;

  const joined = new Date(user.created_at).toLocaleDateString("es-MX", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  const row = (label: string, value: string | null) =>
    value ? (
      <div className="form-grid" style={{ gridTemplateColumns: "160px 1fr" }}>
        <span className="hint">{label}</span>
        <span>{value}</span>
      </div>
    ) : null;

  return (
    <>
      <div className="page-head">
        <h2>Mi perfil</h2>
        <span className={`badge ${isAdmin ? "badge-admin" : "badge-seller"}`}>
          {isAdmin ? "Administrador" : "Vendedor"}
        </span>
      </div>

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>{user.full_name}</h3>
        {row("Usuario", user.username)}
        {row("Correo", user.email)}
        {row("Rol", isAdmin ? "Administrador" : "Vendedor")}
        {row("Miembro desde", joined)}
        {row("Estado", user.is_active ? "Activo" : "Inactivo")}
      </div>

      <p className="hint">
        Información de la cuenta que tiene sesión iniciada. Si necesitas actualizar tu correo,
        nombre o contraseña, contacta a un administrador.
      </p>
    </>
  );
}