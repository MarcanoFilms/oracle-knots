# Oracle Knots Design System

A comprehensive guide to the visual design, components, and patterns used in the Oracle Knots Control Center GUI.

**Version:** 1.0  
**Last Updated:** June 2026  
**Design Philosophy:** Modern, accessible, professional interface for Bitcoin node operators.

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [Color Palette](#color-palette)
3. [Typography](#typography)
4. [Spacing & Layout](#spacing--layout)
5. [Components](#components)
6. [Accessibility](#accessibility)
7. [Interactive States](#interactive-states)
8. [Usage Guidelines](#usage-guidelines)

---

## Design Principles

1. **Clarity First:** Information should be immediately understandable
2. **Consistency:** Reuse patterns; avoid one-off layouts
3. **Accessibility:** WCAG AA compliant, keyboard navigable, readable
4. **Performance:** Minimal animations, responsive to all devices
5. **Brand:** Neon aesthetic (cyan/purple) with professional dark theme

---

## Color Palette

### Background Colors
| Token | Value | Usage |
|-------|-------|-------|
| `--bg-darkest` | `#05070e` | Page background, deepest layer |
| `--bg-darker` | `#090d1a` | Sidebar, navigation |
| `--bg-dark` | `#0f152b` | Cards, containers |
| `--bg-card` | `rgba(13, 20, 41, 0.6)` | Semi-transparent card overlays |

### Accent Colors (Primary Brand)
| Token | Value | Usage |
|-------|-------|-------|
| `--accent-cyan` | `#00f0ff` | Primary action, focus states, highlights |
| `--accent-purple` | `#bd5eff` | Secondary accent, backgrounds |

### Status Colors (Semantic)
| Token | Value | Usage | Meaning |
|-------|-------|-------|---------|
| `--status-green` | `#00ffaa` | Success indicator, online status | Good / Active |
| `--status-red` | `#ff4365` | Error indicator, offline status | Bad / Inactive |
| `--status-orange` | `#ffb000` | Warning indicator, syncing status | Warning / In Progress |

### Text Colors
| Token | Value | Usage |
|-------|-------|-------|
| `--text-primary` | `#f1f5f9` | Body text, headings |
| `--text-secondary` | `#94a3b8` | Labels, secondary text |
| `--text-muted` | `#475569` | Metadata, helper text, disabled |

### Border & Divider
| Token | Value | Usage |
|-------|-------|-------|
| `--border-color` | `rgba(255, 255, 255, 0.06)` | Standard borders, dividers |
| `--border-color-glow` | `rgba(0, 240, 255, 0.15)` | Highlighted/hover borders |

---

## Typography

### Font Stack
```css
Sans-serif: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
Monospace: 'Fira Code', monospace
```

### Font Sizes (8px Base Unit)
| Size | Value | Usage |
|------|-------|-------|
| Extra Small | 11px | Badges, metadata, fine print |
| Small | 12px | Labels, secondary text, captions |
| Base | 14px | Body text (less common) |
| Large | 16px | Section headers, important labels |
| Extra Large | 18px | Page section headers |
| 2X Large | 24px | Page titles, hero sections |
| 3X Large | 32px | Main hero titles (future) |

### Font Weights
- **400 (Normal):** Body text, regular content
- **500 (Medium):** Labels, UI text
- **600 (Semibold):** Headings, emphasized text
- **700 (Bold):** Primary headings, strong emphasis

### Line Heights
- **1.2 (Tight):** Headings, compact text
- **1.5 (Normal):** Body text, labels
- **1.75 (Relaxed):** Long-form content (not yet used)

---

## Spacing & Layout

### Spacing Scale (8px Base Unit)
| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | 4px | Minimal gaps, tight spacing between inline elements |
| `--space-sm` | 8px | Small gap, standard spacing |
| `--space-md` | 12px | Medium gap, card padding, component gaps |
| `--space-lg` | 16px | Large gap, section spacing |
| `--space-xl` | 24px | Extra large gap, major section spacing |
| `--space-2xl` | 32px | Very large gap, top-level spacing |
| `--space-3xl` | 48px | Page-level spacing, major sections |

### Key Dimensions
- **Sidebar Width:** 260px (expanded), 64px (collapsed)
- **Header Height:** 72px
- **Minimum Touch Target:** 44px (accessibility requirement)

### Border Radius
| Token | Value | Usage |
|-------|-------|-------|
| `--border-radius-sm` | 4px | Small components, badges |
| `--border-radius` | 8px | Standard, most components |
| `--border-radius-md` | 12px | Cards, larger containers |
| `--border-radius-lg` | 16px | Large cards, modals (future) |

---

## Components

### Buttons

#### Primary Button
```html
<button class="btn btn-primary">Action</button>
```
- **Colors:** Cyan accent text
- **States:** Default, hover (brighter), active (glow), disabled (muted)
- **Size:** 44px minimum height for accessibility
- **Usage:** Main actions, primary CTAs

#### Secondary Button
```html
<button class="btn btn-secondary">Secondary</button>
```
- **Colors:** Secondary text on transparent
- **States:** Hover, active, disabled
- **Usage:** Alternative actions, less important CTAs

#### Danger Button
```html
<button class="btn btn-danger">Delete</button>
```
- **Colors:** Red text
- **States:** Hover (brighter red), active, disabled
- **Usage:** Destructive actions requiring confirmation

### Cards

#### Standard Card
```html
<div class="card">
  <div class="card-header">
    <h3>Card Title</h3>
  </div>
  <div class="card-body">
    Content here
  </div>
  <div class="card-footer">
    Footer content
  </div>
</div>
```
- **Background:** `--bg-card` or `--bg-dark`
- **Border:** `--border-color`
- **Padding:** 16px (md spacing)
- **Border Radius:** 12px
- **Hover State:** Border color to `--border-color-glow`

#### Stat Card
```html
<div class="stat-card">
  <div class="stat-header">
    <span class="stat-label">Label</span>
    <div class="stat-icon"></div>
  </div>
  <div class="stat-value">123</div>
  <div class="progress-bar-container">
    <div class="progress-bar" style="width: 50%"></div>
  </div>
  <span class="stat-desc">Description</span>
</div>
```
- **Usage:** Dashboard metrics, KPIs
- **Layout:** Vertical stack
- **Icon Position:** Top right

### Forms & Inputs

#### Text Input
```html
<input type="text" class="input-field" placeholder="Enter value">
```
- **Height:** 44px (minimum touch target)
- **Padding:** 12px horizontal, 10px vertical
- **Border:** `--border-color`
- **Focus:** Border color to `--border-color-glow`, outline to `--accent-cyan`
- **Text Color:** `--text-primary`
- **Disabled:** Background to `--bg-darker`, text to `--text-muted`

#### Form Label
```html
<label class="form-label" for="field">Field Label</label>
<input id="field" type="text" class="input-field">
```
- **Position:** Above input (not inside)
- **Size:** 12px, weight 500
- **Color:** `--text-secondary`
- **Spacing:** 8px below label

#### Select / Dropdown
```html
<select class="input-field">
  <option>Option 1</option>
</select>
```
- **Same styling as text input**
- **Padding:** Accommodate dropdown arrow
- **Min Height:** 44px

#### Checkbox & Radio
```html
<input type="checkbox" class="checkbox" id="cb">
<label class="checkbox-label" for="cb">Label</label>
```
- **Size:** 16x16px (larger than standard for accessibility)
- **Focus Ring:** Visible, cyan
- **Checked:** Use `--accent-cyan`

### Status Indicators

#### Status Dot
```html
<span class="status-dot online"></span>
<span class="status-dot offline"></span>
<span class="status-dot syncing"></span>
```
- **Size:** 8px diameter
- **Color Classes:** `.online`, `.offline`, `.syncing`
- **Glow Effect:** Box-shadow for visual depth
- **Animations:** `.syncing` has pulse animation

#### Badge
```html
<span class="badge badge-accent">Label</span>
<span class="badge badge-outline">Label</span>
```
- **Padding:** 4px horizontal, 2px vertical
- **Font Size:** 11px
- **Border Radius:** 4px
- **Variants:** `badge-accent`, `badge-outline`, `badge-success`, `badge-danger`

### Navigation

#### Sidebar Navigation Item
```html
<button class="nav-item active" data-tab="dashboard">
  <svg class="nav-icon">...</svg>
  <span class="nav-label">Dashboard</span>
</button>
```
- **Height:** 44px (minimum)
- **Padding:** 12px 16px
- **Border Radius:** 12px
- **Active State:** Cyan background, text, and glow
- **Hover State:** Lighter background, primary text

#### Header Metrics Pill
```html
<div class="header-peers-pill">
  <span class="header-peers-label">Peers</span>
  <span class="header-peers-value">11</span>
</div>
```
- **Layout:** Inline flex with gap
- **Background:** Subtle transparency
- **Border:** `--border-color`
- **Padding:** 6px 12px

### Progress & Loaders

#### Progress Bar
```html
<div class="progress-bar-container">
  <div class="progress-bar" style="width: 62%"></div>
</div>
```
- **Height:** 4px
- **Background:** `--bg-dark`
- **Fill Color:** `--accent-cyan`
- **Glow:** Optional box-shadow for emphasis

#### Pulse Animation
```css
animation: pulse 1.5s infinite alternate;
```
- **Usage:** Syncing/loading status indicators
- **Speed:** 1.5s

### Modals & Dialogs

#### Modal Container
```html
<div class="modal-backdrop">
  <div class="modal">
    <div class="modal-header">
      <h2>Modal Title</h2>
      <button class="btn-close">&times;</button>
    </div>
    <div class="modal-body">Content</div>
    <div class="modal-footer">
      <button class="btn btn-secondary">Cancel</button>
      <button class="btn btn-primary">Confirm</button>
    </div>
  </div>
</div>
```
- **Backdrop:** Dark with opacity, blur effect
- **Width:** 90vw max 600px (responsive)
- **Border Radius:** 12px
- **Close Button:** Top right, `btn-close`

---

## Accessibility

### Keyboard Navigation
- All interactive elements must be keyboard accessible
- Tab order should follow logical flow (left to right, top to bottom)
- Focus indicators must be visible (cyan outline, 2px)

### Color Contrast
All text color combinations meet WCAG AA standards (4.5:1 contrast for normal text, 3:1 for large text).

### Touch Targets
- Minimum 44x44px for all interactive elements
- Buttons, links, and inputs must meet this standard
- Larger (48x48px) on mobile devices

### Semantic HTML
- Use proper HTML elements: `<button>` for buttons, `<input>` for inputs, `<nav>` for navigation
- Use `aria-label` for icon-only buttons
- Use `aria-expanded` for collapsible sections

### Screen Readers
- Form labels must be associated with inputs: `<label for="id">...</label>`
- Use descriptive button text (avoid "Click Here")
- Use `aria-live` for status updates

---

## Interactive States

### Buttons
| State | Style |
|-------|-------|
| Default | Subtle background, primary text |
| Hover | Background lighter, text brighter, cursor pointer |
| Active/Pressed | Enhanced glow, darker background |
| Focus | Visible cyan outline, 2px |
| Disabled | Muted background and text, cursor not-allowed |

### Inputs
| State | Style |
|-------|-------|
| Default | `--border-color` border, primary text |
| Hover | Border lighter, subtle background change |
| Focus | Cyan outline (2px), `--border-color-glow` |
| Filled | Background to `--bg-dark` if used |
| Disabled | Muted border and text, cursor not-allowed |
| Error | Red left border (4px), error message below |

### Links/Navigation Items
| State | Style |
|-------|-------|
| Default | `--text-secondary` |
| Hover | `--text-primary`, background shift |
| Active | `--accent-cyan`, background glow |
| Focus | Cyan outline |
| Visited | Darker cyan (if applicable) |

---

## Usage Guidelines

### Do's ✓
- Use consistent spacing (multiples of 8px)
- Apply `--border-radius` (8px) to most components
- Ensure 44px minimum touch targets
- Use semantic color meanings (green=good, red=bad, orange=warning)
- Maintain text hierarchy with font weights and sizes
- Test color contrast with WCAG AA checker

### Don'ts ✗
- Don't use inline styles; use CSS classes
- Don't create custom colors outside the palette
- Don't use components with less than 44px height
- Don't over-animate (performance impact)
- Don't violate text contrast standards
- Don't create new button variants; use existing `btn-primary`, `btn-secondary`, `btn-danger`

### Responsive Design
- Mobile first: Design for 320px, enhance for larger
- Breakpoints: 320px (mobile), 768px (tablet), 1024px (desktop), 1920px (large)
- Sidebar collapses on mobile; use hamburger menu if needed
- Cards stack vertically on tablet/mobile
- Forms expand to full width on small screens

### Animation Best Practices
- Use `--transition-speed` (0.25s) for state changes
- Animations should aid understanding, not distract
- Avoid animations on hover for mobile (no hover state)
- Use `will-change` sparingly for performance

---

## Future Enhancements

- [ ] Dark mode toggle (currently always dark)
- [ ] Light theme variant
- [ ] Custom color theming
- [ ] Component Storybook
- [ ] Automated accessibility testing
- [ ] CSS-in-JS for dynamic theming
- [ ] Motion design guidelines
- [ ] Micro-interactions documentation

---

## Maintenance

When adding new components or styles:
1. Check if a similar component exists; reuse if possible
2. Name classes semantically (`.btn-primary` not `.btn-blue`)
3. Use existing design tokens; don't hardcode colors
4. Test accessibility: contrast, keyboard nav, screen readers
5. Test responsiveness on mobile/tablet/desktop
6. Document the component in this guide
7. Update `design-tokens.css` if introducing new tokens
