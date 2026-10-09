"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import {
  buildCatalogStatusCard,
  catalogShareMessage,
} from "@/lib/catalogShareCard";
import { Product, Store } from "@/lib/api";

type Props = {
  store: Store;
  products: Product[];
};

export function CatalogShareButton({ store, products }: Props) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [blob, setBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  const catalogUrl =
    typeof window !== "undefined"
      ? `${window.location.origin}/shop/${store.slug}`
      : `https://komero.netlify.app/shop/${store.slug}`;

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [open]);

  async function ensureCard() {
    if (blob && previewUrl) return { blob, previewUrl };
    setBusy(true);
    setError(null);
    try {
      const nextBlob = await buildCatalogStatusCard({
        store,
        products,
        catalogUrl,
      });
      const url = URL.createObjectURL(nextBlob);
      setBlob(nextBlob);
      setPreviewUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return url;
      });
      return { blob: nextBlob, previewUrl: url };
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Impossible de generer l'image du catalogue",
      );
      throw err;
    } finally {
      setBusy(false);
    }
  }

  async function openShare() {
    setOpen(true);
    try {
      await ensureCard();
    } catch {
      // error already set
    }
  }

  function closeShare() {
    setOpen(false);
  }

  async function downloadImage() {
    try {
      const card = await ensureCard();
      const anchor = document.createElement("a");
      anchor.href = card.previewUrl;
      anchor.download = `${store.slug}-statut-whatsapp.jpg`;
      anchor.click();
    } catch {
      // error already set
    }
  }

  async function shareNative() {
    try {
      const card = await ensureCard();
      const file = new File([card.blob], `${store.slug}-statut-whatsapp.jpg`, {
        type: "image/jpeg",
      });
      const text = catalogShareMessage(store, catalogUrl);
      if (navigator.share && navigator.canShare?.({ files: [file], text })) {
        await navigator.share({
          files: [file],
          title: store.name,
          text,
        });
        return;
      }
      if (navigator.share) {
        await navigator.share({ title: store.name, text, url: catalogUrl });
        return;
      }
      await downloadImage();
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      setError("Partage indisponible. Téléchargez l'image puis ajoutez-la à votre statut.");
    }
  }

  function shareWhatsAppLink() {
    const text = encodeURIComponent(catalogShareMessage(store, catalogUrl));
    window.open(`https://wa.me/?text=${text}`, "_blank", "noopener,noreferrer");
  }

  const modal =
    open && mounted
      ? createPortal(
          <div
            className="shop-share-modal"
            role="dialog"
            aria-modal="true"
            aria-label="Partager le catalogue"
          >
            <div className="shop-share-backdrop" onClick={closeShare} />
            <div className="shop-share-panel">
              <div className="shop-share-head">
                <h2>Statut WhatsApp</h2>
                <button type="button" className="shop-share-close" onClick={closeShare}>
                  Fermer
                </button>
              </div>
              <p className="shop-share-help">
                Téléchargez l&apos;image du catalogue, puis ajoutez-la à votre statut WhatsApp.
                Le lien de la boutique est prêt à partager.
              </p>

              <div className="shop-share-preview">
                {previewUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={previewUrl} alt={`Carte statut ${store.name}`} />
                ) : (
                  <p>{busy ? "Génération de l'image…" : "Aperçu indisponible"}</p>
                )}
              </div>

              {error ? <p className="shop-share-error">{error}</p> : null}

              <div className="shop-share-actions">
                <button
                  type="button"
                  className="shop-share-primary"
                  disabled={busy}
                  onClick={() => void downloadImage()}
                >
                  Télécharger l&apos;image
                </button>
                <button
                  type="button"
                  className="shop-share-primary alt"
                  disabled={busy}
                  onClick={() => void shareNative()}
                >
                  Partager
                </button>
                <button
                  type="button"
                  className="shop-share-secondary"
                  onClick={shareWhatsAppLink}
                >
                  Lien WhatsApp
                </button>
              </div>
            </div>
          </div>,
          document.body,
        )
      : null;

  return (
    <>
      <button type="button" className="shop-share-btn" onClick={() => void openShare()}>
        Partager en statut WhatsApp
      </button>
      {modal}
    </>
  );
}
