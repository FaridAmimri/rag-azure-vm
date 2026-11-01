"use client"; // Rendered on both sides, so `window` tells the server from the browser

// Runs before the first paint so the page never flashes in the wrong theme:
// the saved choice if there is one, otherwise the system setting.
const THEME_SCRIPT = `
  let theme = null;
  try { theme = localStorage.getItem("theme"); } catch {}
  if (theme !== "light" && theme !== "dark") {
    theme = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  document.documentElement.dataset.theme = theme;
`;

export default function ThemeScript() {
  // text/plain in the browser: React warns about <script> tags it renders there,
  // and only the copy in the server's HTML needs to run
  return (
    <script
      type={typeof window === "undefined" ? "text/javascript" : "text/plain"}
      suppressHydrationWarning
      dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }}
    />
  );
}
