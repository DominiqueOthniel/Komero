import type { Dictionary, Locale } from "@/lib/i18n";
import { ChatDemo } from "./ChatDemo";
import { ClosingCta } from "./ClosingCta";
import { Faq } from "./Faq";
import { Hero } from "./Hero";
import { HowItWorks } from "./HowItWorks";
import { ShopPreview } from "./ShopPreview";
import { SiteFooter } from "./SiteFooter";
import { SiteHeader } from "./SiteHeader";

type Props = {
  locale: Locale;
  dict: Dictionary;
};

export function LandingPage({ locale, dict }: Props) {
  return (
    <div className="flex min-h-full flex-col" lang={locale}>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded-lg focus:bg-ink focus:px-4 focus:py-2 focus:text-foam"
      >
        Skip to content
      </a>
      <SiteHeader locale={locale} dict={dict} />
      <main id="main" className="flex-1">
        <Hero dict={dict} />
        <HowItWorks dict={dict} />
        <ChatDemo dict={dict} />
        <ShopPreview dict={dict} />
        <Faq dict={dict} />
        <ClosingCta dict={dict} />
      </main>
      <SiteFooter dict={dict} />
    </div>
  );
}
