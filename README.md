# StyleAgent — AI Personal Stylist

> Complete personal styling intelligence. Built on Claude Vision. Covers every occasion, every visible element, every time.

StyleAgent analyses your outfit photos and returns specific, actionable feedback from a 30-year veteran stylist's perspective — covering garments, accessories, footwear, and grooming across 14 occasion types. It builds a permanent profile from your photos so every analysis is personalised to your undertone, body shape, face shape, and style archetype.

---

## What It Does

**One-time onboarding (5 photos):**
StyleAgent asks for 5 photos — face front, face side, full body front, full body side, and one real outfit you've worn. From these it extracts your skin undertone, body shape, face shape, hair and beard details, build, posture, and baseline style vocabulary. This profile is saved permanently and used in every future analysis.

**Per-analysis (1 outfit photo):**
Upload any outfit photo. StyleAgent returns:
- A numbered list of remarks ordered by priority — critical first
- Each remark includes: what's wrong, why it's wrong, and exactly what to fix
- A colour palette personalised to your undertone (DO / AVOID)
- A "Wear Instead" recommendation for the entire outfit
- Grooming notes specific to your face shape and current style
- A wardrobe gaps list ranked by impact
- A dark-mode editorial image with all remarks, your palette, and a score gauge

---

## Occasions Covered

| Indian | Western | Cross-category |
|---|---|---|
| Indian formal | Western business formal | Smart casual |
| Indian casual | Western business casual | Party / nightout |
| Ethnic fusion | Western streetwear | Wedding guest |
| | | Festival |
| | | Travel |
| | | Gym / athleisure |
| | | Beach |
| | | Lounge |

---

## Every Element Analysed

**Garments** — top, bottom, outerwear, layers, inner layers, full ethnic garments (sherwani, bandhgala, kurta, dhoti, lungi), jacket, blazer, suit
**Accessories** — watch, rings, bracelets, necklace, chain, pendant, belt, bag, sunglasses, hat, cap, turban, pagdi, pocket square, tie, tie pin, cufflinks, earrings
**Footwear** — type, colour, material, condition, occasion match, outfit match, care notes
**Grooming** — haircut style, beard style, beard grooming quality, stubble, mustache, eyebrows
**Colour harmony** — undertone compatibility, clash detection, pattern scale
**Proportion and silhouette** — across your specific height + body shape combination
**Occasion appropriateness** — formality level vs. expected formality

---

## Installation

### Requirements

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/) (for Claude Vision + recommendations)
- A [Replicate API token](https://replicate.com/account/api-tokens) *(optional — for caricature generation)*

### Setup

```bash
# Clone the repo
git clone https://github.com/sarthakmaggu5/style-agent.git
cd style-agent

# Install dependencies
pip install -r requirements.txt

# Set up your API keys
cp .env.example .env
# Open .env and fill in your ANTHROPIC_API_KEY
# Optionally add REPLICATE_API_TOKEN for caricature generation
```

### Validate setup

```bash
python scripts/validate_env.py
```

---

## Usage

### First Run — Build Your Profile

```bash
python src/main.py onboard
```

StyleAgent will ask for 5 photos. Follow the prompts — they're written casually, not clinically. You only do this once. Your profile is saved to `~/.style-agent/profile.json`.

To rebuild your profile later:

```bash
python src/main.py onboard --refresh-profile
```

---

### Analyse an Outfit

```bash
# Auto-detect the occasion
python src/main.py analyze --image ./photo.jpg

# Specify the occasion
python src/main.py analyze --image ./photo.jpg --occasion wedding_guest_indian
python src/main.py analyze --image ./photo.jpg --occasion office_western
python src/main.py analyze --image ./photo.jpg --occasion indian_casual
python src/main.py analyze --image ./photo.jpg --occasion streetwear
python src/main.py analyze --image ./photo.jpg --occasion party
python src/main.py analyze --image ./photo.jpg --occasion festival
python src/main.py analyze --image ./photo.jpg --occasion travel
python src/main.py analyze --image ./photo.jpg --occasion gym
```

#### Output options

```bash
# Hi-res output image (2× resolution)
python src/main.py analyze --image ./photo.jpg --hires

# Export a PDF alongside the JPEG
python src/main.py analyze --image ./photo.jpg --export-pdf

# Choose layout (editorial is the default dark-mode magazine layout)
python src/main.py analyze --image ./photo.jpg --layout editorial
python src/main.py analyze --image ./photo.jpg --layout sidebar
```

---

### View Your Profile

```bash
python src/main.py profile --show
```

---

### View Analysis History

```bash
python src/main.py history --last 5
```

---

## Output — What You Get

### Terminal (always)

```
══════════════════════════════════════════════════════════
  STYLE ANALYSIS  |  Wedding Guest — Indian
  Overall Score   : 5.5 / 10
══════════════════════════════════════════════════════════

YOUR PROFILE
  Undertone   : Deep Warm — olive base    [89% confidence]
  Body Shape  : Inverted Triangle         [82% confidence]
  Build       : Athletic, broad shoulders
  Face Shape  : Square
  Beard       : Medium full beard, well groomed

REMARKS  (fix in this order)

  [1] CRITICAL  |  COLOR
  Issue : Ivory has cool undertones — creates a grey cast against your warm complexion.
  Fix   : Swap to warm cream, off-white with yellow base, or warm champagne.
  Why   : Cool whites fight warm undertones — the face reads tired and drained.

  [2] CRITICAL  |  FABRIC + OCCASION
  Issue : Cotton kurta at a wedding reads two levels below what's expected.
  Fix   : Upgrade to chanderi, silk-cotton blend, or raw silk.

  ...

YOUR COLOR PALETTE
  ✓  Wear  : Rust · Terracotta · Warm Champagne · Deep Teal · Mustard
  ✗  Avoid : Icy white · Cool grey · Lavender · Cobalt

WARDROBE GAPS  (ranked by impact)
  1. Silk-blend kurta in rust or warm champagne
  2. Mojaris / juttis — own nothing for Indian formal
  3. Leather strap watch (tan or cognac)
══════════════════════════════════════════════════════════
```

### Image output (editorial layout)

A dark-mode magazine-quality image saved to `./outputs/`:

- **Left panel** — your caricature (generated by Replicate, or uses the original photo if Replicate is skipped)
- **Right panel** — stacked remark cards with coloured severity bars (red / amber / green), priority numbers `[1]–[N]`, issue context (grey), and fix action (white bold)
- **Header** — "STYLE ANALYSIS · YOUR NAME", occasion, score "4 / 10"
- **Footer** — your actual colour palette as swatches (DO and AVOID rows), "WEAR INSTEAD" outfit recommendation
- **Score gauge** — gold arc gauge bottom-left of caricature

---

## How the Analysis Works (Pipeline)

```
1. Load profile from ~/.style-agent/profile.json
2. Accept outfit photo + optional --occasion flag
3. Validate image (format, size, resolution) → resize → base64
4. Claude Vision → analyses outfit:
     - All garments (type, colour, pattern, fabric, fit, condition)
     - All accessories (type, colour, formality, occasion match)
     - Footwear (type, colour, condition, care notes)
     - Grooming (hair, beard visible in this photo)
5. Replicate API → generate caricature (skipped if no token)
6. Claude → cross-reference profile + outfit breakdown:
     - Apply colour theory for your undertone
     - Apply body type rules for your shape + height
     - Apply grooming guide for your face shape
     - Apply accessory and footwear rules for the occasion
     - Apply Indian / Western / fusion occasion rules
     - Generate remarks ordered by priority
7. Render editorial image → overlay all data
8. Save: annotated JPEG + full JSON to ./outputs/
```

---

## Project Structure

```
style-agent/
├── src/
│   ├── main.py                    ← CLI entry point (Click)
│   ├── agents/
│   │   ├── style_agent.py         ← Master orchestrator
│   │   ├── vision_agent.py        ← Claude Vision analysis
│   │   ├── profile_builder.py     ← Multi-photo profile construction
│   │   ├── caricature_agent.py    ← Replicate caricature generation
│   │   ├── grooming_agent.py      ← Hair, beard, skin sub-analysis
│   │   └── recommendation_agent.py ← Full recommendation generation
│   ├── models/                    ← Pydantic v2 strict data models
│   │   ├── user_profile.py
│   │   ├── outfit.py
│   │   ├── grooming.py
│   │   ├── accessories.py
│   │   ├── footwear.py
│   │   └── recommendation.py
│   ├── fashion_knowledge/         ← Static fashion rules (no API needed)
│   │   ├── indian_wear.py
│   │   ├── western_wear.py
│   │   ├── color_theory.py
│   │   ├── body_types.py
│   │   ├── fabric_guide.py
│   │   ├── grooming_guide.py
│   │   ├── accessory_guide.py
│   │   └── footwear_guide.py
│   ├── prompts/                   ← All Claude prompts
│   ├── services/                  ← API clients (Anthropic, Replicate, image)
│   ├── storage/                   ← Profile + history persistence
│   └── output/
│       ├── renderer.py            ← Editorial image generation (Pillow)
│       └── formatter.py           ← Terminal output formatting
├── tests/
│   ├── unit/                      ← 372 unit tests
│   └── integration/               ← Full pipeline tests (mocked)
├── scripts/
│   └── validate_env.py            ← API key checker
├── .env.example                   ← API key template
└── requirements.txt
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Vision analysis | Anthropic Claude claude-opus-4-5 (vision) |
| Style recommendations | Anthropic Claude claude-opus-4-5 |
| Caricature generation | Replicate (optional) |
| Image processing | Pillow (PIL) |
| Data models | Pydantic v2 (strict mode) |
| CLI | Click |
| API resilience | Tenacity (exponential backoff, 3 retries) |
| Type safety | Python type hints throughout |
| Test coverage | pytest, pytest-mock — 372 tests |

---

## Cost Per Analysis

| Step | API | Approx. Cost |
|---|---|---|
| Onboarding — 5 photos (one time) | Claude Vision ×5 | ~$0.03 |
| Outfit vision analysis | Claude Vision | ~$0.005 |
| Style recommendations | Claude (text) | ~$0.004 |
| Caricature generation | Replicate | ~$0.01–0.03 |
| **Per analysis session** | | **~₹2–4 / $0.02–0.04** |

Caricature generation is the most variable cost. Skipping it (no `REPLICATE_API_TOKEN`) gives you full text + editorial image analysis for ~₹1.

---

## Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional (caricature generation — skipped if not set)
REPLICATE_API_TOKEN=r8_...
```

Copy `.env.example` to `.env` and fill in your keys. The `.env` file is in `.gitignore` — your keys will never be committed.

---

## Running Tests

```bash
python3 -m pytest tests/ -q
# 372 passed
```

---

## Error Handling

Every external API call retries with exponential backoff (2s / 4s / 8s, max 3 retries). Timeouts are 30s for vision, 120s for caricature. If caricature generation fails, the full text + editorial image analysis still runs and is returned. Raw stack traces never appear in the terminal — only clean, user-facing messages.

---

## Data Privacy

- Photos are not stored beyond the analysis session unless `--save-photos` is explicitly passed
- Your profile is saved locally to `~/.style-agent/profile.json` only
- Nothing is sent to any server other than the Anthropic and Replicate APIs during analysis
- API keys are loaded from `.env` only — never hardcoded, never logged

---

*Built with the Anthropic Claude Agent SDK.*
