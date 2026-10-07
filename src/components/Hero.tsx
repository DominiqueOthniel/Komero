import Image from "next/image";
import { siteConfig } from "@/lib/config";
import type { Dictionary } from "@/lib/i18n";
import { WhatsAppIcon } from "./WhatsAppIcon";

type Props = {
  dict: Dictionary;
};

export function Hero({ dict }: Props) {
  return (
    <section className="relative isolate min-h-[calc(100svh-4rem)] overflow-hidden">
      <div className="absolute inset-0 -z-10">
        <Image
          src="/images/hero-commerce.jpg"
          alt=""
          fill
          priority
          sizes="100vw"
          className="animate-drift object-cover object-[center_35%]"
        />
        <div
          className="absolute inset-0"
          style={{ background: "var(--hero-veil)" }}
          aria-hidden="true"
        />
      </div>

      <div className="mx-auto flex min-h-[calc(100svh-4rem)] max-w-6xl flex-col justify-end px-4 pb-8 pt-8 sm:px-6 sm:pb-14 md:justify-center md:pb-20 md:pt-16">
        <p className="animate-rise font-display text-[clamp(2.4rem,11vw,5.75rem)] font-bold leading-[0.92] tracking-[-0.04em] text-citron">
          {dict.hero.brand}
        </p>

        <h1 className="animate-rise-delay-1 mt-3 max-w-2xl font-display text-[clamp(1.25rem,3.4vw,2.35rem)] font-semibold leading-[1.18] tracking-tight text-foam sm:mt-4">
          {dict.hero.headline}
        </h1>

        <p className="animate-rise-delay-2 mt-2.5 max-w-lg text-[15px] leading-relaxed text-foam/90 sm:mt-3 sm:text-base md:text-lg">
          {dict.hero.support}
        </p>

        <div className="animate-rise-delay-3 mt-5 flex flex-col items-start gap-2 sm:mt-8 sm:gap-3">
          <a
            href={siteConfig.whatsappUrl}
            className="group inline-flex min-h-12 items-center gap-2.5 rounded-xl bg-citron px-5 text-[15px] font-bold text-ink no-underline transition-transform hover:-translate-y-0.5 hover:bg-citron-deep sm:min-h-14 sm:gap-3 sm:px-6 sm:text-lg"
          >
            <WhatsAppIcon className="h-5 w-5 transition-transform group-hover:scale-110 sm:h-6 sm:w-6" />
            <span>{dict.hero.cta}</span>
          </a>
          <p className="text-xs text-foam/75 sm:text-sm">{dict.hero.secondary}</p>
          <span
            className="mt-1 h-1 w-24 rounded-full bg-citron animate-pulse-line sm:w-28"
            aria-hidden="true"
          />
        </div>
      </div>
    </section>
  );
}
