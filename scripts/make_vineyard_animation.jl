#!/usr/bin/env julia

# Rebuild the distributable vineyard animation from the checked SVG template.
# The course uses only SVG and SMIL at run time, so viewers need neither Julia
# nor JavaScript.

root = normpath(joinpath(@__DIR__, ".."))
source = joinpath(root, "assets", "vineyard-animation.svg")
output = get(ARGS, 1, source)
svg = read(source, String)

for marker in ("A = 21 − t", "B = 14 − t", "C = 15 + t", "D = t",
               "repeatCount=\"indefinite\"", "fill:none")
    occursin(marker, svg) || error("Missing expected animation marker: $marker")
end

write(output, svg)
println("Wrote transparent vineyard animation to $(abspath(output))")
