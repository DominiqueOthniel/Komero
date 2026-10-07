import { siteConfig } from "@/lib/config";
import type { Dictionary } from "@/lib/i18n";
import { WhatsAppIcon } from "./WhatsAppIcon";

type Props = {
  dict: Dictionary;
};

export function ClosingCta({ dict }: Props) {
  return (
    <section className="px-4 pb-20 pt-8 sm:px-6 sm:pb-28">
      <div className="relative mx-auto max-w-6xl overflow-hidden rounded-[2rem] bg-leaf px-6 py-14 text-foam sm:px-12 sm:py-16">
        <div
          className="pointer-events-none absolute -right-16 -top-20 h-64 w-64 rounded-full bg-citron/20 blur-2xl"
          aria-hidden="true"
        />
        <div
          className="pointer-events-none absolute -bottom-24 left-10 h-72 w-72 rounded-full bg-black/10 blur-2xl"
          aria-hidden="true"
        />

        <div className="relative max-w-2xl">
          <h2 className="font-display text-[clamp(1.8rem,3.8vw,2.9rem)] font-bold leading-tight tracking-tight">
            {dict.close.title}
          </h2>
          <p className="mt-4 text-lg leading-relaxed text-foam/85">{dict.close.support}</p>
          <a
            href={siteConfig.whatsappUrl}
            className="mt-8 inline-flex min-h-14 items-center gap-3 rounded-xl bg-citron px-6 text-base font-bold text-ink no-underline transition-transform hover:-translate-y-0.5 hover:bg-citron-deep sm:text-lg"
          >
            <WhatsAppIcon className="h-6 w-6" />
            <span>{dict.close.cta}</span>
          </a>
          <p className="mt-3 text-sm text-foam/70">{dict.close.note}</p>
        </div>
      </div>
    </section>
  );
}
