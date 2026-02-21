# StyleAgent — AI Personal Stylist
> Complete personal styling intelligence. Production-grade. TDD. Every detail covered.

---

## 🎯 Product Vision

An AI personal stylist that builds a complete understanding of the user across multiple photos, then analyzes any outfit and returns specific, actionable feedback covering every visible element — garments, accessories, footwear, grooming — across every occasion type.

**Occasions covered without exception:**
Indian formal | Indian casual | Ethnic fusion | Western business formal | Western business casual | Western streetwear | Smart casual | Party/nightout | Wedding guest | Festival | Travel | Gym/athleisure | Beach | Lounge

**Every visible element analyzed:**
All garments (top, bottom, outerwear, layers, inner layers if visible, full ethnic garments) | All accessories (watch, rings, bracelets, necklace, chain, belt, bag, sunglasses, hat, cap, turban, pagdi, pocket square, tie, cufflinks) | Footwear (type, color, condition, occasion match, outfit match) | Grooming (haircut style, beard style, beard grooming, stubble, mustache, eyebrows) | Color harmony across entire look | Proportion and silhouette | Occasion appropriateness

---

## 📸 User Profile — Photo Onboarding

On first run (`python src/main.py onboard`), the agent requests 5 photos to build a permanent profile. The photo requests must feel casual and natural — never clinical.

### Photo Request Copy (use exactly this tone in CLI output)

```
Let's build your style profile. I need 5 photos — grab them from 
your camera roll or take them now. Here's what works best:

Photo 1 — A close-up of your face, looking straight at the camera.
           Natural light, indoors is fine.

Photo 2 — Your face from the side (either side).

Photo 3 — Full body, front-facing. Stand naturally, whatever you'd 
           normally wear heading out — jeans, kurta, anything real.

Photo 4 — Full body, side profile. Same everyday look.

Photo 5 — One of your recent outfits you actually went somewhere in.
           Office, dinner, casual day out — just a real one.

Once I have these I'll know enough about you to give useful feedback 
every single time.
```

### What Each Photo Extracts

**Photo 1 (face front):** Skin undertone, skin tone depth, face shape, jaw type, forehead, beard style and density, mustache, eyebrows, visible skin texture

**Photo 2 (face side):** Jaw structure depth, facial depth, beard density on jawline, neck proportions

**Photo 3 (body front):** Body shape, shoulder width, torso length, leg proportion, build, height estimate, baseline style and color preferences, fit preferences

**Photo 4 (body side):** Posture, belly profile, back proportions, build depth

**Photo 5 (real outfit):** Baseline style vocabulary, current formality defaults, color palette the user currently reaches for, accessory and footwear habits

### Profile Merge Logic
- Where photos give conflicting readings, use majority vote and note confidence score
- Minimum 3 photos to proceed; prompt for remaining
- Save to `~/.style-agent/profile.json`
- Returning users load profile automatically — re-onboard only with `--refresh-profile`

---

## 🏗️ Architecture

```
style-agent/
├── CLAUDE.md
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
│
├── src/
│   ├── __init__.py
│   ├── main.py                        ← CLI entry point (Click)
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── style_agent.py             ← Master orchestrator
│   │   ├── vision_agent.py            ← Claude Vision: full photo analysis
│   │   ├── profile_builder.py         ← Multi-photo profile construction + merge
│   │   ├── caricature_agent.py        ← Replicate: caricature generation
│   │   ├── grooming_agent.py          ← Hair, beard, skincare sub-analysis
│   │   └── recommendation_agent.py    ← Full recommendation generation
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user_profile.py
│   │   ├── outfit.py
│   │   ├── grooming.py
│   │   ├── accessories.py
│   │   ├── footwear.py
│   │   └── recommendation.py
│   │
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── profile_analysis.py        ← Vision prompts per photo type
│   │   ├── outfit_analysis.py
│   │   ├── grooming_analysis.py
│   │   ├── accessory_analysis.py
│   │   └── recommendations.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── anthropic_service.py
│   │   ├── replicate_service.py
│   │   └── image_service.py
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── profile_store.py
│   │   └── history_store.py
│   │
│   ├── fashion_knowledge/
│   │   ├── __init__.py
│   │   ├── indian_wear.py
│   │   ├── western_wear.py
│   │   ├── color_theory.py
│   │   ├── body_types.py
│   │   ├── fabric_guide.py
│   │   ├── grooming_guide.py
│   │   ├── accessory_guide.py
│   │   └── footwear_guide.py
│   │
│   └── output/
│       ├── __init__.py
│       ├── renderer.py                ← Overlay remarks on caricature
│       └── formatter.py               ← Terminal + file output
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_vision_agent.py
│   │   ├── test_profile_builder.py
│   │   ├── test_grooming_agent.py
│   │   ├── test_caricature_agent.py
│   │   ├── test_recommendation_agent.py
│   │   ├── test_color_theory.py
│   │   ├── test_body_types.py
│   │   ├── test_indian_wear.py
│   │   ├── test_western_wear.py
│   │   ├── test_grooming_guide.py
│   │   ├── test_accessory_guide.py
│   │   ├── test_footwear_guide.py
│   │   └── test_image_service.py
│   ├── integration/
│   │   ├── test_full_pipeline.py
│   │   └── test_api_services.py
│   └── fixtures/
│       ├── sample_photos/
│       └── mock_responses/
│
└── scripts/
    ├── validate_env.py
    └── run_local.sh
```

---

## 📊 Data Models (Pydantic v2, strict mode throughout)

### UserProfile
```python
class SkinUndertone(str, Enum):
    WARM = "warm"
    COOL = "cool"
    NEUTRAL = "neutral"
    DEEP_WARM = "deep_warm"        # warm undertone, deep skin — common South Asian
    DEEP_COOL = "deep_cool"
    OLIVE_WARM = "olive_warm"      # wheatish with warm base

class BodyShape(str, Enum):
    RECTANGLE = "rectangle"
    TRIANGLE = "triangle"
    INVERTED_TRIANGLE = "inverted_triangle"
    OVAL = "oval"
    TRAPEZOID = "trapezoid"

class FaceShape(str, Enum):
    OVAL = "oval"
    SQUARE = "square"
    ROUND = "round"
    OBLONG = "oblong"
    HEART = "heart"
    DIAMOND = "diamond"

class UserProfile(BaseModel):
    model_config = ConfigDict(strict=True)

    skin_undertone: SkinUndertone
    skin_tone_depth: str           # light / medium / wheatish / tan / deep
    skin_texture_visible: str      # smooth / textured / oily / dry / combination

    body_shape: BodyShape
    height_estimate: str           # tall / average / petite
    build: str                     # slim / lean / athletic / average / broad / stocky
    shoulder_width: str            # narrow / average / broad
    torso_length: str              # short / average / long
    leg_proportion: str            # short / average / long

    face_shape: FaceShape
    jaw_type: str                  # strong / soft / angular / rounded
    forehead: str                  # broad / average / narrow

    hair_color: str
    hair_texture: str              # straight / wavy / curly / coily
    hair_density: str              # thin / medium / thick
    current_haircut_style: str
    haircut_length: str            # short / medium / long
    hair_visible_condition: str    # healthy / frizzy / oily / dry

    beard_style: str               # clean shaven / stubble / short / full / patchy
    beard_density: str             # none / patchy / medium / dense
    beard_color: str
    mustache_style: str            # none / natural / pencil / handlebar
    beard_grooming_quality: str    # well groomed / average / unkempt / not applicable

    confidence_scores: dict[str, float]
    photos_used: int
    profile_created_at: str
    profile_version: int
```

### GroomingProfile
```python
class GroomingProfile(BaseModel):
    model_config = ConfigDict(strict=True)

    current_haircut_assessment: str
    recommended_haircut: str
    haircut_to_avoid: str
    styling_product_recommendation: list[str]
    hair_color_recommendation: str

    current_beard_assessment: str
    recommended_beard_style: str
    beard_grooming_tips: list[str]
    beard_style_to_avoid: str

    eyebrow_assessment: str
    eyebrow_recommendation: str

    visible_skin_concerns: list[str]
    skincare_categories_needed: list[str]

    grooming_score: int            # 1–10
    grooming_remarks: list[Remark]
```

### AccessoryItem + AccessoryAnalysis
```python
class AccessoryType(str, Enum):
    WATCH = "watch"
    RING = "ring"
    BRACELET = "bracelet"
    NECKLACE = "necklace"
    CHAIN = "chain"
    PENDANT = "pendant"
    BELT = "belt"
    BAG = "bag"
    SUNGLASSES = "sunglasses"
    HAT = "hat"
    CAP = "cap"
    TURBAN = "turban"
    PAGDI = "pagdi"
    POCKET_SQUARE = "pocket_square"
    TIE = "tie"
    TIE_PIN = "tie_pin"
    CUFFLINKS = "cufflinks"
    EARRING = "earring"

class AccessoryItem(BaseModel):
    model_config = ConfigDict(strict=True)
    type: AccessoryType
    color: str
    material_estimate: str
    style_category: str            # casual / formal / traditional / statement / sport
    condition: str
    occasion_appropriate: bool
    issue: str
    fix: str

class AccessoryAnalysis(BaseModel):
    items_detected: list[AccessoryItem]
    missing_accessories: list[str]
    accessories_to_remove: list[str]
    accessory_harmony: str
    overall_score: int             # 1–10
```

### FootwearAnalysis
```python
class FootwearAnalysis(BaseModel):
    model_config = ConfigDict(strict=True)
    visible: bool
    type: str                      # sneakers / oxford / loafers / boots / sandals /
                                   # chappals / mojaris / juttis / kolhapuris / etc.
    color: str
    material_estimate: str
    condition: str                 # clean / scuffed / dirty / worn out / sole peeling
    style_category: str
    occasion_match: bool
    outfit_match: bool
    issue: str
    recommended_instead: str
    shoe_care_note: str
```

### GarmentItem + OutfitBreakdown
```python
class GarmentItem(BaseModel):
    model_config = ConfigDict(strict=True)
    category: str                  # top / bottom / outerwear / layer / inner /
                                   # ethnic-top / ethnic-bottom / full-garment
    garment_type: str
    color: str
    pattern: str                   # solid / stripes / checks / floral / geometric /
                                   # embroidered / printed / textured
    fabric_estimate: str
    fit: str
    length: str
    collar_type: str               # "n/a" if not applicable
    sleeve_type: str               # "n/a" if not applicable
    condition: str
    occasion_appropriate: bool
    issue: str
    fix: str

class OutfitBreakdown(BaseModel):
    model_config = ConfigDict(strict=True)
    occasion_detected: str
    occasion_requested: str
    occasion_match: bool
    items: list[GarmentItem]
    accessory_analysis: AccessoryAnalysis
    footwear_analysis: FootwearAnalysis
    overall_color_harmony: str
    color_clash_detected: bool
    silhouette_assessment: str
    proportion_assessment: str
    formality_level: int           # 1–10
    outfit_score: int              # 1–10
```

### StyleRemark + StyleRecommendation
```python
class RemarkCategory(str, Enum):
    COLOR = "color"
    FIT = "fit"
    FABRIC = "fabric"
    OCCASION = "occasion"
    PROPORTION = "proportion"
    ACCESSORY = "accessory"
    FOOTWEAR = "footwear"
    GROOMING_HAIR = "grooming_hair"
    GROOMING_BEARD = "grooming_beard"
    GROOMING_SKIN = "grooming_skin"
    LAYERING = "layering"
    PATTERN = "pattern"
    LENGTH = "length"
    CONDITION = "condition"
    POSTURE = "posture"

class Remark(BaseModel):
    model_config = ConfigDict(strict=True)
    severity: str                  # critical / moderate / minor
    category: RemarkCategory
    body_zone: str                 # head / face / neck / upper-body / lower-body / feet / full-look
    element: str
    issue: str
    fix: str
    why: str
    priority_order: int

class StyleRecommendation(BaseModel):
    model_config = ConfigDict(strict=True)
    user_profile: UserProfile
    grooming_profile: GroomingProfile
    outfit_breakdown: OutfitBreakdown

    outfit_remarks: list[Remark]
    grooming_remarks: list[Remark]
    accessory_remarks: list[Remark]
    footwear_remarks: list[Remark]

    color_palette_do: list[str]
    color_palette_dont: list[str]
    color_palette_occasion_specific: list[str]

    recommended_outfit_instead: str
    recommended_grooming_change: str
    recommended_accessories: str

    wardrobe_gaps: list[str]
    shopping_priorities: list[str]

    overall_style_score: int       # 1–10
    outfit_score: int
    grooming_score: int
    accessory_score: int
    footwear_score: int

    caricature_image_path: str
    annotated_output_path: str
    analysis_json_path: str
```

---

## 🧠 Fashion Knowledge Base — Full Spec

### `grooming_guide.py`

**Hair by face shape:**
```
Oval    : Most cuts work. Avoid excessive height that further elongates.
Square  : Textured crops, side parts, tapered sides. Avoid boxy/bowl cuts.
Round   : Height on top, tight sides. Avoid bowl cuts, unstyled curtains.
Oblong  : Side sweeps, volume on sides. Avoid height — elongates further.
Heart   : Medium length, soft fringe. Avoid heavy top-heavy volume.
Diamond : Maintain width at forehead/jaw. Avoid narrow side profiles.
```

**Beard by face shape:**
```
Oval    : Any style. Classic full beard recommended.
Square  : Longer on chin to soften jaw. Cheeks and sides trimmed shorter.
Round   : Extended chin to elongate. Sides tight.
Oblong  : Avoid long chin. Keep full and wide for added width.
Heart   : Fuller chin to balance narrower jaw. Light cheek coverage.
Diamond : Full at jaw. Cheeks clean — avoids width at cheekbones.
```

### `color_theory.py`

```
WARM UNDERTONE (yellow/golden base):
  Do   : rust, terracotta, camel, warm beige, mustard, peach, coral,
         warm red, burnt orange, olive green, warm brown, cream, gold
  Avoid: cool grey, icy white, lavender, cobalt blue, cool pink, silver

COOL UNDERTONE (pink/blue base):
  Do   : navy, burgundy, cool grey, emerald, cobalt, cool white, rose,
         mauve, icy blue, charcoal, silver, cool teal
  Avoid: warm yellows, orange, rust, warm beige, gold

NEUTRAL UNDERTONE:
  Do   : both palettes in muted, desaturated versions
  Avoid: extremely saturated versions of either extreme

DEEP WARM (warm undertone, deep skin — common South Asian):
  Do   : jewel tones (sapphire, emerald, deep burgundy, royal purple),
         warm earth tones, gold, rust, deep teal
  Avoid: pastels (wash out), neon, very light neutrals

OLIVE WARM (wheatish, warm base):
  Do   : warm earth tones, muted greens, warm tans, terracotta, deep blues
  Avoid: nude/beige too close to skin tone, cool pastels, stark white
```

### `body_types.py`

```
RECTANGLE: structured shoulders, belted silhouettes, contrast top/bottom
  Avoid: boxy all-over with no definition

INVERTED TRIANGLE: longer hemlines, V-necks, vertical top lines, A-line bottoms
  Avoid: shoulder padding, chest horizontal stripes, puffed sleeves

TRIANGLE: structured shoulders, top details, darker bottoms
  Avoid: tight bottom + tight top, hip-level horizontal patterns

OVAL: vertical lines, open necklines, straight cuts, longer lengths
  Avoid: horizontal waist bands, cropped tops, un-tucked shirts without structure

TRAPEZOID: most silhouettes work, maintain proportional balance
  Avoid: excessive bulk everywhere
```

### `accessory_guide.py`

```
WATCH:
  Formal   → leather strap (tan/black/dark brown), dress watch, metal case
  Casual   → NATO / rubber strap fine, sport watch fine
  Never    → plastic Casio or rubber sport strap with formal or ethnic formal
  Size     → case diameter must not exceed wrist width

RINGS:
  Max 2 hands total visible; stack on same or adjacent fingers
  Signet ring → formal or smart casual only
  Statement ring → casual or streetwear only

BELT:
  Match to shoe color family (not exact match required)
  Thin belt with slim trousers; standard width with regular fit
  Never wear a belt with sherwani, formal kurta, or bandhgala

BAG:
  Backpack → casual and travel only, never with formal or ethnic formal
  Laptop bag / structured tote → business casual ok
  Clutch → smart casual and party
  Jhola / cloth bag → casual ethnic only

SUNGLASSES:
  Round face → angular frames (wayfarer, square)
  Square face → round or oval frames
  Oval face → most frames work
  Remove for formal indoor settings

TURBAN / PAGDI:
  Assess color match with outfit
  Fabric weight must match occasion fabric weight
  Style (casual dastar vs formal pagdi) must match occasion
```

### `footwear_guide.py`

```
INDIAN FORMAL (sherwani / bandhgala):
  → Mojaris (plain or embellished), juttis, kolhapuris (formal), leather oxfords (plain, neutral)
  → Never: sneakers, sports sandals, rubber chappals

INDIAN CASUAL (everyday kurta):
  → Kolhapuris, loafers, clean white sneakers, leather sandals
  → Never: formal black oxfords, sports shoes

WESTERN FORMAL:
  → Oxford, Derby, Monk strap — black or dark brown, polished
  → Never: loafers, sneakers, suede

WESTERN BUSINESS CASUAL:
  → Loafers, clean leather sneakers, Chelsea boots
  → Never: sports shoes, rubber sandals

STREETWEAR:
  → Sneakers (matching palette), chunky trainers, clean low-tops
  → Condition is critical — dirty sneakers ruin the entire look

WEDDING GUEST (Indian):
  → Same as Indian formal

CONDITION RULES:
  Scuffed leather   → moderate, recommend polish or cobbler
  Dirty sneakers    → critical, must clean before wearing again
  Sole peeling      → critical, replace immediately
  Yellowed sole     → moderate, clean or replace
```

### `indian_wear.py`

```
KURTA LENGTH:
  Tall + any shape       → mid-thigh or below
  Average + rectangle    → hip to mid-thigh
  Petite + any shape     → at or just above hip (never lower — shortens further)
  Inverted triangle      → always mid-thigh+ to balance top width

COLLAR BY FACE SHAPE:
  Bandhgala → square, oval, oblong
  Nehru     → oval, heart, diamond
  Mandarin  → versatile, most face shapes
  Angrakha  → oval and heart

FABRIC BY OCCASION:
  Wedding / formal  → chanderi, silk-cotton blend, raw silk, brocade
  Office / smart    → cotton-silk blend, linen-cotton, structured cotton
  Casual            → plain cotton, block print, linen
  Festival          → any — color and print more important than fabric

VALID ETHNIC FUSION:
  Kurta + tailored trousers
  Kurta + dark slim jeans
  Bandhgala jacket + western trousers
  Nehru jacket over shirt

INVALID ETHNIC FUSION:
  Sherwani + jeans → never
  Ethnic top + track/gym bottoms → never
  Formal kurta + cargo shorts → never
  Mojaris with western formal suit → avoid

SOUTH ASIAN SKIN PALETTES:
  Warm olive / wheatish  : mustard, rust, deep teal, warm navy, ivory, earthy browns
  Deep warm              : jewel tones, gold, warm burgundy, deep orange, forest green
  Medium warm            : wide range — avoid nude too close to skin tone
```

### `western_wear.py`

```
TROUSER BREAK:
  Tall   → no break or slight break
  Average → half break is safe default
  Petite  → no break always, consider ankle length

COLLAR BY FACE SHAPE:
  Spread collar  → square or angular face
  Button-down    → oval, heart, oblong
  Band collar    → oval and oblong
  Never: spread collar on round face

LAYERING:
  Heavier fabric always outer
  Fit tapers inward — base layer slimmest, outer most relaxed
  Outer can break in color but must relate tonally or complementarily

TROUSER + SHOE PAIRING:
  Slim / tapered   → loafers, derbies, clean sneakers
  Wide / relaxed   → chunky sneakers, chelsea boots, brogues
  Formal tailored  → oxford or derby only

BELT + SHOE:
  Black belt = black shoes
  Brown belt = tan / cognac / brown (any shade)
  No belt needed: chinos + untucked shirt, denim, tailored suits with suspenders
```

---

## 🔄 Full Analysis Pipeline

```
[ONBOARDING — first run only]
5 photos uploaded sequentially
  → Photo-specific vision prompt per type
  → Extract attributes from each photo
  → Merge into single UserProfile (majority vote on conflicts)
  → Save to ~/.style-agent/profile.json
  → Print profile summary to user

[ANALYSIS — every subsequent run]
1. Load UserProfile from ~/.style-agent/profile.json
2. Accept outfit photo + optional --occasion flag
3. image_service: validate format, size, resolution → resize → base64
4. vision_agent → Claude Vision:
     OutfitBreakdown (all garments)
     AccessoryAnalysis (all accessories)
     FootwearAnalysis
     GroomingProfile (hair + beard visible in this photo)
5. caricature_agent → Replicate API:
     Generate caricature
     Download + save locally
6. recommendation_agent → Claude API:
     Cross-reference UserProfile + OutfitBreakdown
     Apply color_theory for undertone
     Apply body_type rules for silhouette
     Apply grooming_guide rules
     Apply accessory_guide + footwear_guide
     Apply occasion knowledge (indian / western / fusion)
     Generate Remarks ordered by priority_order
     Generate full StyleRecommendation
7. renderer: load caricature, overlay remarks by body_zone, save annotated PNG
8. formatter: print terminal report, save JSON to ./outputs/
```

---

## 🧪 Complete Test Suite

### `test_models.py`
```
test_user_profile_rejects_invalid_undertone
test_face_shape_enum_all_values
test_body_shape_enum_all_values
test_accessory_type_enum_complete
test_garment_item_requires_issue_and_fix
test_remark_severity_valid_values
test_remark_priority_order_positive_int
test_footwear_visible_false_returns_empty
test_style_recommendation_json_roundtrip
test_strict_mode_rejects_extra_fields
```

### `test_color_theory.py`
```
test_warm_palette_contains_rust_terracotta
test_warm_avoids_cobalt
test_cool_palette_contains_navy_emerald
test_cool_avoids_warm_yellows
test_deep_warm_includes_jewel_tones
test_deep_warm_excludes_pastels
test_olive_warm_palette_correct
test_clash_detected_correctly
test_monochromatic_not_flagged_as_clash
test_pattern_scale_small_frame_small_print
```

### `test_body_types.py`
```
test_rectangle_belted_silhouette_in_do
test_inverted_triangle_no_shoulder_padding
test_inverted_triangle_longer_hemline_recommended
test_triangle_darker_bottom_in_do
test_oval_vertical_lines_in_do
test_trapezoid_balanced_proportion
test_every_type_has_do_and_dont
test_kurta_length_tall_inverted_triangle
test_kurta_length_petite_hip_only
```

### `test_grooming_guide.py`
```
test_oval_face_most_haircuts_valid
test_square_face_avoids_boxy
test_round_face_adds_height
test_oblong_face_adds_width_not_height
test_beard_round_elongates_chin
test_beard_heart_fuller_chin
test_beard_square_longer_chin_shorter_sides
test_beard_diamond_full_jaw_clean_cheeks
test_grooming_score_1_to_10
test_eyebrow_recommendation_not_empty
```

### `test_accessory_guide.py`
```
test_formal_requires_leather_strap
test_casual_allows_nato
test_plastic_watch_flagged_with_formal
test_belt_black_matches_black_shoe
test_no_belt_with_sherwani
test_backpack_flagged_with_formal
test_ring_max_two_hands
test_sunglasses_round_face_angular_frames
test_turban_color_assessed
test_missing_accessories_suggested
```

### `test_footwear_guide.py`
```
test_sherwani_requires_mojari
test_sneakers_critical_with_sherwani
test_western_formal_requires_oxford_derby_monk
test_sneakers_flagged_western_formal
test_streetwear_allows_clean_sneakers
test_dirty_sneakers_critical
test_scuffed_leather_moderate
test_sole_peeling_critical
test_yellowed_sole_moderate
test_shoe_care_note_populated_when_bad
```

### `test_indian_wear.py`
```
test_kurta_length_tall_mid_thigh
test_kurta_length_petite_hip
test_bandhgala_square_face
test_nehru_oval_face
test_wedding_silk_or_chanderi
test_casual_cotton
test_fusion_kurta_jeans_valid
test_fusion_sherwani_jeans_invalid
test_fusion_ethnic_top_track_pants_invalid
test_warm_olive_palette
test_deep_warm_jewel_tones
test_festival_fabric_any
```

### `test_western_wear.py`
```
test_tall_no_break
test_petite_no_break_always
test_spread_collar_not_round_face
test_button_down_oval_ok
test_layering_heavier_outer
test_slim_trouser_loafer_derby
test_black_belt_black_shoe
test_brown_belt_cognac_ok
test_no_belt_denim_ok
```

### `test_vision_agent.py`
```
test_returns_valid_outfit_breakdown
test_detects_minimum_one_garment
test_detects_accessories_when_visible
test_empty_accessory_list_when_none
test_footwear_visible_true_when_in_frame
test_footwear_visible_false_when_not
test_detects_grooming
test_low_quality_image_handled
test_indian_garment_detected
test_western_garment_detected
test_fusion_detected
test_occasion_mismatch_flagged
test_confidence_scores_0_to_1
```

### `test_profile_builder.py`
```
test_builds_profile_from_5_photos
test_accepts_3_photos_minimum
test_rejects_fewer_than_3
test_conflicting_undertone_majority_vote
test_profile_saved_to_json
test_profile_loaded_matches_original
test_version_increments_on_refresh
test_refresh_overwrites_existing
```

### `test_caricature_agent.py`
```
test_replicate_called_correct_model
test_returns_local_image_path
test_image_downloaded
test_timeout_handled_gracefully
test_api_error_handled
test_fallback_original_photo_if_fails
```

### `test_recommendation_agent.py`
```
test_remarks_ordered_by_priority
test_critical_remark_color_clash
test_critical_remark_dirty_shoes
test_critical_remark_sole_peeling
test_grooming_remarks_in_output
test_accessory_remarks_in_output
test_footwear_remarks_in_output
test_indian_occasion_indian_garments
test_western_occasion_western_garments
test_warm_undertone_avoids_cool_in_recommendation
test_inverted_triangle_no_shoulder_emphasis
test_shopping_priorities_ranked
test_wardrobe_gaps_not_empty
test_all_scores_1_to_10
```

### `test_image_service.py`
```
test_rejects_over_15mb
test_accepts_jpg_png_webp_heic
test_rejects_gif_pdf
test_resize_preserves_ratio
test_base64_decodable
test_corrupted_image_value_error
test_minimum_400px_enforced
```

### Integration Tests (`test_full_pipeline.py`)
```
test_warm_indian_casual_mocked
test_cool_western_business_mocked
test_deep_warm_wedding_guest_mocked
test_onboarding_5_photos_mocked
test_returning_user_loads_profile_mocked
test_caricature_fail_still_returns_text
test_vision_fail_clear_error
test_annotated_output_created
test_json_saved_to_outputs
test_history_log_updated
```

---

## 🖨️ Terminal Output Format

```
══════════════════════════════════════════════════════════
  STYLE ANALYSIS  |  Wedding Guest — Indian
  Overall Score   : 5.5 / 10
══════════════════════════════════════════════════════════

YOUR PROFILE
  Undertone   : Deep Warm — olive base    [89% confidence]
  Body Shape  : Inverted Triangle         [82% confidence]
  Build       : Athletic, broad shoulders
  Height      : Tall
  Face Shape  : Square
  Hair        : Short taper fade, straight, medium density
  Beard       : Medium full beard, well groomed

──────────────────────────────────────────────────────────
OUTFIT BREAKDOWN
──────────────────────────────────────────────────────────
  Kurta       : Ivory cotton, straight cut, hip length
  Bottom      : Dark navy churidar
  Watch       : Silver case, black rubber strap          [visible]
  Footwear    : Brown leather oxfords, scuffed           [visible]
  Belt        : None  ✓ correct for kurta

  Color Harmony  : Clashing — ivory cool-toned vs warm undertone
  Silhouette     : Top-heavy — kurta ends at widest point
  Formality      : 6 / 10
  Occasion match : ✗

──────────────────────────────────────────────────────────
REMARKS  (fix in this order)
──────────────────────────────────────────────────────────

  [1] CRITICAL  |  COLOR
  Issue : Ivory has cool undertones. Creates a grey cast against your warm complexion.
  Fix   : Swap to warm cream, off-white with yellow base, or warm champagne.
  Why   : Cool whites fight warm undertones — the face reads tired and drained.

  [2] CRITICAL  |  FABRIC + OCCASION
  Issue : Cotton kurta at a wedding reads two levels below what's expected.
  Fix   : Upgrade to chanderi, silk-cotton blend, or raw silk.
  Why   : Fabric weight signals formality in Indian wear as much as silhouette.

  [3] CRITICAL  |  LENGTH + PROPORTION
  Issue : Hip-length kurta ends at your broadest point. Shoulder dominance maximised.
  Fix   : Mid-thigh or longer. Elongates the silhouette, balances inverted triangle.
  Why   : Longer hem draws the eye down, reducing perceived shoulder width.

  [4] MODERATE  |  FOOTWEAR
  Issue : Leather oxfords with a kurta — Western formal language on Indian traditional.
  Fix   : Swap to mojaris or embellished juttis.
  Why   : Footwear must speak the same style language as the garment.

  [5] MODERATE  |  FOOTWEAR CONDITION
  Issue : Oxfords are visibly scuffed.
  Fix   : Polish before next wear, or take to a cobbler this week.
  Why   : Shoe condition is noticed immediately — it anchors or undermines everything.

  [6] MODERATE  |  ACCESSORY
  Issue : Rubber strap is sport-casual. Wrong signal for wedding formality.
  Fix   : Tan leather strap or simple metal bracelet.
  Why   : Strap material carries the formality signal of the entire wrist.

  [7] MINOR  |  GROOMING — BEARD
  Issue : Full beard on sides adds width to an already square jaw.
  Fix   : Trim cheek line higher, let chin grow slightly longer.
  Why   : Length at chin softens square jaw; width on sides reinforces it.

──────────────────────────────────────────────────────────
YOUR COLOR PALETTE
──────────────────────────────────────────────────────────
  ✓  Wear  : Rust · Terracotta · Warm Champagne · Deep Teal · Burnt Orange
             Mustard · Warm Cream · Forest Green · Rich Burgundy · Emerald
  ✗  Avoid : Icy white · Cool grey · Lavender · Cobalt · Pale pink

──────────────────────────────────────────────────────────
WEAR THIS INSTEAD
──────────────────────────────────────────────────────────
  Kurta    : Rust or warm champagne silk-cotton, straight cut, mid-thigh
  Bottom   : Ivory churidar — warm top, neutral base now reads balanced
  Shoes    : Embroidered mojaris, tan or gold
  Watch    : Tan leather strap or simple gold-tone bracelet

──────────────────────────────────────────────────────────
GROOMING
──────────────────────────────────────────────────────────
  Hair    : Taper fade works for your face shape. Keep it.
  Beard   : Trim cheek line 0.5–1cm higher. Let chin grow 1–2 weeks.
            Elongates jaw, reduces perceived facial width.

──────────────────────────────────────────────────────────
WARDROBE GAPS  (ranked by impact)
──────────────────────────────────────────────────────────
  1. Silk-blend kurta in rust or warm champagne — highest impact, multiple occasions
  2. Mojaris / juttis — own nothing for Indian formal right now
  3. Leather strap watch (tan or cognac)
  4. Mid-thigh length kurtas — wardrobe has no proportion balance

──────────────────────────────────────────────────────────
  Caricature  →  ./outputs/caricature_20240215.png
  Annotated   →  ./outputs/analysis_20240215_annotated.png
  JSON        →  ./outputs/analysis_20240215.json
══════════════════════════════════════════════════════════
```

---

## 🚀 CLI Interface

```bash
python src/main.py onboard                                         # first time setup
python src/main.py onboard --refresh-profile                       # rebuild profile

python src/main.py analyze --image ./photo.jpg                     # auto-detect occasion
python src/main.py analyze --image ./photo.jpg --occasion wedding_guest_indian
python src/main.py analyze --image ./photo.jpg --occasion office_western
python src/main.py analyze --image ./photo.jpg --occasion indian_casual
python src/main.py analyze --image ./photo.jpg --occasion streetwear
python src/main.py analyze --image ./photo.jpg --occasion party
python src/main.py analyze --image ./photo.jpg --occasion festival
python src/main.py analyze --image ./photo.jpg --occasion travel
python src/main.py analyze --image ./photo.jpg --occasion gym

python src/main.py analyze --image ./photo.jpg --style cartoon     # caricature styles
python src/main.py analyze --image ./photo.jpg --style pixar
python src/main.py analyze --image ./photo.jpg --style caricature

python src/main.py profile --show                                  # view your profile
python src/main.py history --last 5                                # view past analyses
```

---

## ⚠️ Error Handling — Non-Negotiable

Every external API call must:
1. Retry with exponential backoff — max 3 retries at 2s / 4s / 8s
2. Timeout — 30s for vision, 120s for caricature generation
3. Return user-friendly error message, never raw stack trace in terminal
4. Log full error internally
5. Degrade gracefully — caricature failure still returns full text analysis

---

## 🔒 Quality Gates

- API keys from `.env` only, never hardcoded
- `.env` in `.gitignore` always
- Photos not stored beyond session unless `--save-photos` passed
- `scripts/validate_env.py` runs at startup, fails loudly if keys missing
- All Pydantic models `ConfigDict(strict=True)`
- Type hints on every function, no bare `Any`
- Docstring on every public class and function
- `ruff` linting, `black` formatting

---

## 💰 Cost Per Run

| Step | API | Cost |
|---|---|---|
| Onboarding — 5 photos (one time) | Claude Vision ×5 | ~$0.03 |
| Outfit vision analysis | Claude Vision | ~$0.005 |
| Style recommendations | Claude Opus | ~$0.004 |
| Caricature generation | Replicate | ~$0.01–0.03 |
| **Per analysis session** | | **~₹2–4** |

---

## 📋 Build Order — Run Pytest After Each Step, Don't Proceed If Tests Fail

```
Step 1   src/models/ (all models) + tests/unit/test_models.py
Step 2   fashion_knowledge/color_theory.py + test_color_theory.py
Step 3   fashion_knowledge/body_types.py + test_body_types.py
Step 4   fashion_knowledge/grooming_guide.py + test_grooming_guide.py
Step 5   fashion_knowledge/accessory_guide.py + test_accessory_guide.py
Step 6   fashion_knowledge/footwear_guide.py + test_footwear_guide.py
Step 7   fashion_knowledge/indian_wear.py + test_indian_wear.py
Step 8   fashion_knowledge/western_wear.py + test_western_wear.py
Step 9   fashion_knowledge/fabric_guide.py (integrated into steps 7+8 tests)
Step 10  services/image_service.py + test_image_service.py
Step 11  services/anthropic_service.py + services/replicate_service.py + mocked tests
Step 12  agents/vision_agent.py + test_vision_agent.py (mocked)
Step 13  agents/profile_builder.py + test_profile_builder.py (mocked)
Step 14  agents/caricature_agent.py + test_caricature_agent.py (mocked)
Step 15  agents/grooming_agent.py (tested via recommendation tests)
Step 16  agents/recommendation_agent.py + test_recommendation_agent.py (mocked)
Step 17  output/renderer.py + output/formatter.py
Step 18  agents/style_agent.py (master orchestrator)
Step 19  storage/profile_store.py + storage/history_store.py
Step 20  src/main.py (Click CLI)
Step 21  tests/integration/test_full_pipeline.py (all mocked)
Step 22  requirements.txt + .env.example + README.md

Rule: pytest must pass before proceeding to next step. No exceptions.
```

---

*This CLAUDE.md is the single source of truth. Every implementation decision traces back here.*
