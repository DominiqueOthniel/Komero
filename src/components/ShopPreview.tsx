import Image from "next/image";
import type { Dictionary } from "@/lib/i18n";

type Props = {
  dict: Dictionary;
};

export function ShopPreview({ dict }: Props) {
  return (
    <section id="shop" className="scroll-mt-20 px-4 py-20 sm:px-6 sm:py-28">
      <div className="mx-auto max-w-6xl">
        <div className="max-w-2xl">
          <h2 className="font-display text-[clamp(1.8rem,3.5vw,2.75rem)] font-bold tracking-tight text-ink">
            {dict.shop.title}
          </h2>
          <p className="mt-3 text-lg leading-relaxed text-ink-soft">{dict.shop.support}</p>
        </div>

        <div className="mt-12 grid items-start gap-10 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="overflow-hidden rounded-[1.75rem] border border-line bg-foam">
            <div className="border-b border-line px-5 py-4">
              <p className="font-display text-xl font-bold text-ink">{dict.shop.storeName}</p>
              <p className="text-sm text-ink-soft">{dict.shop.replies}</p>
            </div>
            <div className="grid gap-0 sm:grid-cols-2">
              {dict.shop.products.map((product) => (
                <article key={product.name} className="border-t border-line sm:odd:border-r">
                  <div className="relative aspect-[4/3] overflow-hidden bg-mist">
                    <Image
                      src={product.image}
                      alt={product.alt}
                      fill
                      sizes="(max-width: 640px) 100vw, 40vw"
                      className="object-cover transition-transform duration-700 hover:scale-105"
                    />
                  </div>
                  <div className="px-4 py-4">
                    <div className="flex items-baseline justify-between gap-3">
                      <h3 className="font-display text-lg font-semibold text-ink">
                        {product.name}
                      </h3>
                      <p className="text-sm font-semibold text-leaf">{product.price}</p>
                    </div>
                    <p className="mt-3 inline-flex text-sm font-semibold text-leaf">
                      {dict.shop.order}
                    </p>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <ul className="flex flex-col gap-6">
            {dict.shop.points.map((point, index) => (
              <li key={point} className="flex gap-4">
                <span
                  className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-leaf font-display text-sm font-bold text-citron"
                  aria-hidden="true"
                >
                  {index + 1}
                </span>
                <p className="text-base leading-relaxed text-ink-soft">{point}</p>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
