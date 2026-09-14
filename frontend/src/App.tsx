import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import { RequireAuth } from "./components/RequireAuth";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Products from "./pages/ProductosPage";
import Sales from "./pages/Sales";
import DailySummary from "./pages/DailySummary";
import Inventory from "./pages/Inventory";
import Users from "./pages/Users";
import Recommendations from "./pages/Recommendations";
import Holidays from "./pages/Holidays";
import Profile from "./pages/Profile";
import SalesHome from "./pages/SalesHome";
import { homeFor } from "./navigation";

function RoleLanding() {
  const { user } = useAuth();
  return <Navigate to={homeFor(user?.role)} replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/*"
            element={
              <RequireAuth>
                <Layout>
                  <Routes>
                    <Route
                      path="/dashboard"
                      element={
                        <RequireAuth role="admin">
                          <Dashboard />
                        </RequireAuth>
                      }
                    />
                    <Route path="/sales" element={<Sales />} />
                    <Route path="/home" element={<SalesHome />} />
                    <Route path="/summary" element={<DailySummary />} />
                    <Route path="/products" element={<Products />} />
                    <Route path="/inventory" element={<Inventory />} />
                    <Route
                      path="/recommendations"
                      element={
                        <RequireAuth role="admin">
                          <Recommendations />
                        </RequireAuth>
                      }
                    />
                    <Route
                      path="/holidays"
                      element={
                        <RequireAuth role="admin">
                          <Holidays />
                        </RequireAuth>
                      }
                    />
                    <Route
                      path="/users"
                      element={
                        <RequireAuth role="admin">
                          <Users />
                        </RequireAuth>
                      }
                    />
                    <Route path="/profile" element={<Profile />} />
                    <Route path="*" element={<RoleLanding />} />
                  </Routes>
                </Layout>
              </RequireAuth>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}