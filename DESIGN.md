# Design direction

Committed for this project; every surface (`wordcount.py`, `demo.sh`) consumes
these tokens. Nothing in the build falls back to a generic slate-and-blue
default.

## Surface and archetype

| Decision | Value |
| --- | --- |
| Archetype | `cli` — a console program, not a web page |
| Style family | calm-precise |
| Surface / mode | terminal dark (`#0b0f0e` on a dark terminal) |
| Type personality | mono / mono — **system monospace**, no webfont, no remote asset |
| Density | compact |
| Signature | aligned columns; box-drawing rules; one accent for primary status; no colour-only signal |

There is no CSS in this project: the "design source of truth" is the `THEME`
table in `wordcount.py` plus the escape sequences in `demo.sh`. Both encode the
same palette, and both refuse to emit colour unless the stream is a terminal
and `NO_COLOR` is unset.

## Palette

| Token | OKLCH | Hex | Role |
| --- | --- | --- | --- |
| accent | `oklch(0.58 0.12 170)` | `#00906f` | primary status: the `wordcount:` diagnostic label, the `ok` verdict, the pass/fail footer |
| foreground | `oklch(0.95 0.008 170)` | `#e6edea` | body text |
| muted | `oklch(0.70 0.012 170)` | `#9aa8a4` | chrome: rules, section captions, the `usage:` label |
| surface | `oklch(0.16 0.008 170)` | `#0b0f0e` | the terminal background the ramp is built against |

Hue 170 is carried through every token; the neutrals are the same hue at
chroma `≤ 0.012`, so the accent reads as the only chromatic event on screen.

### Contrast against the surface (`#0b0f0e`)

| Pair | Ratio | Verdict |
| --- | --- | --- |
| foreground `#e6edea` | ≈ 16.2:1 | AAA |
| muted `#9aa8a4` | ≈ 7.8:1 | AAA |
| accent `#00906f` | ≈ 4.8:1 | AA for normal text |

### ANSI encoding

24-bit colour is emitted as `ESC[38;2;r;g;b m` from the hex values above
(`#00906f` → `38;2;0;144;111`, `#9aa8a4` → `38;2;154;168;164`), reset with
`ESC[0m`. Nothing depends on `$TERM` capabilities beyond a plain `isatty()`
check, so an unknown terminal degrades to correct, uncoloured text rather than
wrong colour.

## Shape language

* **No chrome.** No boxes around output, no spinners, no banners inside the
  program itself — the tool prints one integer and exits.
* **Box-drawing rules** (`─`, U+2500) separate sections in `demo.sh`; the
  aligned table uses the same character for its column underline so the whole
  transcript shares one separator system.
* **Aligned columns.** File names are left-aligned in a fixed 32-character
  column, word totals are right-aligned in a 6-character column, verdicts start
  at a fixed offset — so counts line up down the page and differences are
  readable at a glance.
* **One accent, and never alone.** Every state also carries a word (`ok`,
  `exit 1`, `MISMATCH`, `all 15 checks passed`), so the palette is decoration
  rather than the signal. Colour is suppressed for pipes, `NO_COLOR`, and
  `TERM=dumb`; the recording stays legible either way.

## What is intentionally plain

stdout is machine-facing, so the count is emitted with **no** colour, padding
or decoration — pipes, `$(...)` capture and `wc` all see the bare integer. All
styling lives on stderr and in `demo.sh`, the two human-facing surfaces.
