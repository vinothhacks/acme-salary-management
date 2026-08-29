import { NavLink, Outlet } from "react-router-dom";
import { api } from "../lib/api";

const links = [
  { to: "/", label: "Dashboard" },
  { to: "/employees", label: "Employees" },
  { to: "/import", label: "Import" },
];

export default function Layout() {
  return (
    <div className="app-frame">
      <aside className="rail">
        <p className="eyebrow">ACME</p>
        <h1 className="rail-title">Salary</h1>
        <nav>
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.to === "/"} className="rail-link">
              {link.label}
            </NavLink>
          ))}
        </nav>
        <button
          className="ghost"
          type="button"
          onClick={async () => {
            await api.logout();
            window.location.href = "/login";
          }}
        >
          Sign out
        </button>
      </aside>
      <div className="stage">
        <Outlet />
      </div>
    </div>
  );
}
