import Link from "next/link";
import { siteConfig } from "@/lib/config";
import type { Dictionary, Locale } from "@/lib/i18n";
import { WhatsAppIcon } from "./WhatsAppIcon";

type Props = {
  locale: Locale;
  dict: Dictionary;
};

export function SiteHeader({ locale, dict }: Props) {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-foam/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-4 px-4 sm:px-6">
        <Link
          href={`/${locale}/`}
          className="font-display text-[1.35rem] font-bold tracking-tight text-ink no-underline"
          aria-label={`${siteConfig.name}, home`}
        >
          {siteConfig.name}
        </Link>

        <nav
          aria-label="Primary"
          className="ml-4 hidden items-center gap-5 text-sm font-medium text-ink-soft md:flex"
        >
          <a href="#how" className="no-underline transition-colors hover:text-leaf">
            {dict.nav.how}
          </a>
          <a href="#shop" className="no-underline transition-colors hover:text-leaf">
            {dict.nav.shop}
          </a>
          <a href="#faq" className="no-underline transition-colors hover:text-leaf">
            {dict.nav.faq}
          </a>
        </nav>

        <div className="ml-auto flex items-center gap-2 sm:gap-3">
          <nav aria-label={dict.nav.langAria}>
            <ul className="flex items-center text-sm font-semibold">
              <li>
                {locale === "fr" ? (
                  <span
                    aria-current="true"
                    className="inline-flex min-h-10 min-w-10 items-center justify-center underline decoration-2 decoration-leaf underline-offset-4"
                  >
                    FR
                  </span>
                ) : (
                  <Link
                    href="/fr/"
                    hrefLang="fr"
                    lang="fr"
                    className="inline-flex min-h-10 min-w-10 items-center justify-center text-ink-soft no-underline hover:text-ink"
                    aria-label="FR, Français"
                  >
                    FR
                  </Link>
                )}
              </li>
              <li className="border-l border-line">
                {locale === "en" ? (
                  <span
                    aria-current="true"
                    className="inline-flex min-h-10 min-w-10 items-center justify-center underline decoration-2 decoration-leaf underline-offset-4"
                  >
                    EN
                  </span>
                ) : (
                  <Link
                    href="/en/"
                    hrefLang="en"
                    lang="en"
                    className="inline-flex min-h-10 min-w-10 items-center justify-center text-ink-soft no-underline hover:text-ink"
                    aria-label="EN, English"
                  >
                    EN
                  </Link>
                )}
              </li>
            </ul>
          </nav>

          <a
            href={siteConfig.whatsappUrl}
            className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-leaf px-3.5 text-sm font-semibold text-foam no-underline transition-colors hover:bg-leaf-deep sm:px-4"
          >
            <WhatsAppIcon className="h-[18px] w-[18px]" />
            <span className="hidden min-[400px]:inline">{dict.nav.tryCta}</span>
          </a>
        </div>
      </div>
    </header>
  );
}
