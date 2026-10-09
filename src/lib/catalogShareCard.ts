import { formatXafShort, Product, Store } from "@/lib/api";

const WIDTH = 1080;
const HEIGHT = 1920;

function loadImage(src: string): Promise<HTMLImageElement | null> {
  return new Promise((resolve) => {
    const img = new Image();
    if (src.startsWith("http://") || src.startsWith("https://")) {
      img.crossOrigin = "anonymous";
    }
    img.onload = () => resolve(img);
    img.onerror = () => resolve(null);
    img.src = src;
  });
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  const radius = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.arcTo(x + w, y, x + w, y + h, radius);
  ctx.arcTo(x + w, y + h, x, y + h, radius);
  ctx.arcTo(x, y + h, x, y, radius);
  ctx.arcTo(x, y, x + w, y, radius);
  ctx.closePath();
}

function drawCover(
  ctx: CanvasRenderingContext2D,
  img: HTMLImageElement,
  x: number,
  y: number,
  w: number,
  h: number,
) {
  const scale = Math.max(w / img.width, h / img.height);
  const dw = img.width * scale;
  const dh = img.height * scale;
  const dx = x + (w - dw) / 2;
  const dy = y + (h - dh) / 2;
  ctx.save();
  ctx.beginPath();
  ctx.rect(x, y, w, h);
  ctx.clip();
  ctx.drawImage(img, dx, dy, dw, dh);
  ctx.restore();
}

function wrapText(
  ctx: CanvasRenderingContext2D,
  text: string,
  maxWidth: number,
  maxLines: number,
) {
  const words = text.split(/\s+/).filter(Boolean);
  if (words.length === 0) return [];

  const ellipsize = (value: string) => {
    let last = value;
    while (ctx.measureText(`${last}…`).width > maxWidth && last.length > 1) {
      last = last.slice(0, -1);
    }
    return `${last}…`;
  };

  const lines: string[] = [];
  let current = "";
  for (let index = 0; index < words.length; index += 1) {
    const word = words[index];
    const next = current ? `${current} ${word}` : word;
    if (ctx.measureText(next).width > maxWidth && current) {
      lines.push(current);
      current = word;
      if (lines.length === maxLines) {
        lines[maxLines - 1] = ellipsize(lines[maxLines - 1]);
        return lines;
      }
    } else {
      current = next;
    }
  }
  if (current) {
    if (lines.length < maxLines) lines.push(current);
    else lines[maxLines - 1] = ellipsize(lines[maxLines - 1]);
  }
  return lines;
}

export async function buildCatalogStatusCard(options: {
  store: Store;
  products: Product[];
  catalogUrl: string;
}): Promise<Blob> {
  const { store, products, catalogUrl } = options;
  const accent = store.primary_color || "#0F6B5C";
  const canvas = document.createElement("canvas");
  canvas.width = WIDTH;
  canvas.height = HEIGHT;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Canvas unavailable");

  // Background atmosphere
  const gradient = ctx.createLinearGradient(0, 0, WIDTH, HEIGHT);
  gradient.addColorStop(0, "#F4FAF7");
  gradient.addColorStop(0.45, "#E8F2EE");
  gradient.addColorStop(1, "#DCEDE6");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  // Accent wash
  const wash = ctx.createRadialGradient(180, 160, 40, 180, 160, 520);
  wash.addColorStop(0, `${accent}33`);
  wash.addColorStop(1, "transparent");
  ctx.fillStyle = wash;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  // Header card
  ctx.fillStyle = "rgba(255,255,255,0.92)";
  roundRect(ctx, 64, 96, WIDTH - 128, 320, 36);
  ctx.fill();

  ctx.fillStyle = accent;
  ctx.font = "700 34px Manrope, sans-serif";
  ctx.fillText("BOUTIQUE KOMERO", 104, 170);

  ctx.fillStyle = "#0E1F1C";
  ctx.font = "800 72px Bricolage Grotesque, Manrope, sans-serif";
  const titleLines = wrapText(ctx, store.name, WIDTH - 240, 2);
  titleLines.forEach((line, index) => {
    ctx.fillText(line, 104, 260 + index * 78);
  });

  ctx.fillStyle = "#243833";
  ctx.font = "600 34px Manrope, sans-serif";
  const countLabel =
    products.length === 1 ? "1 article disponible" : `${products.length} articles disponibles`;
  ctx.fillText(countLabel, 104, 370);

  // Product grid (up to 4), sized for 1 / 2 / 3+ items
  const picks = products.slice(0, 4);
  const loaded = await Promise.all(
    picks.map(async (product) => {
      const src = product.images[0]?.image_url || "/images/product-wax.jpg";
      const img = await loadImage(src);
      return { product, img };
    }),
  );

  const gridTop = 470;
  const gap = 28;
  const footerY = HEIGHT - 280;
  const gridBottom = footerY - 48;
  const count = Math.max(loaded.length, 1);
  const columns = count === 1 ? 1 : 2;
  const rows = Math.ceil(count / columns);
  const cellW =
    columns === 1 ? WIDTH - 128 : (WIDTH - 128 - gap * (columns - 1)) / columns;
  const availableH = gridBottom - gridTop;
  const rowGap = gap + 70;
  const cellH = Math.min(
    columns === 1 ? 820 : 520,
    Math.floor((availableH - rowGap * (rows - 1) - 70) / rows),
  );

  loaded.forEach(({ product, img }, index) => {
    const col = index % columns;
    const row = Math.floor(index / columns);
    const x =
      columns === 1
        ? 64
        : 64 + col * (cellW + gap);
    const y = gridTop + row * (cellH + rowGap);

    ctx.fillStyle = "#FFFFFF";
    roundRect(ctx, x, y, cellW, cellH + 70, 28);
    ctx.fill();

    if (img) {
      ctx.save();
      roundRect(ctx, x, y, cellW, cellH - 8, 28);
      ctx.clip();
      drawCover(ctx, img, x, y, cellW, cellH - 8);
      ctx.restore();
    } else {
      ctx.fillStyle = "#E8F2EE";
      roundRect(ctx, x, y, cellW, cellH - 8, 28);
      ctx.fill();
    }

    ctx.fillStyle = "#0E1F1C";
    ctx.font = "700 34px Manrope, sans-serif";
    const nameLines = wrapText(ctx, product.name, cellW - 40, 1);
    ctx.fillText(nameLines[0] || product.name, x + 22, y + cellH + 28);

    ctx.fillStyle = accent;
    ctx.font = "800 32px Manrope, sans-serif";
    ctx.fillText(formatXafShort(product.price), x + 22, y + cellH + 62);
  });

  // Footer CTA band
  ctx.fillStyle = accent;
  roundRect(ctx, 64, footerY, WIDTH - 128, 180, 36);
  ctx.fill();

  ctx.fillStyle = "#FFFFFF";
  ctx.font = "800 44px Manrope, sans-serif";
  ctx.fillText("Commandez sur WhatsApp", 104, footerY + 78);

  ctx.font = "600 30px Manrope, sans-serif";
  const urlLines = wrapText(ctx, catalogUrl.replace(/^https?:\/\//, ""), WIDTH - 240, 2);
  urlLines.forEach((line, index) => {
    ctx.fillText(line, 104, footerY + 126 + index * 36);
  });

  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (!blob) reject(new Error("Image generation failed"));
        else resolve(blob);
      },
      "image/jpeg",
      0.92,
    );
  });
}

export function catalogShareMessage(store: Store, catalogUrl: string) {
  return (
    `Découvrez le catalogue ${store.name} sur Komero\n` +
    `${catalogUrl}\n` +
    `Commandez facilement sur WhatsApp.`
  );
}
