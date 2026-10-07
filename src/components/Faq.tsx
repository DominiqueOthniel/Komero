import type { Dictionary } from "@/lib/i18n";

type Props = {
  dict: Dictionary;
};

export function Faq({ dict }: Props) {
  return (
    <section id="faq" className="scroll-mt-20 px-4 py-16 sm:px-6 sm:py-24">
      <div className="mx-auto max-w-3xl">
        <h2 className="font-display text-[clamp(1.8rem,3.5vw,2.75rem)] font-bold tracking-tight text-ink">
          {dict.faq.title}
        </h2>
        <p className="mt-3 text-lg leading-relaxed text-ink-soft">{dict.faq.support}</p>

        <div className="mt-10 divide-y divide-line border-y border-line">
          {dict.faq.items.map((item) => (
            <details key={item.q} className="group py-5">
              <summary className="cursor-pointer list-none font-display text-lg font-semibold text-ink marker:content-none [&::-webkit-details-marker]:hidden">
                <span className="flex items-start justify-between gap-4">
                  {item.q}
                  <span
                    className="mt-1 text-leaf transition-transform group-open:rotate-45"
                    aria-hidden="true"
                  >
                    +
                  </span>
                </span>
              </summary>
              <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-ink-soft">
                {item.a}
              </p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}
