import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { api } from "./lib/api";
import Dashboard from "./pages/Dashboard";
import EmployeeDetail from "./pages/EmployeeDetail";
import Employees from "./pages/Employees";
import ImportPage from "./pages/ImportPage";
import Login from "./pages/Login";
import NewEmployee from "./pages/NewEmployee";

const client = new QueryClient();

function RequireAuth() {
  const [state, setState] = useState<"loading" | "in" | "out">("loading");
  useEffect(() => {
    api
      .me()
      .then(() => setState("in"))
      .catch(() => setState("out"));
  }, []);
  if (state === "loading") return <p className="muted">Checking session…</p>;
  if (state === "out") return <Navigate to="/login" replace />;
  return <Layout />;
}

export default function App() {
  return (
    <QueryClientProvider client={client}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<RequireAuth />}>
          <Route index element={<Dashboard />} />
          <Route path="employees" element={<Employees />} />
          <Route path="employees/new" element={<NewEmployee />} />
          <Route path="employees/:id" element={<EmployeeDetail />} />
          <Route path="import" element={<ImportPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </QueryClientProvider>
  );
}
