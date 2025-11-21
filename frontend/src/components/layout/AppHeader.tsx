import React, { useContext } from "react";
import { NavLink } from "react-router-dom";
import { UserContext } from "../../context/user";

const NAV_LINKS = [
    { to: "/analisis", label: "Análisis PU" },
    { to: "/catalogo", label: "Catálogo" },
    { to: "/comparador", label: "Comparador" },
];
const ADMIN_LINK = { to: "/admin", label: "Administración" };

export function AppHeader() {
    const user = useContext(UserContext);
    const navLinks = user?.is_admin ? [...NAV_LINKS, ADMIN_LINK] : NAV_LINKS;

    return (
        <header className="app-header">
            <div className="brand">Precios Unitarios</div>
            <nav>
                {navLinks.map((link) => (
                    <NavLink key={link.to} to={link.to} className={({ isActive }) => (isActive ? "active" : undefined)}>
                        {link.label}
                    </NavLink>
                ))}
            </nav>
        </header>
    );
}
