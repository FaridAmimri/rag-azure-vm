"use client"; // Runs in the browser: needs the click event and localStorage

import styles from "./ThemeToggle.module.css";

export default function ThemeToggle() {
  function toggle() {
    const root = document.documentElement;
    const theme = root.dataset.theme === "dark" ? "light" : "dark";
    root.dataset.theme = theme;
    try {
      localStorage.setItem("theme", theme);
    } catch {
      // Storage blocked (private window): the choice just won't be remembered
    }
  }

  // Both icons are always rendered: the CSS shows the right one from data-theme
  return (
    <button
      className={styles.toggle}
      type="button"
      onClick={toggle}
      aria-label="Basculer entre le mode clair et le mode sombre"
      title="Mode clair / sombre"
    >
      <svg className={styles.sun} viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
      </svg>
      <svg className={styles.moon} viewBox="0 0 24 24" aria-hidden="true">
        <path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z" />
      </svg>
    </button>
  );
}
