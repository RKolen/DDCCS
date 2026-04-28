# Fonts — DDCCS Design System

Three typefaces are used. Currently loaded from Google Fonts CDN.
To self-host, place the TTF files below in this directory, then swap
the `@import` in `src/styles/tokens.css` to:

```css
@import url('../../../fonts/fonts.css');
```

## Required files

| Filename | Font | Weight | Style |
|---|---|---|---|
| `Cinzel-Regular.ttf` | Cinzel | 400 | normal |
| `Cinzel-SemiBold.ttf` | Cinzel | 600 | normal |
| `Cinzel-Bold.ttf` | Cinzel | 700 | normal |
| `CrimsonText-Regular.ttf` | Crimson Text | 400 | normal |
| `CrimsonText-Italic.ttf` | Crimson Text | 400 | italic |
| `CrimsonText-SemiBold.ttf` | Crimson Text | 600 | normal |
| `FiraCode-Regular.ttf` | Fira Code | 400 | normal |
| `FiraCode-Medium.ttf` | Fira Code | 500 | normal |

## Download steps

1. Visit each Google Fonts page and click **"Get font" -> "Download all"**:
   - Cinzel: https://fonts.google.com/specimen/Cinzel
   - Crimson Text: https://fonts.google.com/specimen/Crimson+Text
   - Fira Code: https://fonts.google.com/specimen/Fira+Code
2. Extract the `.zip`. The `.ttf` files are inside.
3. Rename to match the filenames above and place them in this directory.

All three fonts are released under the SIL Open Font Licence 1.1 —
free for personal and commercial use, including self-hosting.
