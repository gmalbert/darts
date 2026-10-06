import { NavLink, Outlet, useLocation } from "react-router-dom";

const NAV = [
  { label: "Home", path: "/", icon: "\uD83C\uDFAF" },
  { label: "Players", path: "/players", icon: "\uD83D\uDC64" },
  { label: "Matches", path: "/matches", icon: "\uD83C\uDFAE" },
  { label: "Tournaments", path: "/tournaments", icon: "\uD83C\uDFC6" },
  { label: "Odds", path: "/odds", icon: "\uD83D\uDCCA" },
  { label: "Tools", path: "/tools", icon: "\uD83D\uDD27" },
];

export function Shell() {
  const location = useLocation();
  const isHome = location.pathname === "/";

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <nav className="sidebar-nav">
          <span className="sidebar-section">Main</span>
          {NAV.map((n) => (
            <NavLink
              key={n.path}
              to={n.path}
              end={n.path === "/"}
              className={({ isActive }) => isActive ? "active" : ""}
            >
              {n.icon} {n.label}
            </NavLink>
          ))}
        </nav>
        {!isHome && (
          <a href="/" style={{ textDecoration: "none" }}>
            <img src="/logo.png" alt="BullzIQ" className="sidebar-logo" />
          </a>
        )}
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
