import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <nav className="navbar">
      <Link to="/" className="brand">MediAI</Link>
      <div className="nav-links">
        <Link to="/">Dashboard</Link>
        <Link to="/image">Image Detection</Link>
        <Link to="/clinical">Clinical Data</Link>
        <Link to="/history">History</Link>
        {user?.role === "admin" && <Link to="/admin">Admin</Link>}
      </div>
      <div className="nav-user">
        <span>{user?.full_name} ({user?.role})</span>
        <button
          className="btn btn-small"
          onClick={() => {
            logout();
            navigate("/login");
          }}
        >
          Logout
        </button>
      </div>
    </nav>
  );
}