"""
Legacy Marathi font conversion utilities.

MSCE PDFs commonly embed Shree Dev 0708/0708E fonts. Those PDFs render
correctly, but text extraction returns font glyph codes instead of Unicode
Devanagari. This module converts those glyph codes to Unicode for import.
"""

from __future__ import annotations

import re


SHREE_DEV_0708_UNICODE_TO_LEGACY = {
    "अ": "A", "आ": "Am", "इ": "B", "ई": "B©", "उ": "C", "ऊ": "D$", "ऋ": "F$",
    "ए": "E", "ऐ": "Eo", "ऑ": "Am°", "ओ": "Amo", "औ": "Am¡",
    "ं": "§", "ः": "…", "ँ": "±",
    "क": "H$", "ख": "I", "ग": "J", "घ": "K", "च": "M", "छ": "N>", "ज": "O",
    "झ": "P", "ञ": "Äm", "ङ": "L>", "ट": "Q>", "ठ": "R>", "ड": "S>", "ढ": "T>", "ण": "U",
    "त": "V", "थ": "W", "द": "X", "ध": "Y", "न": "Z", "प": "n", "फ": "\\$",
    "ब": "~", "भ": "^", "म": "_", "य": "`", "र": "a", "ल": "b", "ळ": "i",
    "व": "d", "श": "e", "ष": "f", "स": "g", "ह": "h", "ऱ": "µa", "ऴ": "µi", "क्ष": "j", "ज्ञ": "k",
    "ा": "m", "ि": "{", "ी": "r", "ु": "w", "ू": "y", "ृ": "¥", "ॅ": "°",
    "े": "o", "ै": "¡", "ॉ": "m°", "ो": "mo", "ौ": "m¡", "्": "²",
    "०": "0", "१": "1", "२": "2", "३": "3", "४": "4", "५": "5", "६": "6",
    "७": "7", "८": "8", "९": "9",
    "क्": "Š", "ख्": "»", "ग्": "½", "घ्": "¿", "ङ्": "L²>", "च्": "À", "छ्": "N²>", "ज्": "Á", "झ्": "Â",
    "ञ्": "Ä", "ट्": "Q²>", "ठ्": "R²>", "ड्": "S²>", "ढ्": "T²>", "ण्": "Ê", "त्": "Ë", "थ्": "Ï",
    "द्": "X²", "ध्": "Ü", "न्": "Ý", "प्": "ß",
    "फ्": "â", "ब्": "ã", "भ्": "ä", "म्": "å", "य्": "æ", "र्": "©",
    "ऱ्": "è", "ल्": "ë", "ळ्": "ù", "व्": "ì", "श्": "í", "ष्": "î", "स्": "ñ", "ह्": "ô",
    "क्ष्": "ú", "ज्ञ्": "k²",
    "त्र": "Ì", "त्त": "Îm", "न्न": "Þ", "द्द": "Ô", "द्ध": "Õ", "द्व": "Û",
    "द्य": "Ú", "द्म": "Ù", "न्ह": "Ýh", "म्ह": "åh", "ल्ह": "ëh", "व्ह": "ìh",
    "क्व": "¹$", "त्व": "Ëd", "स्व": "ñd", "प्र": "à", "क्र": "H«$", "ग्र": "J«",
    "द्र": "Ì", "ब्र": "Ð", "श्र": "~«", "स्र": "l", "ह्र": "ò",
    "प्ल": "õ", "क्ल": "ßb", "ग्ल": "Šb", "फ्ल": "½b", "श्ल": "âb", "स्ल": "íb",
}

SHREE_DEV_POST_RA = "\ue000"

SHREE_DEV_0708E_LEGACY_OVERRIDES = {
    "H¥$": "कृ", "Ho$": "के", "Hw$": "कु", "Hy$": "कू", "Q´>": "ट्र", "Sy>": "डू",
    "’w$": "फु", "’o$": "फे", "’$": "फ", "ê$": "रू", "é": "रू", "lr": "श्री",
    "á": "प्त", "³": "क्", "´": "्र", "«": "्र", "s": "ी", "Wu": "र्थी",
    "u": "ी", "t": "ीं", "q": "िं", "[": "ि", "¶": "य", "‘": "म",
    "þ": "ु", "ÿ": "ू", "ç": "्य", "ø": "ह्य", "ª": f"{SHREE_DEV_POST_RA}ं",
    "|": "ें", "pñd": "स्वी", "pñ": "स्", "D$": "ऊ", "D": "ऊ", ">": "",
}

SHREE_DEV_ALLOWED_PASSTHROUGH = set(" \n\t.,;:!?()\"'/-+=%")
SHREE_DEV_ARTIFACT_RE = re.compile(
    r"(?:H\$|[<>\[\]{}~`^¡¥§©ª«°²³´¶½ÀÂÊËÌÎÐÜÝÞßàáãåçèéêëìíîñúþÿ])"
)


def _build_legacy_map() -> dict[str, str]:
    legacy_map: dict[str, str] = {}
    for unicode_text, legacy_text in SHREE_DEV_0708_UNICODE_TO_LEGACY.items():
        legacy_map.setdefault(legacy_text, unicode_text)
    legacy_map["Ì"] = "त्र"
    legacy_map["©"] = SHREE_DEV_POST_RA
    legacy_map.update(SHREE_DEV_0708E_LEGACY_OVERRIDES)
    return legacy_map


SHREE_DEV_0708E_LEGACY_TO_UNICODE = _build_legacy_map()
SHREE_DEV_0708E_TOKENS = sorted(SHREE_DEV_0708E_LEGACY_TO_UNICODE, key=len, reverse=True)


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    value = value.replace("\u00a0", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def reorder_shree_dev_unicode(text_value: str) -> str:
    consonant = r"[\u0915-\u0939\u0958-\u095f]"
    marks = r"[\u093e-\u094c\u0901-\u0903\u0970]*"
    text_value = re.sub(r"ि(" + consonant + r"(?:्" + consonant + r")*)", r"\1ि", text_value)
    text_value = re.sub(r"िं(" + consonant + r"(?:्" + consonant + r")*)", r"\1िं", text_value)
    text_value = re.sub("(" + consonant + r")(ु|ू|ृ)्र", r"\1्र\2", text_value)
    text_value = re.sub(
        "(" + consonant + r"(?:्" + consonant + r")?)(" + marks + ")" + SHREE_DEV_POST_RA + r"([ंँ]?)",
        r"र्\1\2\3",
        text_value,
    )
    return text_value.replace(SHREE_DEV_POST_RA, "र्")


def convert_shree_dev_0708e_to_unicode(value: str | None) -> str:
    if not value:
        return ""
    output: list[str] = []
    idx = 0
    while idx < len(value):
        for token in SHREE_DEV_0708E_TOKENS:
            if value.startswith(token, idx):
                output.append(SHREE_DEV_0708E_LEGACY_TO_UNICODE[token])
                idx += len(token)
                break
        else:
            char = value[idx]
            if char in SHREE_DEV_ALLOWED_PASSTHROUGH or char.isdigit():
                output.append(char)
            elif char in {"\u2009", "\x07", "\r"}:
                output.append(" ")
            else:
                output.append(char)
            idx += 1

    converted = reorder_shree_dev_unicode("".join(output))
    converted = converted.replace("''", '"').replace("``", '"').replace("'", '"')
    converted = re.sub(r"[ \t]+", " ", converted)
    converted = re.sub(r"\s+\n", "\n", converted)
    return normalize_text(converted)


def has_shree_dev_artifacts(value: str | None) -> bool:
    return bool(value and SHREE_DEV_ARTIFACT_RE.search(value))


def devanagari_digit_to_ascii(value: str) -> str:
    return value.translate(str.maketrans("०१२३४५६७८९", "0123456789"))
