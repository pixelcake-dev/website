<h1>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/pixelcake-orizzontale-negativo.svg">
    <img src="assets/pixelcake-orizzontale-colore.svg" alt="PixelCake" width="300">
  </picture>
</h1>

**Infrastructure, piece by piece.**

This is the website of PixelCake, a visual designer for small networks that runs in the browser:
you draw the network, configure it, and ask it whether one device reaches another.

Two static pages, with nothing to build:

- `index.html`: what PixelCake is and what it does
- `why.html`: why I am building it
- `assets/`: the style sheet, a small script (light and dark theme, the drawings), the logo, and pictures of the app in both themes
- `assets/fonts/`: the two typefaces, Inter and JetBrains Mono, served from the site itself, each with its licence
- `tools/drawings.py`: draws the five illustrations and writes them into the pages

The pages load nothing from other sites: no trackers, no cookies, no fonts from elsewhere.

To look at the site, open `index.html` in a browser. To change a drawing, edit `tools/drawings.py` and run it:

```bash
python tools/drawings.py
```

## Licence

The texts, the drawings, the pictures and the logo are © Phil-pje, all rights reserved: see [LICENSE](LICENSE).
PixelCake itself, the application, is free software under the GNU AGPL v3.0.
The typefaces keep their own licence (SIL Open Font License 1.1).

Contact: pixelcake.dev@gmail.com
