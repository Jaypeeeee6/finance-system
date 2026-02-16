# Design Tokens — Responsive Breakpoints

This document centralizes the project's responsive breakpoints so layouts stay consistent across viewports. Use the same `max-width` values in media queries when adding or changing responsive styles.

- File reference: `static/css/style.css`, `static/css/write_cheque.css`, `static/css/responsive.css`

## Breakpoints

| Breakpoint | Target | Where used |
|------------|--------|------------|
| **1200px** | Small desktop / laptop | `write_cheque.css`: cheque layout single column, preview panel order, bank selection 2 cols |
| **1072px** | Tablet / dashboard filters | `responsive.css`: dashboard only — filters (dropdowns) below search bar |
| **1024px** | Tablet / small laptop | `style.css`: hamburger menu, nav as dropdown/collapsible; `responsive.css`: pagination (compact), main content padding, step tabs overflow (no dashboard-specific styles at this breakpoint) |
| **768px** | iPad portrait / tablet | `style.css`: nav padding, dashboard header column, stats 1 col, form-row 1 col, recurring modal 95%; `write_cheque.css`: cheque container padding, form/preview panels, amount input 1 col, bank selection 1 col, form actions column, modal 95%; `responsive.css`: pagination, dashboard full-bleed, step tabs |
| **420px** | Small phone | `responsive.css`: pagination (smaller buttons), dashboard full-bleed, step tabs, table Actions column min-width reduced |

## CSS files

- **`static/css/style.css`**: App shell (nav, hamburger, dashboard header, stats grid), search input, form rows, recurring modal.
- **`static/css/write_cheque.css`**: Write cheque page (cheque layout, form, preview, bank selection, modals).
- **`static/css/responsive.css`**: Pagination, payment-requests/dashboard tables, IT dashboard full-bleed, step tabs.

## Usage

When adding new responsive styles, use the same `max-width` values so behavior stays consistent:

```css
@media (max-width: 1200px) {
  /* Small desktop / cheque layout */
}

@media (max-width: 1072px) {
  /* Dashboard: filters below search bar */
}

@media (max-width: 1024px) {
  /* Tablet / hamburger nav */
}

@media (max-width: 768px) {
  /* iPad portrait / tablet */
}

@media (max-width: 420px) {
  /* Small phone */
}
```

## Notes

- Prefer these breakpoint values over ad-hoc widths so the app behaves consistently across pages.
- Breakpoints are defined as `max-width`; use the same convention for new media queries.
