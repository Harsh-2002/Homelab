---
name: Homelab Architecture Diagrams
description: A restrained visual system for readable, code-generated technical schematics.
colors:
  primary: "#225d82"
  secondary: "#25675d"
  ink: "#18252c"
  muted: "#52636d"
  rule: "#c7d2d7"
  paper: "#f8fafb"
  surface: "#ffffff"
  blue-wash: "#edf4f8"
  teal-wash: "#edf5f1"
typography:
  display:
    fontFamily: "Arial, Liberation Sans, sans-serif"
    fontSize: "46px"
    fontWeight: 600
  headline:
    fontFamily: "Arial, Liberation Sans, sans-serif"
    fontSize: "28px"
    fontWeight: 600
  title:
    fontFamily: "Arial, Liberation Sans, sans-serif"
    fontSize: "25px"
    fontWeight: 600
  body:
    fontFamily: "Arial, Liberation Sans, sans-serif"
    fontSize: "22px"
    fontWeight: 400
  label:
    fontFamily: "Arial, Liberation Sans, sans-serif"
    fontSize: "20px"
    fontWeight: 400
rounded:
  node: "12px"
  enclosure: "16px"
spacing:
  sheet-inset: "64px"
  host-column-gap: "56px"
  node-inset: "22px"
  enclosure-inset: "24px"
components:
  service-node:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.node}"
    padding: "22px"
  host-frame:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.enclosure}"
    padding: "24px"
    width: "720px"
    height: "650px"
  cluster-panel:
    backgroundColor: "{colors.blue-wash}"
    textColor: "{colors.ink}"
    rounded: "{rounded.enclosure}"
    padding: "40px 24px"
  flow-card:
    backgroundColor: "{colors.teal-wash}"
    textColor: "{colors.ink}"
    rounded: "{rounded.node}"
    padding: "24px"
---

# Design System: Homelab Architecture Diagrams

## Overview

**Creative North Star: “The Engineering Schematic.”**

This visual system applies to the static architecture sheets in this directory. It uses a cool paper field, plain sans-serif labels, fine strokes and measured spacing so containment and relationships remain easy to follow. Color is reserved for grouping and selected paths; geometry carries the explanation.

**Key Characteristics:**

- Fixed landscape sheets composed from editable SVG geometry.
- Blue grouping and teal relationship accents against quiet neutrals.
- Static, flat presentation with no generated imagery or external assets.

## Colors

The palette is cool and restrained: ink and muted gray-blue carry text, while two accents distinguish grouping from selected relationships.

### Primary
- **Blueprint Blue** (`primary`): Used for cluster grouping, related headings and selected connectors.

### Secondary
- **Muted Teal** (`secondary`): Reserved for selected dependency and data paths, with a pale teal wash for flow cards.

### Neutral
- **Dark Blue-Grey Ink** (`ink`): Main headings and node titles.
- **Slate Blue-Grey** (`muted`): Supporting labels and secondary copy.
- **Fine Divider Gray** (`rule`): Panel outlines, separators and quiet connector lines.
- **Cool Near-White Paper** (`paper`): Sheet background.
- **White Surface** (`surface`): Default node and host-panel fill.
- **Pale Blue Wash** (`blue-wash`): Cluster and selected grouped nodes.
- **Pale Teal Wash** (`teal-wash`): Data-flow cards.

**The Color-Has-Meaning Rule.** Keep blue for grouping and teal for selected relationships; use neutrals for most text and structure.

## Typography

**Display Font:** Arial (with Liberation Sans and sans-serif fallbacks)<br>
**Body Font:** Arial (with Liberation Sans and sans-serif fallbacks)<br>
**Label/Mono Font:** None; labels use the same plain sans-serif family.

**Character:** Compact, direct and technical. Weight and size establish hierarchy without a separate display face, decorative lettering or uppercase styling.

### Hierarchy
- **Display:** Sheet title.
- **Headline:** Flow-group headings.
- **Title:** Host, node and panel headings.
- **Body:** Service descriptions and relationship notes.
- **Label:** Page metadata, footers and compact notes.

The generated SVGs use an 18–46px type range, with a few intermediate sizes for fit and emphasis. Repeated body lines use explicit baseline spacing; there is no letter-spacing treatment.

## Layout

Each sheet uses a fixed 2400 × 1820 landscape viewBox. The host-placement sheet starts with an access band, continues through three equal-width physical-host columns, then a shared cluster panel and a compact boundary row. The flow sheet organizes relationships into horizontal groups separated by fine rules. Both use a 64px outer inset, generous column gaps and left-aligned labels; connector paths turn at right angles. The layout is static and intended to remain legible when zoomed or printed from SVG/PDF.

## Elevation & Depth

The diagrams are flat: there are no shadows, gradients or motion. Grouping comes from pale color washes, fine outlines, whitespace and containment.

## Shapes

Nodes use softly rounded corners; larger host and cluster enclosures use the wider radius in the token set. Most box strokes are 1.5px, with host frames and the cluster edge using slightly stronger gray-blue outlines. Relationship lines are thin, with small arrowheads; dashed paths distinguish selected configuration or dependency links in the flow sheet.

## Components

- **Service node:** A white rounded rectangle with a semibold title and muted supporting lines. Compact nodes reduce title and body size to fit their assigned slot.
- **Host frame:** A large white enclosure that groups one physical host and its guests; the header aligns host identity and hardware details above a thin divider.
- **Cluster panel:** A pale-blue enclosure below the host columns, subdivided into three information groups.
- **Flow card:** A pale-teal rounded panel for the three highlighted data-path examples.

These are static diagram primitives, not interactive controls.

## Do's and Don'ts

### Do
- **Do** keep the page title, group headings and supporting copy in the established sans-serif hierarchy.
- **Do** use containment, whitespace and orthogonal lines to make relationships readable.
- **Do** reserve the two accent colors for grouping and selected paths.

### Don't
- **Don't** add shadows, gradients, motion, icon libraries or generated imagery.
- **Don't** use accent colors as decoration or introduce an additional palette.
- **Don't** turn the sheets into a dashboard or add interactive controls.
