# CSS Architecture Documentation

## Overview

This document outlines the CSS architecture and organization for the SGK Export application. We follow a component-based approach with a modular file structure to ensure maintainability, reusability, and performance.

## File Structure

```
app/static/css/
├── main.css                # Main CSS file with imports and global styles
├── critical.css            # Critical CSS for above-the-fold content
├── styles.css              # Legacy styles (gradually being refactored)
├── components/             # Component-specific styles
│   ├── buttons.css         # Button styles
│   ├── dashboard.css       # Dashboard-specific styles
│   ├── forms.css           # Form elements and layouts
│   ├── modal.css           # Modal styles
│   ├── modals.css          # Enhanced modal styles (to be merged with modal.css)
│   ├── navigation.css      # Navigation and menu styles
│   ├── preview.css         # Document preview styles
│   ├── print.css           # Print-specific styles
│   ├── profile.css         # User profile styles
│   ├── states.css          # Element state styles (hidden, visible, etc.)
│   └── tables.css          # Table styles
└── layouts/                # Layout structures for different pages
```

## CSS Methodology

We follow these principles for our CSS architecture:

1. **Component-Based**: Each UI component has its own CSS file
2. **BEM Naming**: We use BEM (Block, Element, Modifier) naming convention
3. **Minimal Specificity**: We avoid deep nesting and keep specificity low
4. **No Inline Styles**: All styles are defined in CSS files, not inline
5. **CSS Variables**: We use CSS custom properties for theming and consistency

## Theming

Core design tokens are defined as CSS variables in `main.css`:

```css
:root {
    --primary-color: #4169E1;
    --secondary-color: #718096;
    --success-color: #48BB78;
    --danger-color: #F56565;
    --warning-color: #ED8936;
    --info-color: #4299E1;
    --text-primary: #2D3748;
    --text-secondary: #4A5568;
    --background-primary: #FFFFFF;
    --background-secondary: #F7FAFC;
    --border-color: #E2E8F0;
}
```

## Component Structure

Each component CSS file follows this structure:

1. Component-specific variables (if needed)
2. Component layout and structure
3. Component variations
4. Component states
5. Responsive adjustments

## State Management

Element states are managed through classes, not inline styles:

- `.hidden` - Element is not displayed
- `.display-inline` - Element uses inline display
- `.readonly-input` - Styling for read-only form fields

## Media Queries

We use a mobile-first approach with breakpoints defined as:

```css
/* Mobile (default) */
/* Tablet */
@media (min-width: 768px) { ... }
/* Desktop */
@media (min-width: 1024px) { ... }
/* Large Desktop */
@media (min-width: 1400px) { ... }
```

## Performance Optimization

1. **Critical CSS**: Above-the-fold styles are inlined
2. **Lazy-loading**: Non-critical CSS is loaded with `preload` and `onload`
3. **Minimal Reset**: We use a minimal CSS reset to reduce overhead
4. **No CSS Frameworks**: We avoid heavy CSS frameworks
5. **Optimization**: CSS is minified in production

## Best Practices

1. **No `!important`**: Avoid using `!important` except for utility classes
2. **Document Unusual CSS**: Comment any non-obvious CSS techniques
3. **Consistent Units**: Use `rem` for typography, `px` for borders, `%` for layout
4. **Use Flexbox/Grid**: Prefer modern layout techniques 
5. **Test All Breakpoints**: Ensure all components work across all device sizes

## Contributing

When adding new styles:

1. Identify the appropriate component file or create a new one
2. Follow the existing naming conventions
3. Add responsive styles as needed
4. Document any complex techniques
5. Avoid adding inline styles to HTML templates

## Legacy Code

The `styles.css` file contains legacy styles that are being gradually refactored into the component-based structure. New features should avoid using these styles and instead use or create component-specific styles. 