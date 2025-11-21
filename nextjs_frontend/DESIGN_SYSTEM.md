# AUB LMS Design System

## Color Palette

### Primary Colors
```css
--aub-green-dark: #1a4d2e      /* Deep forest green - primary brand */
--aub-green: #2d5f3f           /* AUB green - headers, buttons */
--aub-green-light: #4a7c59     /* Hover states */
--aub-green-pale: #e8f5e9      /* Backgrounds, subtle accents */

--aub-gold: #c5a572            /* Gold accent - highlights */
--aub-gold-light: #d4b98a      /* Lighter gold */
--aub-gold-dark: #a68a5c       /* Darker gold for text */

--aub-white: #ffffff           /* Pure white */
--aub-cream: #faf8f3           /* Warm off-white background */
--aub-beige: #f5f1e8           /* Light beige for cards */
```

### Semantic Colors
```css
--success: #2e7d32
--warning: #f57c00
--error: #c62828
--info: #0277bd
```

### Text Colors
```css
--text-primary: #1a1a1a        /* Main text */
--text-secondary: #4a4a4a      /* Secondary text */
--text-muted: #757575          /* Muted text */
--text-on-green: #ffffff       /* Text on green backgrounds */
```

## Typography

### Font Stack
```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

### Font Sizes
- Heading 1: 2.5rem (40px) - Page titles
- Heading 2: 2rem (32px) - Section headers
- Heading 3: 1.5rem (24px) - Card titles
- Heading 4: 1.25rem (20px) - Subsections
- Body: 1rem (16px) - Main text
- Small: 0.875rem (14px) - Captions, labels
- Tiny: 0.75rem (12px) - Badges, metadata

## Spacing System

Based on 4px grid:
- xs: 4px
- sm: 8px
- md: 16px
- lg: 24px
- xl: 32px
- 2xl: 48px
- 3xl: 64px

## Components

### Buttons
- Primary: Green background, white text
- Secondary: White background, green border, green text
- Tertiary: Transparent, green text
- Danger: Red background, white text

### Cards
- White background
- Subtle shadow
- Rounded corners (8px)
- Hover: slight elevation increase

### Inputs
- Border: light gray
- Focus: green border
- Rounded corners (6px)

### Navigation
- Top bar: Deep green background
- Active link: Gold underline
- Hover: Light green background

## Layout Grid

- Desktop: 12-column grid, 1200px max width
- Tablet: 8-column grid, 768px max width
- Mobile: 4-column grid, 100% width

## Accessibility

- WCAG 2.1 AA compliance
- Minimum contrast ratio: 4.5:1
- Focus indicators on all interactive elements
- Keyboard navigation support
- Screen reader friendly labels

