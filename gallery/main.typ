/**
 * main.typ
 *
 * This is an example paper which demonstrates how to use typ-files rendered
 * with custom `matplotlib` backend based on Typst.
 */

#set document(title: [#smallcaps[Typst] #smallcaps[Matplotlib] Backend Demo])
#set page(
  paper: "a4",
  margin: (left: 0.75in, right: 8.5in - (0.75in + 6.75in), top: 1.0in),
)

#set par(justify: true, leading: 0.58em)
#set text(font: "Times", size: 10pt)
#show: it => columns(2, gutter: 0.25in, it)

#lorem(50)

#lorem(50)

#lorem(50)

#lorem(50)

#lorem(50)

#lorem(50)

#lorem(50)

// NOTE The point is to include typ-file and adjust figure kind
// correspondently.
#figure(
  include "line-plot-simple.typ",
  kind: image,
  caption: [Simple line plot],
  placement: top,
) <line-plot-simple>

#lorem(50)

#lorem(50)
