import { siteConfig } from "@/lib/config";
import type { Dictionary } from "@/lib/i18n";

type Props = {
  dict: Dictionary;
};

export function SiteFooter({ dict }: Props) {
  return (
    <footer className="border-t border-line px-4 py-10 sm:px-6">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="font-display text-xl font-bold text-ink">{siteConfig.name}</p>
          <p className="mt-1 text-sm text-ink-soft">{dict.footer.tagline}</p>
        </div>
        <p className="text-sm text-ink-soft">{dict.footer.rights}</p>
      </div>
    </footer>
  );
}
