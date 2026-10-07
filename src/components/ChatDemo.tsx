import type { Dictionary } from "@/lib/i18n";

type Props = {
  dict: Dictionary;
};

export function ChatDemo({ dict }: Props) {
  return (
    <section className="px-4 py-8 sm:px-6 sm:py-12">
      <div className="mx-auto grid max-w-6xl items-center gap-12 lg:grid-cols-[1fr_1.05fr]">
        <div className="max-w-xl">
          <h2 className="font-display text-[clamp(1.8rem,3.5vw,2.75rem)] font-bold tracking-tight text-ink">
            {dict.demo.title}
          </h2>
          <p className="mt-3 text-lg leading-relaxed text-ink-soft">{dict.demo.support}</p>
        </div>

        <div
          className="overflow-hidden rounded-[1.75rem] border border-line bg-[#0b2f28] p-3 shadow-[0_24px_60px_rgba(14,31,28,0.18)]"
          aria-label="WhatsApp conversation preview"
        >
          <div className="rounded-[1.35rem] bg-[#efeae2] px-3 py-4 sm:px-4">
            <div className="mb-4 flex items-center gap-3 border-b border-black/5 pb-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-leaf font-display text-sm font-bold text-citron">
                K
              </div>
              <div>
                <p className="text-sm font-semibold text-ink">Komero</p>
                <p className="text-xs text-ink-soft">online</p>
              </div>
            </div>

            <ul className="flex flex-col gap-2.5">
              {dict.demo.lines.map((line, index) => {
                const isYou = line.who === "you";
                return (
                  <li
                    key={`${line.who}-${index}`}
                    className={`chat-line max-w-[92%] rounded-2xl px-3.5 py-2.5 text-[14px] leading-snug ${
                      isYou
                        ? "ml-auto rounded-br-md bg-[#d9fdd3] text-ink"
                        : "mr-auto rounded-bl-md bg-white text-ink"
                    }`}
                    style={{ animationDelay: `${index * 90}ms` }}
                  >
                    <span className="mb-1 block text-[11px] font-semibold uppercase tracking-wide text-ink-soft/80">
                      {isYou ? dict.demo.you : dict.demo.bot}
                    </span>
                    {line.text}
                  </li>
                );
              })}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
