# walkForwardCorrelation/render — how it is read

| file | what it does | in → out |
|---|---|---|
| `scatter.py` | The correlation figure: every parameter tuple as one point, in-sample against out-of-sample | points → svg |
| `figures.py` | The CSCV page: the lambda bands, the partition cloud, and every statistic explained | rows → html |

Inline SVG, no plotting library and no image files: the page is one self-contained `.html` the owner
can open from anywhere.

Above 25 points the per-point captions stop helping and start hiding, so `scatter` drops them and
keeps the stratum colours — one hue per stratum, distinguishable in greyscale by shape as well.

**Every statistic on the CSCV page carries its own explanation in Spanish.** A number the reader
cannot interpret is a number that gets used wrong; `figures.py` is long for that reason and should
stay that way.
