import type { Metadata } from "next";
import { LandingPage } from "@/components/LandingPage";
import { getDictionary } from "@/lib/i18n";

const dict = getDictionary("en");

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

export default function EnglishPage() {
  return <LandingPage locale="en" dict={dict} />;
}
