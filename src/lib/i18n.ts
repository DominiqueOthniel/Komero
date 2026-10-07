export type Locale = "en" | "fr";

export const locales: Locale[] = ["en", "fr"];

export type Dictionary = {
  meta: {
    title: string;
    description: string;
  };
  nav: {
    how: string;
    shop: string;
    faq: string;
    tryCta: string;
    langAria: string;
  };
  hero: {
    brand: string;
    headline: string;
    support: string;
    cta: string;
    secondary: string;
  };
  how: {
    title: string;
    support: string;
    steps: { title: string; body: string }[];
  };
  demo: {
    title: string;
    support: string;
    you: string;
    bot: string;
    lines: { who: "you" | "bot"; text: string }[];
  };
  shop: {
    title: string;
    support: string;
    storeName: string;
    replies: string;
    order: string;
    points: string[];
    products: { name: string; price: string; image: string; alt: string }[];
  };
  faq: {
    title: string;
    support: string;
    items: { q: string; a: string }[];
  };
  close: {
    title: string;
    support: string;
    cta: string;
    note: string;
  };
  footer: {
    rights: string;
    tagline: string;
  };
};

const en: Dictionary = {
  meta: {
    title: "Komero: Your shop lives on WhatsApp",
    description:
      "Add products by photo or voice note, share one link, and get clean orders on WhatsApp. Free trial, no card, no cut of your sales.",
  },
  nav: {
    how: "How it works",
    shop: "Your shop",
    faq: "FAQ",
    tryCta: "Open WhatsApp",
    langAria: "Language",
  },
  hero: {
    brand: "Komero",
    headline: "Sell from WhatsApp without the endless “how much?”",
    support:
      "Photo in, shop link out. Customers browse prices and sizes; you get orders ready to confirm.",
    cta: "Create my shop on WhatsApp",
    secondary: "14 days free · no card · no commission",
  },
  how: {
    title: "Four steps. Still on your phone.",
    support: "No app to install. No website to build. Komero runs the shop; you stay in WhatsApp.",
    steps: [
      {
        title: "Name your shop",
        body: "Message Komero, pick a name, choose the number customers will see. Your link is live.",
      },
      {
        title: "Add products your way",
        body: "Send photos, then write or voice-note name, price, stock, sizes or colours. Confirm once.",
      },
      {
        title: "Share one link",
        body: "Drop it in your bio, status, or ads. That link is the front door of your business.",
      },
      {
        title: "Confirm clean orders",
        body: "Cart, sizes, and total arrive structured in WhatsApp. Tap confirm; stock updates.",
      },
    ],
  },
  demo: {
    title: "It feels like chatting with a sharp assistant",
    support: "Same WhatsApp you already use. Komero drafts the catalogue; you approve.",
    you: "You",
    bot: "Komero",
    lines: [
      { who: "you", text: "Photo of a wax dress" },
      {
        who: "bot",
        text: "Got it. Send more photos if you have them, then describe: name, price, quantity, sizes or colours.",
      },
      { who: "you", text: "Wax dress 12000, 3 pieces, sizes 40 to 44" },
      {
        who: "bot",
        text: "Wax dress · 12,000 F · sizes 40 to 44 · 3 in stock. Publish?",
      },
      { who: "you", text: "Confirm" },
      { who: "bot", text: "Online. Share: chez-awa.komero.app/p/7K2WAX4R" },
    ],
  },
  shop: {
    title: "What your customers actually see",
    support:
      "Photos, prices, sizes, and stock, without asking you a hundred times a day.",
    storeName: "Chez Awa",
    replies: "Orders open on WhatsApp",
    order: "Order on WhatsApp",
    points: [
      "They choose size or colour, tap order, and WhatsApp opens with the cart already written.",
      "You get a coded order with the total. Confirm, correct, or mark not received in one tap.",
      "When stock hits zero, the shop shows sold out. No spreadsheet required.",
    ],
    products: [
      {
        name: "Wax dress",
        price: "12,000 F",
        image: "/images/product-wax.jpg",
        alt: "Colorful garments on a boutique rack",
      },
      {
        name: "Leather bag",
        price: "5,000 F",
        image: "/images/product-bag.jpg",
        alt: "Tan leather messenger bag with brass rings",
      },
    ],
  },
  faq: {
    title: "Straight answers",
    support: "The questions sellers ask before they try it.",
    items: [
      {
        q: "Do I need a computer or a website?",
        a: "No. Everything happens in WhatsApp, in writing or by voice note. Komero builds the shop and the link for you.",
      },
      {
        q: "Do sizes and colours work?",
        a: "Yes. Say them when you describe the product, for example “wax dress 12000, sizes 40 to 44”. Customers pick theirs when they order.",
      },
      {
        q: "How do customers pay?",
        a: "They pay you directly: Mobile Money, cash on delivery, whatever you agree on WhatsApp. Komero never touches their money.",
      },
      {
        q: "Is my number safe?",
        a: "Customers only see the number you choose at signup. Komero never messages your customers for you.",
      },
      {
        q: "What happens after the trial?",
        a: "Near the end, Komero sends a payment link for Orange Money or MTN Mobile Money. Without payment the shop pauses; your products stay ready to reopen.",
      },
      {
        q: "Can I use English or French?",
        a: "Both. Type /language whenever you want to switch.",
      },
    ],
  },
  close: {
    title: "Next time someone asks the price, send the link.",
    support: "Start on WhatsApp in under a minute. Keep selling the way you already do, with a shop that works while you sleep.",
    cta: "Start free on WhatsApp",
    note: "14-day trial · cancel anytime · you keep 100% of sales",
  },
  footer: {
    rights: "Komero. Built for sellers who live on WhatsApp.",
    tagline: "Catalogue, orders, stock, from your chat.",
  },
};

const fr: Dictionary = {
  meta: {
    title: "Komero: Votre boutique vit sur WhatsApp",
    description:
      "Ajoutez vos produits par photo ou message vocal, partagez un lien, recevez des commandes claires sur WhatsApp. Essai gratuit, sans carte, sans commission.",
  },
  nav: {
    how: "Comment ça marche",
    shop: "Votre boutique",
    faq: "FAQ",
    tryCta: "Ouvrir WhatsApp",
    langAria: "Langue",
  },
  hero: {
    brand: "Komero",
    headline: "Vendez sur WhatsApp sans le « c’est combien ? » sans fin",
    support:
      "Une photo, un lien boutique. Vos clients voient prix et tailles ; vous recevez des commandes prêtes à confirmer.",
    cta: "Créer ma boutique sur WhatsApp",
    secondary: "14 jours gratuits · sans carte · sans commission",
  },
  how: {
    title: "Quatre étapes. Toujours sur votre téléphone.",
    support:
      "Pas d’appli à installer. Pas de site à construire. Komero tient la boutique ; vous restez sur WhatsApp.",
    steps: [
      {
        title: "Nommez votre boutique",
        body: "Écrivez à Komero, choisissez un nom et le numéro que vos clients verront. Votre lien est en ligne.",
      },
      {
        title: "Ajoutez vos produits",
        body: "Envoyez des photos, puis décrivez à l’écrit ou en vocal : nom, prix, stock, tailles ou couleurs. Confirmez une fois.",
      },
      {
        title: "Partagez un seul lien",
        body: "Dans votre bio, votre statut ou vos pubs. Ce lien est la vitrine de votre activité.",
      },
      {
        title: "Confirmez des commandes claires",
        body: "Panier, tailles et total arrivent structurés sur WhatsApp. Un tap pour confirmer ; le stock suit.",
      },
    ],
  },
  demo: {
    title: "Comme discuter avec un assistant précis",
    support: "Le WhatsApp que vous utilisez déjà. Komero prépare le catalogue ; vous validez.",
    you: "Vous",
    bot: "Komero",
    lines: [
      { who: "you", text: "Photo d’une robe wax" },
      {
        who: "bot",
        text: "Reçu. Envoyez d’autres photos si besoin, puis décrivez : nom, prix, quantité, tailles ou couleurs.",
      },
      { who: "you", text: "Robe wax 12000, 3 pièces, tailles 40 à 44" },
      {
        who: "bot",
        text: "Robe wax · 12 000 F · tailles 40 à 44 · 3 en stock. Je publie ?",
      },
      { who: "you", text: "Confirmer" },
      { who: "bot", text: "En ligne. Lien : chez-awa.komero.app/p/7K2WAX4R" },
    ],
  },
  shop: {
    title: "Ce que vos clients voient vraiment",
    support:
      "Photos, prix, tailles et stock, sans vous écrire cent fois par jour.",
    storeName: "Chez Awa",
    replies: "Commandes sur WhatsApp",
    order: "Commander sur WhatsApp",
    points: [
      "Ils choisissent taille ou couleur, tapent commander, et WhatsApp s’ouvre avec le panier déjà rédigé.",
      "Vous recevez une commande avec code et total. Confirmer, corriger ou marquer non reçue en un tap.",
      "Quand le stock tombe à zéro, la boutique affiche épuisé. Pas de tableur.",
    ],
    products: [
      {
        name: "Robe wax",
        price: "12 000 F",
        image: "/images/product-wax.jpg",
        alt: "Vêtements colorés sur un portant de boutique",
      },
      {
        name: "Sac cuir",
        price: "5 000 F",
        image: "/images/product-bag.jpg",
        alt: "Sac messager en cuir beige avec anneaux laiton",
      },
    ],
  },
  faq: {
    title: "Réponses directes",
    support: "Ce que les vendeurs demandent avant d’essayer.",
    items: [
      {
        q: "Il me faut un ordinateur ou un site ?",
        a: "Non. Tout se passe sur WhatsApp, à l’écrit ou en vocal. Komero crée la boutique et le lien pour vous.",
      },
      {
        q: "Les tailles et couleurs marchent ?",
        a: "Oui. Dites-les en décrivant le produit, par exemple « robe wax 12000, tailles 40 à 44 ». Le client choisit au moment de commander.",
      },
      {
        q: "Comment les clients paient ?",
        a: "Ils vous paient directement : Mobile Money, à la livraison, comme vous vous entendez sur WhatsApp. Komero ne touche pas à leur argent.",
      },
      {
        q: "Mon numéro est-il protégé ?",
        a: "Les clients ne voient que le numéro que vous choisissez à l’inscription. Komero n’écrit jamais à vos clients à votre place.",
      },
      {
        q: "Et après l’essai ?",
        a: "Vers la fin, Komero envoie un lien de paiement Orange Money ou MTN Mobile Money. Sans paiement la boutique se met en pause ; vos produits restent prêts à rouvrir.",
      },
      {
        q: "Je peux parler français ou anglais ?",
        a: "Les deux. Tapez /language quand vous voulez changer.",
      },
    ],
  },
  close: {
    title: "La prochaine fois qu’on demande le prix, envoyez le lien.",
    support:
      "Démarrez sur WhatsApp en moins d’une minute. Continuez à vendre comme aujourd’hui, avec une boutique qui travaille pendant que vous dormez.",
    cta: "Commencer gratuitement sur WhatsApp",
    note: "Essai 14 jours · résiliez quand vous voulez · 100 % de vos ventes pour vous",
  },
  footer: {
    rights: "Komero. Pour les vendeurs qui vivent sur WhatsApp.",
    tagline: "Catalogue, commandes, stock, depuis votre chat.",
  },
};

export const dictionaries: Record<Locale, Dictionary> = { en, fr };

export function getDictionary(locale: Locale): Dictionary {
  return dictionaries[locale];
}
