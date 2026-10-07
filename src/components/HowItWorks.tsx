import type { Dictionary } from "@/lib/i18n";

type Props = {
  dict: Dictionary;
};

export function HowItWorks({ dict }: Props) {
  return (
    <section id="how" className="scroll-mt-20 px-4 py-20 sm:px-6 sm:py-28">
      <div className="mx-auto max-w-6xl">
        <div className="max-w-2xl">
          <h2 className="font-display text-[clamp(1.8rem,3.5vw,2.75rem)] font-bold tracking-tight text-ink">
            {dict.how.title}
          </h2>
          <p className="mt-3 text-lg leading-relaxed text-ink-soft">{dict.how.support}</p>
        </div>

        <ol className="mt-14 grid gap-10 md:grid-cols-2 lg:grid-cols-4 lg:gap-8">
          {dict.how.steps.map((step, index) => (
            <li key={step.title} className="relative">
              <div className="font-display text-5xl font-bold leading-none text-leaf/25">
                {String(index + 1).padStart(2, "0")}
              </div>
              <h3 className="mt-3 font-display text-xl font-semibold text-ink">
                {step.title}
              </h3>
              <p className="mt-2 text-[15px] leading-relaxed text-ink-soft">{step.body}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
