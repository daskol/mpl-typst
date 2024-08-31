![Linting and testing][1]
![Nightly][2]

[1]: https://github.com/nntile/nntile/actions/workflows/on-schedule.yml/badge.svg
[2]: https://github.com/nntile/nntile/actions/workflows/on-push.yml/badge.svg

# Typst Matplotlib Backend

*Typst backend for matplotlib (Python visualization library).*

## Overview

At the moment, Typst supports main vector and raster image formats. Namely,
images in PNG, JPEG, GIF, or SVG format can be easily emplaced in a document
with Typst. However, it is **not possible** to keep metadata and annotations.
These are mandatory in order to allow a reader to select and interact with
vector content (e.g. text) on images. Although SVG can contain text metadata in
principle, Typst does not support this feature at the moment but still it is
able to render SVG as a vector content.

This package solves this problem for `matplotlib` users. Basically, this
project implements a custom render (or backend) for `matplotlib` which
generates `typ`-file containing Typst markup. Generated markup file can be
later included in the original markup so that the resulting PDF will have
interactable content. Matplotlib exploits exactly the same strategy in order to
generate PGF-files &mdash; a LaTeX markup itself &mdash; which can be included
into LaTeX markup directly.

## Usage

In order to render image with `mpl_typst` one can import `mpl_typst.as_default`
module in order to use `mpl_typst` backend by default.

```python
import mpl_typst.as_default
```

Or one can configure it manually.

```python
import matplotlib
import mpl_typst
mpl.use('module://mpl_typst')
```

Also, it is possible to use rendering context as usual to override backend.

```python
import matplotlib as mpl
import mpl_typst
with mpl.rc_context({'backend': 'module://mpl_typst'}):  # or mpl_typst.BACKEND
    ...
```

Next, you can save your figure to `typ` as usual.

```python
fig, ax = plt.subplots()
...
fig.savefig('line-plot-simple.typ')
```

As soon as you get a `typ`-file you can included it directly to `figure`
function and adjust figure time.

```typst
#figure(
  include "line-plot-simple.typ",
  kind: image,
  caption: [Simple line plot],
  placement: top,
) <line-plot-simple>
```
