# Design Tokens — Responsive Breakpoints

This document centralizes the project's responsive breakpoints so layouts stay consistent across viewports. Use the same `max-width` values in media queries when adding or changing responsive styles.

- File reference: `static/css/dashboard.css`, `static/css/inventory.css`

## Breakpoints

| Breakpoint | Target | Where used |
|------------|--------|------------|
| **1390px** | Small desktop / laptop | `dashboard.css`: topbar/content padding, search width, stats grid (4 cols), panels |
| **1190px** | iPad landscape / small laptop | `dashboard.css`: tighter padding, search 280px, page header wraps; `inventory.css`: table toolbar wraps, category dropdown 140px, card padding |
| **900px** | Narrow laptop / iPad | `dashboard.css`: content 12px 14px, search 240px; `inventory.css`: table actions/footer padding, search 180px, category 130px |
| **768px** | iPad portrait / tablet | `dashboard.css`: page header stacks (column), brand text hidden, search full width; `inventory.css`: request layout stacks, side panel full width, table toolbar/footer wrap, table wrapper 50vh |
| **640px** | Small tablet / large phone | `dashboard.css`: hamburger menu, sidebar as drawer, main margin-left 0 |
| **480px** | Phone | `dashboard.css`: stats 1 col; `inventory.css`: table column min-widths, category dropdown 120px, tighter padding |

## CSS files

- **`static/css/dashboard.css`**: App shell (topbar, sidebar, main content), page headers, stats grid, panels.
- **`static/css/inventory.css`**: Warehouse inventory, table actions, category filter, table wrapper, request layouts, side panel, grids.

## Usage

When adding new responsive styles, use the same `max-width` values so behavior stays consistent:

```css
@media (max-width: 1390px) {
  /* Small desktop / laptop */
}

@media (max-width: 1190px) {
  /* iPad / small laptop */
}

@media (max-width: 900px) {
  /* Narrow laptop / iPad */
}

@media (max-width: 768px) {
  /* iPad portrait / tablet */
}

@media (max-width: 640px) {
  /* Sidebar becomes drawer */
}

@media (max-width: 480px) {
  /* Phone */
}
```

## Notes

- Prefer these breakpoint values over ad-hoc widths so the app behaves consistently across pages.
- Breakpoints are defined as `max-width`; use the same convention for new media queries.
