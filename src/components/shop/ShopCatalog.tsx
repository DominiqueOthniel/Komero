"use client";

import Link from "next/link";
import {
  startTransition,
  useDeferredValue,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Category,
  formatXafShort,
  Product,
  Store,
} from "@/lib/api";
import { CatalogShareButton } from "@/components/shop/CatalogShareButton";
import { ProductMedia } from "@/components/shop/ProductMedia";

type SortKey = "featured" | "price_asc" | "price_desc" | "name";
type StockFilter = "all" | "in_stock";

type Props = {
  store: Store;
  products: Product[];
  categories: Category[];
};

function waOrderLink(store: Store, product: Product) {
  const number = (store.whatsapp_number || store.phone || "").replace(/[^\d]/g, "");
  const text = encodeURIComponent(
    `Bonjour, je suis interesse(e) par :\n${product.name}\nPrix : ${formatXafShort(product.price)}\nBoutique : ${store.name}`,
  );
  return number ? `https://wa.me/${number}?text=${text}` : `https://wa.me/?text=${text}`;
}

export function ShopCatalog({ store, products, categories }: Props) {
  const [query, setQuery] = useState("");
  const [categoryId, setCategoryId] = useState<string>("all");
  const [stock, setStock] = useState<StockFilter>("all");
  const [sort, setSort] = useState<SortKey>("featured");
  const [scrolledPast, setScrolledPast] = useState(false);
  const [filtersExpanded, setFiltersExpanded] = useState(false);
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const deferredQuery = useDeferredValue(query.trim().toLowerCase());

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel || typeof IntersectionObserver === "undefined") return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        const past = !entry.isIntersecting;
        setScrolledPast(past);
        if (!past) setFiltersExpanded(false);
      },
      { root: null, threshold: 0, rootMargin: "-8px 0px 0px 0px" },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, []);

  const categoryMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const category of categories) {
      map.set(category.id, category.name);
    }
    return map;
  }, [categories]);

  const filtered = useMemo(() => {
    let list = [...products];

    if (deferredQuery) {
      list = list.filter((product) => {
        const haystack = `${product.name} ${product.description || ""}`.toLowerCase();
        return haystack.includes(deferredQuery);
      });
    }

    if (categoryId === "uncategorized") {
      list = list.filter((product) => !product.category_id);
    } else if (categoryId !== "all") {
      list = list.filter((product) => product.category_id === categoryId);
    }

    if (stock === "in_stock") {
      list = list.filter((product) => product.stock_quantity > 0);
    }

    list.sort((a, b) => {
      const priceA = Number(a.price);
      const priceB = Number(b.price);
      if (sort === "price_asc") return priceA - priceB;
      if (sort === "price_desc") return priceB - priceA;
      if (sort === "name") return a.name.localeCompare(b.name, "fr");
      return 0;
    });

    return list;
  }, [products, deferredQuery, categoryId, stock, sort]);

  const accent = store.primary_color || "#0F6B5C";
  const hasUncategorized = products.some((product) => !product.category_id);
  const hasActiveFilters =
    Boolean(deferredQuery) || categoryId !== "all" || stock !== "all" || sort !== "featured";
  const compact = scrolledPast && !filtersExpanded;
  const filterClassName = [
    "shop-filters",
    "animate-rise-delay-2",
    compact ? "is-compact" : "",
    scrolledPast ? "is-sticky-active" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="shop-catalog" style={{ ["--shop-accent" as string]: accent }}>
      <header className="shop-masthead">
        <div className="shop-masthead-inner">
          <p className="shop-kicker">Boutique Komero</p>
          <h1 className="shop-title animate-rise">{store.name}</h1>
          <p className="shop-support animate-rise-delay-1">
            {store.description ||
              "Parcourez les articles, filtrez facilement, puis commandez sur WhatsApp."}
          </p>
          <p className="shop-count animate-rise-delay-2">
            {products.length} article{products.length === 1 ? "" : "s"}
          </p>
          <div className="shop-share-row animate-rise-delay-3">
            <CatalogShareButton store={store} products={products} />
          </div>
        </div>
      </header>

      <div className="shop-shell">
        <div ref={sentinelRef} className="shop-filter-sentinel" aria-hidden="true" />
        <section className={filterClassName} aria-label="Filtres catalogue">
          <div className="shop-filter-top">
            <label className="shop-search">
              <span className="sr-only">Rechercher un article</span>
              <input
                type="search"
                value={query}
                onChange={(event) => {
                  const value = event.target.value;
                  startTransition(() => setQuery(value));
                }}
                placeholder="Rechercher un article…"
                autoComplete="off"
              />
            </label>
            {scrolledPast ? (
              <button
                type="button"
                className={`shop-filter-toggle${hasActiveFilters ? " has-active" : ""}`}
                aria-expanded={!compact}
                onClick={() => setFiltersExpanded((open) => !open)}
              >
                {compact ? "Filtres" : "Réduire"}
                {hasActiveFilters && compact ? (
                  <span className="shop-filter-dot" aria-hidden="true" />
                ) : null}
              </button>
            ) : null}
          </div>

          <div className="shop-filter-details">
            <div className="shop-filter-row">
              <div className="shop-chips" role="list">
                <button
                  type="button"
                  role="listitem"
                  className={categoryId === "all" ? "is-active" : undefined}
                  onClick={() => startTransition(() => setCategoryId("all"))}
                >
                  Tous
                </button>
                {categories.map((category) => (
                  <button
                    key={category.id}
                    type="button"
                    role="listitem"
                    className={categoryId === category.id ? "is-active" : undefined}
                    onClick={() => startTransition(() => setCategoryId(category.id))}
                  >
                    {category.name}
                  </button>
                ))}
                {hasUncategorized ? (
                  <button
                    type="button"
                    role="listitem"
                    className={categoryId === "uncategorized" ? "is-active" : undefined}
                    onClick={() =>
                      startTransition(() => setCategoryId("uncategorized"))
                    }
                  >
                    Autres
                  </button>
                ) : null}
              </div>

              <div className="shop-controls">
                <label>
                  <span>Disponibilite</span>
                  <select
                    value={stock}
                    onChange={(event) =>
                      startTransition(() =>
                        setStock(event.target.value as StockFilter),
                      )
                    }
                  >
                    <option value="all">Tous</option>
                    <option value="in_stock">En stock</option>
                  </select>
                </label>
                <label>
                  <span>Trier</span>
                  <select
                    value={sort}
                    onChange={(event) =>
                      startTransition(() => setSort(event.target.value as SortKey))
                    }
                  >
                    <option value="featured">Par defaut</option>
                    <option value="price_asc">Prix croissant</option>
                    <option value="price_desc">Prix decroissant</option>
                    <option value="name">Nom A-Z</option>
                  </select>
                </label>
              </div>
            </div>

            <div className="shop-filter-meta">
              <p>
                {filtered.length} resultat{filtered.length === 1 ? "" : "s"}
                {deferredQuery ? ` pour « ${query.trim()} »` : ""}
              </p>
              {hasActiveFilters ? (
                <button
                  type="button"
                  className="shop-reset"
                  onClick={() => {
                    startTransition(() => {
                      setQuery("");
                      setCategoryId("all");
                      setStock("all");
                      setSort("featured");
                    });
                  }}
                >
                  Reinitialiser
                </button>
              ) : null}
            </div>
          </div>
        </section>

        {filtered.length === 0 ? (
          <div className="shop-empty">
            <h2>Aucun article trouve</h2>
            <p>Essayez un autre mot, une autre categorie, ou reinitialisez les filtres.</p>
            <button
              type="button"
              className="shop-reset solid"
              onClick={() => {
                startTransition(() => {
                  setQuery("");
                  setCategoryId("all");
                  setStock("all");
                  setSort("featured");
                });
              }}
            >
              Voir tous les articles
            </button>
          </div>
        ) : (
          <ul className="shop-grid">
            {filtered.map((product, index) => {
              const image =
                product.images[0]?.image_url || "/images/product-wax.jpg";
              const categoryName = product.category_id
                ? categoryMap.get(product.category_id)
                : null;
              const inStock = product.stock_quantity > 0;

              return (
                <li
                  key={product.id}
                  className="shop-item"
                  style={{ animationDelay: `${Math.min(index, 8) * 0.05}s` }}
                >
                  <Link
                    href={`/shop/${store.slug}/product/${product.id}`}
                    className="shop-item-link"
                  >
                    <div className="shop-item-media">
                      <ProductMedia
                        src={image}
                        alt={product.name}
                        sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
                        priority={index < 2}
                      />
                      <span
                        className={`shop-stock ${inStock ? "ok" : "out"}`}
                      >
                        {inStock ? "En stock" : "Epuise"}
                      </span>
                    </div>
                    <div className="shop-item-body">
                      {categoryName ? (
                        <p className="shop-item-category">{categoryName}</p>
                      ) : (
                        <p className="shop-item-category">Article</p>
                      )}
                      <h2>{product.name}</h2>
                      <p className="shop-item-price">
                        {formatXafShort(product.price)}
                      </p>
                    </div>
                  </Link>
                  <a
                    href={waOrderLink(store, product)}
                    className="shop-wa"
                    target="_blank"
                    rel="noreferrer"
                  >
                    Commander
                  </a>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
