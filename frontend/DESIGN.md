---
name: Hookclip
description: Dark, Linear-style design system for the Hookclip clipper tool — near-black ground, hairlines, one red accent.
colors:
  accent: "#d92d20"
  accent-deep: "#c22e23"
  accent-text: "#ff8a7a"
  neutral-bg: "#0a0a0b"
  surface: "#111113"
  surface-2: "#1a1a1e"
  ink: "#fafafa"
  ink-soft: "#a1a1aa"
  ink-faint: "#8b8b93"
  line: "#232326"
  line-strong: "#2e2e33"
  alert-bg: "#1d1210"
  alert-border: "#3d1f1a"
  alert-text: "#ff8a7a"
typography:
  display:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "56px"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.03em"
  headline:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "36px"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "20px"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "0em"
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "12.5px"
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "0.08em"
rounded:
  sm: "8px"
  md: "10px"
  lg: "12px"
  xl: "16px"
  pill: "999px"
spacing:
  section: "72px"
  card: "24px"
  row: "28px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.neutral-bg}"
    rounded: "{rounded.pill}"
    padding: "11px 20px"
  button-primary-hover:
    backgroundColor: "#e4e4e7"
  button-accent:
    backgroundColor: "{colors.accent}"
    textColor: "#ffffff"
    rounded: "{rounded.pill}"
    padding: "11px 20px"
  button-accent-hover:
    backgroundColor: "{colors.accent-deep}"
  button-disabled:
    backgroundColor: "{colors.accent}"
    textColor: "#ffffff"
  input:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "12px 16px"
---

# Design System: Hookclip

## Overview

**Creative North Star: "The Night Desk"**

Hookclip is the desk where a night of GTA VI streams turns into money. The interface is the room the work happens in: near-black, quiet, precise, with one red accent that marks only actions and the single best score. Nothing glows, nothing gradients, nothing pretends to be a photo. The product itself is the visual — the ranked moment list, the score chips, the 9:16 clip frame — shown at full size in the first viewport instead of claimed in copy.

Dark is earned by the scene, not picked by category: clippers work at night, in dark rooms, watching streams. The tool lives where the footage lives.

**Key Characteristics:**
- Near-black ground with hairline borders; depth comes from tonal layering, not shadows.
- One red accent, used sparingly: actions and the top score only.
- Hairline-divided rows instead of cards as page structure.
- Real product UI as the only visual; demonstration data is labeled as a sample.
- System font stack throughout; hierarchy comes from size, weight, and color, never a display face.

## Colors

The palette is a neutral near-black with a single red. No purple, no neon, no secondary hue.

### Primary
- **Clipper Red** (#d92d20): the one accent. CTAs, the primary action on every screen, the top score chip. White text on it passes 4.5:1. The hover/deeper state is #c22e23.
- **Red Tint for Text** (#ff8a7a): the same hue lightened for small text on dark surfaces (the "Most popular" flag, alert text). Never use the raw accent for small text — it fails contrast.

### Neutral
- **Night** (#0a0a0b): page ground.
- **Panel** (#111113): cards, panels, pricing tables.
- **Raised** (#1a1a1e): inputs, chips, project items — one step above Panel.
- **Ink** (#fafafa): display and body text.
- **Soft Ink** (#a1a1aa): secondary text, descriptions.
- **Faint Ink** (#8b8b93): meta text, captions, placeholders. Passes 4.5:1 on every surface.
- **Hairline** (#232326): borders between sections and rows.
- **Strong Hairline** (#2e2e33): input borders, chip borders, the hot plan's edge.

### Named Rules
**The One Red Rule.** Red appears on ≤10% of any screen: actions and the top score. Its rarity is the point. If red shows up somewhere that is not an action or the #1 score, it is wrong.
**The Hairline Rule.** Every divider is a 1px hairline in Hairline or Strong Hairline. No colored border above 1px on any card, list item, callout, or alert.

## Typography

**Display Font:** system stack (-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif). **Body Font:** the same stack. There is no display face and no webfont: hierarchy comes from size, weight, and color.

**Character:** plain, tight, confident. Headlines are heavy and tightly tracked; body text is regular weight with generous line height.

### Hierarchy
- **Display** (800, 56px, 1.15, -0.03em): hero headline only. Two lines maximum.
- **Headline** (800, 36px, 1.15, -0.02em): section headings.
- **Title** (800, 20px, 1.15, -0.02em): row titles, card headings, plan names.
- **Body** (400, 17px, 1.6): body copy. Measure 65–75ch; feature and step paragraphs cap at 560px.
- **Label** (700, 12.5px, 0.08em, uppercase): row tags and the "Most popular" flag.

### Named Rules
**The No Eyebrow Rule.** No kicker or eyebrow label above a heading, ever. The heading carries its own weight.

## Layout

One centered column, max width 1080px, 24px side padding. Sections are 72px tall with a 1px hairline on top. Headings sit above their content with more space above than below. The hero is centered; dashboard and checkout are left-aligned app screens. At 760px and below, grids collapse to one column, the nav hides, and section padding drops to 56px.

## Elevation & Depth

Depth is tonal layering, not shadow: ground → Panel → Raised, each one step lighter. Shadows exist in exactly two places, both soft with offset and blur, never a zero-offset halo: the hero product panel (`0 24px 60px rgba(0,0,0,0.45)`) and the hot pricing plan (`0 16px 40px rgba(0,0,0,0.35)`).

## Shapes

Corners are gently rounded: 12px on cards and panels, 10px on inputs and chips, 16px on the hero product panel, pill (999px) on buttons. Borders are 1px hairlines. No hard offset shadows, no geometric masks, no clip-path decoration.

## Components

### Buttons
- **Shape:** pill (999px). Padding 11px 20px (15px 30px large, 8px 16px small).
- **Primary:** white background, near-black text. Hover lightens to #e4e4e7.
- **Accent:** red background, white text. Hover deepens to #c22e23.
- **Disabled:** accent at 0.45 opacity, cursor not-allowed.
- **Focus:** 2px white outline, 2px offset, on every interactive element.

### Chips
- **Score chip:** 48–52px square, 10–12px radius, Raised background, Strong Hairline border, white bold tabular numerals. The top score is red.
- **Credits pill:** pill shape, Panel background, Strong Hairline border, soft gray text.

### Cards / Containers
- **Corner Style:** 12px radius.
- **Background:** Panel on the page ground.
- **Border:** 1px Hairline. The hot plan uses Strong Hairline plus a 1px outline and a soft shadow.
- **Internal Padding:** 24–28px.

### Inputs / Fields
- **Style:** Raised background, 1px Strong Hairline border, 10px radius, white text, faint placeholder.
- **Focus:** border turns Ink.
- **Error:** alert text in Red Tint on a dark red-brown ground (#1d1210) with a matching border.

### Navigation
- **Style:** sticky header, solid Night ground, 1px Hairline bottom border, 64px tall. Logo left (white square, drawn play triangle), nav links in Soft Ink, primary button right. Nav hides below 760px.

### Product panel (signature)
- **Style:** Panel background, Hairline border, 16px radius, soft shadow. Header row with title left and sample meta right; body is a grid of the moment list and a 9:16 clip frame.
- **Clip frame:** 9:16, Strong Hairline border, 10px radius, authored still image with a solid dark caption bar (never a gradient scrim).

## Do's and Don'ts

### Do:
- **Do** show the product doing its job in the first viewport — the ranked list, not a claim about it.
- **Do** keep every text color at 4.5:1 or better on its surface (verified by the Impeccable detector, Nov 15, 2026).
- **Do** label demonstration data as a sample wherever a visitor could mistake it for real output.
- **Do** theme browser surfaces from the palette: red text selection, white focus rings, dark scrollbars.
- **Do** use one authored motion moment per page (the hero panel's rise, exponential ease-out), and respect reduced-motion.

### Don't:
- **Don't** add a gradient, glow, glass panel, bento grid, or orb anywhere.
- **Don't** use same-size icon-plus-heading-plus-text cards as page structure; use hairline rows.
- **Don't** use the hero-metric template (big number, small label, supporting stats) — state the earn case in a sentence.
- **Don't** use Unicode glyphs or emoji as icons; draw the mark as SVG.
- **Don't** use monospace as a costume for "technical"; reserve it for code, data, or measurement (tabular numerals on scores and times).
- **Don't** invent social proof, customers, benchmarks, or earnings claims. Verified medians only, with the never-guaranteed caveat.
- **Don't** use em-dashes as a crutch; prefer commas and periods.
