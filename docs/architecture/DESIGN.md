---
name: Homelab Topology Diagrams
description: Native Excalidraw topology tree and labelled relationship frames.
colors:
  canvas: "#f8fafc"
  ink: "#263848"
  node-text: "#233647"
  frame-title: "#142b3c"
  tree-key: "#536575"
  ownership-arrow: "#9baab5"
  arrow-fallback: "#9caab4"
  flow-arrow: "#2c7185"
  physical-fill: "#e7eff8"
  guest-fill: "#e8f4f0"
  logical-fill: "#f0edf9"
  service-fill: "#ffffff"
  device-fill: "#fff3df"
typography:
  display:
    fontFamily: "Helvetica, Arial, sans-serif"
    fontSize: "30px"
    fontWeight: 400
  body:
    fontFamily: "Helvetica, Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.25
  key:
    fontFamily: "Helvetica, Arial, sans-serif"
    fontSize: "17px"
    fontWeight: 400
  label:
    fontFamily: "Helvetica, Arial, sans-serif"
    fontSize: "13px"
    fontWeight: 400
  callout:
    fontFamily: "Helvetica, Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 400
rounded:
  node: "6px"
spacing:
  node-label-inset: "12px"
  frame-title-inset-x: "36px"
  frame-title-inset-y: "30px"
components:
  topology-node:
    backgroundColor: "{colors.service-fill}"
    textColor: "{colors.node-text}"
    rounded: "{rounded.node}"
    padding: "10px 12px"
  frame-title:
    textColor: "{colors.frame-title}"
    typography: "{typography.display}"
  flow-label:
    textColor: "{colors.flow-arrow}"
    typography: "{typography.callout}"
---

# Design System: Homelab Topology Diagrams

## Overview

**Creative North Star: “The Connected Topology.”**

One native Excalidraw scene combines the 131-node, 130-edge ownership and network-attachment tree with 20 labelled flow frames. The tree shows physical devices and hosts through VM/LXC guests to Docker and Kubernetes services. Focused frames trace selected request and data paths.

The public scene is names-only. The private scene adds IP:port labels from local ignored address maps. The scene uses native shapes, text, frames and arrows; its PNGs are frame exports. Local rendering uses the official CLI and needs no account, API key or hosted service.

**Key Characteristics:**

- One editable canvas: a left-to-right topology tree and 20 focused flow frames.
- Node fill identifies physical, guest, logical, service or device categories.
- Relationship labels carry meaning; connector styling alone is not a relationship taxonomy.

## Colors

Dark blue-grey carries labels and outlines; restrained fills separate node categories, while muted neutral and teal strokes distinguish topology links from focused flow links.

### Primary
- **Topology Ink** (ink): Shared shape and text outline color.
- **Flow Teal** (flow-arrow): Focused relationship arrows and their labels.

### Neutral
- **Canvas** (canvas): Excalidraw scene background.
- **Node Text** (node-text): Text inside labelled nodes.
- **Frame Title** (frame-title): Frame headings.
- **Tree Key** (tree-key): Build date and tree-scope note.
- **Ownership Arrow** (ownership-arrow): Tree ownership/network-attachment links.
- **Arrow Fallback** (arrow-fallback): Generator helper default; current tree and flow calls specify their own arrow colors.

### Node Fills
- **Physical** (physical-fill), **Guest** (guest-fill), **Logical** (logical-fill), **Service** (service-fill) and **Device** (device-fill) identify node categories.

**The Labelled-Arrow Rule.** Read the arrow label for relationship meaning. Do not infer packet flow, membership or dependency from color or dash style alone.

## Typography

**Display Font:** Helvetica (with Arial and sans-serif fallbacks)<br>
**Body Font:** Helvetica (with Arial and sans-serif fallbacks)<br>
**Label/Mono Font:** None.

The generator uses Excalidraw font family 2, Helvetica. The hierarchy is compact and consistent across the canvas.

### Hierarchy
- **Display** (400, 30px): Frame headings.
- **Key** (400, 17px): Tree edition, date and relationship-scope note.
- **Body** (400, 16px): Node labels.
- **Callout** (400, 14px) and **Label** (400, 13px): Flow annotations; the generator uses both sizes.

## Layout

The tree is laid out left to right from Graphviz coordinates and occupies one native frame. Its dimensions follow the graph; the current manifest records about 3469 × 3405 units. Twenty 2800 × 400 flow frames sit to its right, stacked with 50 units between frames. The canvas and frame contents are fixed; no responsive reflow is defined.

## Elevation & Depth

The scene is flat: no shadows, gradients or motion. Node categories, frame boundaries, whitespace and connector geometry carry the hierarchy.

## Shapes

Nodes are native rounded rectangles with a 6px radius, 1.4px outline and 12px text inset. Arrows use native bound connectors with an end arrowhead; tree routing follows Graphviz polylines. Fan-out links in several flow frames are dashed across different relationship types, so their explicit labels are authoritative.

## Components

- **Topology node:** A native labelled rectangle. Its fill follows the node category; text uses the shared body style.
- **Frame title:** Native text at the upper-left of each frame.
- **Flow label and arrow:** A labelled native connector; flow annotations use teal. Some fan-out connectors are dashed, without assigning one universal meaning to that dash.

These are static diagram primitives. They are not controls or a responsive web interface.

## Do's and Don'ts

### Do
- **Do** use the tree for ownership and network attachment, and flow frames for labelled end-to-end paths.
- **Do** read each relationship label, especially on dashed fan-out connectors.
- **Do** preserve unknown hardware and network details as unknown.
- **Do** keep the IP-bearing scene and address sources private.

### Don't
- **Don't** read every tree edge as a packet path.
- **Don't** infer relationship semantics from dash style or color alone.
- **Don't** publish the private scene or its local address maps.
