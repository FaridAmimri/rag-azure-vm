import Search from "@/components/Search";
import ThemeToggle from "@/components/ThemeToggle";
import styles from "./page.module.css";

export default function Home() {
  return (
    <main className={styles.main}>
      <ThemeToggle />
      <p className={styles.eyebrow}>1 220 pages · Azure Virtual Machines</p>
      <h1 className={styles.title}>Une question sur vos VM Azure ?</h1>
      <p className={styles.intro}>
        Obtenez une réponse tirée de la documentation Microsoft, avec les pages
        qui la justifient.
      </p>
      <Search />
    </main>
  );
}
