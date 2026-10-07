import type { Metadata } from "next";
import { LandingPage } from "@/components/LandingPage";
import { getDictionary } from "@/lib/i18n";

const dict = getDictionary("fr");

export const metadata: Metadata = {
  title: dict.meta.title,
  description: dict.meta.description,
  alternates: {
    languages: {
      en: "/en",
      fr: "/fr",
    },
  },
};

export default function FrenchPage() {
  return <LandingPage locale="fr" dict={dict} />;
}
