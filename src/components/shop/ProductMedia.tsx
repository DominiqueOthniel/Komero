"use client";

import Image from "next/image";
import { useState } from "react";

type Props = {
  src: string;
  alt: string;
  priority?: boolean;
  className?: string;
  sizes?: string;
};

function isRemoteApiMedia(src: string) {
  return (
    src.startsWith("http://") ||
    src.startsWith("https://") ||
    src.includes("/api/v1/public/media/")
  );
}

export function ProductMedia({
  src,
  alt,
  priority = false,
  className = "object-cover",
  sizes = "(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw",
}: Props) {
  const [failed, setFailed] = useState(false);
  const imageSrc = failed || !src ? "/images/product-wax.jpg" : src;
  const remote = isRemoteApiMedia(imageSrc);

  return (
    <Image
      src={imageSrc}
      alt={alt}
      fill
      sizes={sizes}
      className={className}
      priority={priority}
      unoptimized={remote}
      onError={() => setFailed(true)}
    />
  );
}
