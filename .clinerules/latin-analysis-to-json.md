# Latin Word Analysis Rules (JSON Specification)

These rules apply whenever analyzing a Latin word (verb, noun,
adjective, particle, numeral, etc.).\
All output **must be valid JSON** and follow the structure below.


# ------------------------------------------------------------------------
# AUTOMATIC WHITAKER LOOKUP
# ------------------------------------------------------------------------
# Whenever a Latin word is requested, **always** execute the MCP tool
#   analyze_latin  {"word": "<lemma>"}
# first.  Use the returned raw lines to populate the fields below:
#   - lemma          → take from Whitaker header line
#   - part_of_speech → map Whitaker part-of-speech abbreviations
#                       (V → verb, N → noun, ADJ → adjective, etc.)
#   - translations.en → first English gloss(es) shown by Whitaker
#   - translations.la → principal parts (verbs) or genitive (nouns)
#   - declension/gender/conjugation → parse Whitaker codes
#   - forms          → build the tag→list object from every form line
#
# If Whitaker returns multiple head-words, output **one JSON object per head-word**
# in a top-level array, each object still obeying the rules below.
# ------------------------------------------------------------------------


------------------------------------------------------------------------

## 1. General JSON Structure

Every analyzed entry must be a JSON object.

### Required top-level fields:

-   **lemma** --- canonical dictionary form
    -   For verbs: *1st person singular, present active indicative*
        (e.g., **amo**, **video**, **capio**, **sum**)\
    -   For nouns: **nominative singular**\
    -   For adjectives: **nominative singular masculine**\
    -   For particles / fixed forms: exact dictionary lemma
-   **part_of_speech** --- one of:
    -   *verb*, *noun*, *adjective*, *adverb*, *pronoun*, *preposition*,
        *conjunction*, *interjection*, *numeral*, *participle*,
        *particle*, etc.
-   **translations** (object):
    -   **en**: short English meaning(s), 1--3 words when possible
    -   **la**: full Latin principal parts or dictionary info

Example:

``` json
"translations": {
  "en": "stone, rock",
  "la": "lapis, lapidis"
}
```

------------------------------------------------------------------------

## 2. Nouns

### Required fields:

-   **declension** --- number 1--5; 0 for indeclinable nouns\
-   **gender** --- masculine, feminine, neuter\
-   **nominative** --- nominative singular\
-   Optional: **accusative**, **genitive**, **ablative**, etc.\
-   **forms** --- an object mapping grammatical tags → list of forms

### Forms notation:

-   Tags such as:
    -   `ablative_sg`
    -   `genitive_pl`
    -   `dative_sg`

Suffixes: - `_m` → masculine\
- `_f` → feminine\
- `_n` → neuter

Example:

``` json
"forms": {
  "ablative_sg": ["lapide"]
}
```

------------------------------------------------------------------------

## 3. Verbs

### Required fields:

-   **conjugation** --- 1, 2, 3, 3, 4, or 0 f   `"irregular"`
-   **infinitive**
-   **present**
-   **future**
-   **perfect**
-   **supine**
-   **forms** --- grammatical tag → list of forms

Verb lemma **must always** be 1st person singular present active
indicative.

Forms examples: - `present_participle` - `pluperfect_subjunctive` -
`present_indicative_1sg` - `present_participle_nom_sg_m`

Example:

``` json
"forms": {
  "present_participle": ["volante"],
  "pluperfect_subjunctive": ["voluisses"],
  "present_participle_nom_sg_m": ["volens"],
  "genitive_sg": ["volentis"]
}
```

------------------------------------------------------------------------

## 4. Numerals

### Required fields:

-   **part_of_speech**: "numeral"
-   **type**: cardinal / ordinal / distributive / adverbial
-   **declension**:
    -   0 for indeclinable
    -   number if declined

Example:

``` json
{
  "lemma": "decem",
  "part_of_speech": "numeral",
  "declension": 0,
  "type": "cardinal",
  "nominative": "decem",
  "translations": {
    "en": "ten",
    "la": "decem"
  }
}
```

------------------------------------------------------------------------

## 5. Optional Fields

Optional: - **type**\
- **stem**\
- **note**\
- **irregularities**

No commentary outside JSON.

------------------------------------------------------------------------

## 6. Output Format

Output must always be: - A single JSON object **or** a list of JSON
objects\
- Strict JSON syntax\
- No trailing commas\
- No prose outside JSON unless explicitly asked

------------------------------------------------------------------------

## 7. Example Output

``` json
[
  {
    "lemma": "lapis",
    "part_of_speech": "noun",
    "declension": 3,
    "gender": "masculine",
    "nominative": "lapis",
    "accusative": "lapidem",
    "translations": {
      "en": "stone, rock",
      "la": "lapis, lapidis"
    },
    "forms": {
      "ablative_sg": ["lapide"]
    }
  },
  {
    "lemma": "decem",
    "part_of_speech": "numeral",
    "declension": 0,
    "type": "cardinal",
    "nominative": "decem",
    "translations": {
      "en": "ten",
      "la": "decem"
    }
  },
  {
    "lemma": "volo",
    "part_of_speech": "verb",
    "conjugation": 1,
    "infinitive": "volare",
    "perfect": "volavi",
    "supine": "volatum",
    "forms": {
      "present_participle": ["volante"],
      "pluperfect_subjunctive": ["voluisses"],
      "present_participle_nom_sg_m": ["volens"],
      "present_participle_nom_sg_f": ["volens"],
      "present_participle_acc_sg_n": ["volens"],
      "genitive_sg": ["volentis"]
    },
    "translations": {
      "en": "to fly, will, wish",
      "la": "volo, volare, volavi, volatum"
    }
  },
  {
    "lemma": "negotium",
    "part_of_speech": "noun",
    "declension": 2,
    "gender": "neuter",
    "nominative": "negotium",
    "ablative": "negotio",
    "translations": {
      "en": "business, task; pestilence",
      "la": "negotium, -ii"
    }
  }
]
```