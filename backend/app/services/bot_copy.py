"""French / English copy for the WhatsApp merchant bot."""

from __future__ import annotations

from typing import Any

Lang = str  # "fr" | "en"


def normalize_lang(value: str | None) -> Lang | None:
    if not value:
        return None
    lowered = value.strip().lower()
    if lowered in {"fr", "français", "francais", "french"}:
        return "fr"
    if lowered in {"en", "english", "anglais"}:
        return "en"
    return None


COPY: dict[str, dict[str, str]] = {
    "ask_language": {
        "fr": (
            "Bienvenue sur Komero.\n"
            "Choisissez votre langue / Choose your language :"
        ),
        "en": (
            "Welcome to Komero.\n"
            "Choose your language / Choisissez votre langue :"
        ),
    },
    "lang_saved": {
        "fr": "Langue : Francais. Vous pouvez la changer dans Plus > Langue.",
        "en": "Language: English. You can change it in More > Language.",
    },
    "ask_store_name": {
        "fr": "Quel est le nom de votre boutique ?",
        "en": "What is your shop name?",
    },
    "ask_store_name_again": {
        "fr": "Envoyez le nom de votre boutique pour terminer l'installation.",
        "en": "Send your shop name to finish setup.",
    },
    "onboarding_paused": {
        "fr": "Installation en pause. Envoyez le nom de la boutique quand vous etes pret.",
        "en": "Setup paused. Send your shop name when you are ready.",
    },
    "store_ready": {
        "fr": "Boutique prete : {name}.",
        "en": "Shop ready: {name}.",
    },
    "main_menu": {
        "fr": (
            "Komero · {name}\n"
            "\n"
            "Voici tout ce que vous pouvez faire :\n"
            "• Produits : ajouter, lister, supprimer\n"
            "• Ventes : enregistrer une vente, envoyer un recu PDF\n"
            "• Boutique : ouvrir votre catalogue public\n"
            "\n"
            "Exemples rapides :\n"
            "• Robe wax 15000 FCFA, 8 pieces\n"
            "• vente Robe 2 12000\n"
            "\n"
            "Astuce : envoyez menu a tout moment."
        ),
        "en": (
            "Komero · {name}\n"
            "\n"
            "Here is everything you can do:\n"
            "• Products: add, list, delete\n"
            "• Sales: record a sale, send a PDF receipt\n"
            "• Shop: open your public catalog\n"
            "\n"
            "Quick examples:\n"
            "• Wax dress 15000 FCFA, 8 pieces\n"
            "• sale Dress 2 12000\n"
            "\n"
            "Tip: send menu anytime."
        ),
    },
    "products_menu": {
        "fr": "Menu Produits. Que voulez-vous faire ?",
        "en": "Products menu. What do you want to do?",
    },
    "sales_menu": {
        "fr": "Menu Ventes. Que voulez-vous faire ?",
        "en": "Sales menu. What do you want to do?",
    },
    "more_menu": {
        "fr": "Plus d'options.",
        "en": "More options.",
    },
    "add_product_prompt": {
        "fr": (
            "Ajout de produit.\n"
            "Envoyez une photo avec legende, ou un texte.\n"
            "Exemples :\n"
            "• Robe rouge 12000 FCFA, 5 pieces\n"
            "• 2022 Ford 1,5M\n"
            "• iPhone 13 180k\n"
            "Envoyez menu pour revenir."
        ),
        "en": (
            "Add a product.\n"
            "Send a photo with caption, or text.\n"
            "Examples:\n"
            "• Red dress 12000 FCFA, 5 pieces\n"
            "• 2022 Ford 1.5M\n"
            "• iPhone 13 180k\n"
            "Send menu to go back."
        ),
    },
    "product_missing": {
        "fr": "Il me manque : {missing}. {hint}",
        "en": "I still need: {missing}. {hint}",
    },
    "product_hint_photo": {
        "fr": "Renvoyez une photo avec legende claire, ex: 2022 Ford 1,5M ou Robe wax 15000 FCFA.",
        "en": "Send a photo with a clear caption, e.g. 2022 Ford 1.5M or Wax dress 15000 FCFA.",
    },
    "product_hint_text": {
        "fr": "Exemple : Robe wax 15000 FCFA, 8 pieces. Ou : 2022 Ford 1,5M.",
        "en": "Example: Wax dress 15000 FCFA, 8 pieces. Or: 2022 Ford 1.5M.",
    },
    "product_draft_title": {
        "fr": "Brouillon produit :",
        "en": "Product draft:",
    },
    "product_photo_received": {
        "fr": "Photo recue. J'ai lu la legende.",
        "en": "Photo received. I read the caption.",
    },
    "product_draft_low_confidence": {
        "fr": "Je ne suis pas totalement sur. Verifiez avant de confirmer.",
        "en": "I am not fully sure. Check before confirming.",
    },
    "label_name": {"fr": "Nom", "en": "Name"},
    "label_price": {"fr": "Prix", "en": "Price"},
    "label_stock": {"fr": "Stock", "en": "Stock"},
    "label_sizes": {"fr": "Tailles", "en": "Sizes"},
    "label_missing": {"fr": "Manque", "en": "Missing"},
    "product_draft_footer": {
        "fr": "Confirmer pour publier, Modifier, ou Annuler.",
        "en": "Confirm to publish, Edit, or Cancel.",
    },
    "product_cancelled": {
        "fr": "Creation produit annulee.",
        "en": "Product creation cancelled.",
    },
    "product_edit_prompt": {
        "fr": "Envoyez les details corriges en texte, ou une nouvelle photo avec legende.",
        "en": "Send the corrected details as text, or a new photo with caption.",
    },
    "product_incomplete": {
        "fr": "Brouillon incomplet. Renvoyez le produit avec nom et prix.",
        "en": "Draft incomplete. Send the product again with name and price.",
    },
    "product_published": {
        "fr": "Produit publie : {name} ({price}).",
        "en": "Product published: {name} ({price}).",
    },
    "no_products": {
        "fr": "Aucun produit pour le moment.",
        "en": "No products yet.",
    },
    "products_list": {
        "fr": "Vos produits :\n{lines}",
        "en": "Your products:\n{lines}",
    },
    "delete_prompt": {
        "fr": (
            "Suppression produit.\n"
            "Repondez avec le numero :\n{lines}\n"
            "Ou envoyez menu pour annuler."
        ),
        "en": (
            "Delete a product.\n"
            "Reply with the number:\n{lines}\n"
            "Or send menu to cancel."
        ),
    },
    "delete_confirm": {
        "fr": "Supprimer definitivement « {name} » ({price}) ?",
        "en": "Permanently delete “{name}” ({price})?",
    },
    "delete_done": {
        "fr": "Produit supprime : {name}.",
        "en": "Product deleted: {name}.",
    },
    "delete_cancelled": {
        "fr": "Suppression annulee.",
        "en": "Deletion cancelled.",
    },
    "delete_not_found": {
        "fr": "Produit introuvable. Envoyez un numero de la liste.",
        "en": "Product not found. Send a number from the list.",
    },
    "sale_help": {
        "fr": (
            "Pour enregistrer une vente, envoyez :\n"
            "vente BBC 9000\n"
            "ou : vente Robe 2 12000\n"
            "Puis choisissez Recu PDF."
        ),
        "en": (
            "To record a sale, send:\n"
            "sale BBC 9000\n"
            "or: sale Dress 2 12000\n"
            "Then choose PDF receipt."
        ),
    },
    "sale_recorded": {
        "fr": "Vente enregistree : {code} · {total}.",
        "en": "Sale recorded: {code} · {total}.",
    },
    "ask_receipt_name": {
        "fr": (
            "Recu pour {code} : {items}, {total}.\n"
            "Au nom de qui ? Ecrivez le nom du client, ou tapez Sans nom."
        ),
        "en": (
            "Receipt for {code}: {items}, {total}.\n"
            "In whose name? Write the customer name, or tap No name."
        ),
    },
    "receipt_cancelled": {
        "fr": "Recu annule.",
        "en": "Receipt cancelled.",
    },
    "receipt_name_prompt": {
        "fr": "Ecrivez le nom du client, ou tapez Sans nom.",
        "en": "Write the customer name, or tap No name.",
    },
    "receipt_caption": {
        "fr": "Recu {number} · {total}. Verification : {verify}",
        "en": "Receipt {number} · {total}. Verify: {verify}",
    },
    "receipt_online": {
        "fr": "Recu {number} pret en ligne (PDF) : {verify}",
        "en": "Receipt {number} ready online (PDF): {verify}",
    },
    "receipt_share": {
        "fr": "Partagez ce lien avec votre client :\n{verify}",
        "en": "Share this link with your customer:\n{verify}",
    },
    "sale_not_found": {
        "fr": "Vente introuvable.",
        "en": "Sale not found.",
    },
    "no_last_sale": {
        "fr": "Aucune vente recente. Enregistrez d'abord une vente.",
        "en": "No recent sale. Record a sale first.",
    },
    "catalog_intro": {
        "fr": "Catalogue public de {name}.",
        "en": "Public catalog for {name}.",
    },
    "catalog_updated": {
        "fr": "Catalogue mis a jour. Fiche produit : {url}",
        "en": "Catalog updated. Product page: {url}",
    },
    "voice_pending": {
        "fr": (
            "Note vocale recue. Pour l'instant, repondez avec le produit en texte "
            "(nom + prix en FCFA), ou envoyez une photo avec legende."
        ),
        "en": (
            "Voice note received. For now, reply with the product as text "
            "(name + price in FCFA), or send a photo with a caption."
        ),
    },
    "image_failed": {
        "fr": "Je n'ai pas pu telecharger cette photo. Renvoyez-la, ou decrivez le produit en texte.",
        "en": "I could not download that photo. Please send it again, or describe the product in text.",
    },
    "help": {
        "fr": (
            "Aide Komero\n"
            "• menu : menu principal\n"
            "• Produits : ajouter / lister / supprimer\n"
            "• Ventes : vente Nom prix · recu PDF\n"
            "• Plus : catalogue, langue, aide\n"
            "• langue : changer FR / EN"
        ),
        "en": (
            "Komero help\n"
            "• menu: main menu\n"
            "• Products: add / list / delete\n"
            "• Sales: sale Name price · PDF receipt\n"
            "• More: catalog, language, help\n"
            "• language: switch FR / EN"
        ),
    },
    "fallback": {
        "fr": (
            "Je n'ai pas compris.\n"
            "Envoyez menu pour les options,\n"
            "ou : vente BBC 9000"
        ),
        "en": (
            "I did not understand.\n"
            "Send menu for options,\n"
            "or: sale BBC 9000"
        ),
    },
    "btn_fr": {"fr": "Francais", "en": "Francais"},
    "btn_en": {"fr": "English", "en": "English"},
    "btn_products": {"fr": "Produits", "en": "Products"},
    "btn_sales": {"fr": "Ventes", "en": "Sales"},
    "btn_more": {"fr": "Plus", "en": "More"},
    "btn_add": {"fr": "Ajouter", "en": "Add"},
    "btn_list": {"fr": "Liste", "en": "List"},
    "btn_delete": {"fr": "Supprimer", "en": "Delete"},
    "btn_new_sale": {"fr": "Nouvelle vente", "en": "New sale"},
    "btn_receipt": {"fr": "Recu PDF", "en": "PDF receipt"},
    "btn_back": {"fr": "Retour", "en": "Back"},
    "btn_catalog": {"fr": "Catalogue", "en": "Catalog"},
    "btn_language": {"fr": "Langue", "en": "Language"},
    "btn_help": {"fr": "Aide", "en": "Help"},
    "btn_confirm": {"fr": "Confirmer", "en": "Confirm"},
    "btn_edit": {"fr": "Modifier", "en": "Edit"},
    "btn_cancel": {"fr": "Annuler", "en": "Cancel"},
    "btn_yes_delete": {"fr": "Oui, supprimer", "en": "Yes, delete"},
    "btn_no": {"fr": "Non", "en": "No"},
    "btn_no_name": {"fr": "Sans nom", "en": "No name"},
    "btn_open_catalog": {"fr": "Ouvrir boutique", "en": "Open shop"},
    "btn_menu": {"fr": "Menu", "en": "Menu"},
}


def t(key: str, lang: Lang | None, **kwargs: Any) -> str:
    bundle = COPY.get(key) or {}
    code = lang if lang in ("fr", "en") else "fr"
    text = bundle.get(code) or bundle.get("fr") or key
    if kwargs:
        return text.format(**kwargs)
    return text


def buttons(lang: Lang | None, *keys: tuple[str, str]) -> list[dict[str, str]]:
    """Build WhatsApp reply buttons: each item is (id, copy_key)."""
    result: list[dict[str, str]] = []
    for button_id, copy_key in keys[:3]:
        result.append({"id": button_id, "title": t(copy_key, lang)[:20]})
    return result
