import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth";
import Navbar from "./components/Navbar";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import ImageDetect from "./pages/ImageDetect";
import ClinicalDetect from "./pages/ClinicalDetect";
import History from "./pages/History";
import Admin from "./pages/Admin";

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="container">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  const { user } = useAuth();
  return (
    <div className="app">
      {user && <Navbar />}
      <main className="main">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<Protected><Dashboard /></Protected>} />
          <Route path="/image" element={<Protected><ImageDetect /></Protected>} />
          <Route path="/clinical" element={<Protected><ClinicalDetect /></Protected>} />
          <Route path="/history" element={<Protected><History /></Protected>} />
          <Route path="/admin" element={<Protected><Admin /></Protected>} />
        </Routes>
      </main>
    </div>
  );
}