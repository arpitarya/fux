---
type: Index
description: "How the paper's twenty figures are rendered from their Mermaid sources, and how to re-render one."
---

# Figures for the paper

Every `fig-NN-*.svg` here is rendered from the Mermaid source of the same name
under `src/`, with `@mermaid-js/mermaid-cli` (theme `base`, white background).
The paper also inlines each source in a collapsed block, so it renders without
the images. To re-render one after editing its source:

```sh
npx -p @mermaid-js/mermaid-cli mmdc -c mermaid.config.json -i src/fig-NN-x.mmd -o fig-NN-x.svg -b white
```

The figures carry no timestamps and no measured value that is not also in the
paper's text; a number lives in the prose and the table, the figure repeats it.
