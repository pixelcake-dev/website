The two typefaces of the site, served from here.

- **Inter** 4.001, variable weight. Copyright 2016 The Inter Project Authors (https://github.com/rsms/inter)
- **JetBrains Mono** 2.211, regular and medium. Copyright 2020 The JetBrains Mono Project Authors (https://github.com/JetBrains/JetBrainsMono)

Both are distributed under the SIL Open Font License 1.1: the full text is in `Inter-OFL.txt` and `JetBrainsMono-OFL.txt`.

The files are the Latin sets in WOFF2, as packaged by [Fontsource](https://fontsource.org): the characters of other scripts are left out, and nothing else is changed.

The arrow → (U+2192) is in none of the Latin sets. `inter-arrow-wght-normal.woff2` and `jetbrains-mono-arrow-wght-normal.woff2` hold that one character, from the same versions of the same typefaces (Inter 4.001, JetBrains Mono 2.211), under the same licence: they are the subsets Google Fonts makes for a single character (`text=→`). The style sheet uses them for that character alone (`unicode-range: U+2192`).
