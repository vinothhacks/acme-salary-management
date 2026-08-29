import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import EmployeeDetail from "./pages/EmployeeDetail";
import Employees from "./pages/Employees";
import ImportPage from "./pages/ImportPage";
import Login from "./pages/Login";
import NewEmployee from "./pages/NewEmployee";

const client = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={client}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Layout />}>
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
