import { redirect } from "next/navigation";

// Netlify also force-redirects `/` → `/en` in netlify.toml.
export default function Home() {
  redirect("/en/");
}
