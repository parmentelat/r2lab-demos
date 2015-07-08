#!/usr/bin/env python3

# computes an index file in markdown/index.md from ./index.md with all the other md files referenced

import sys
import os
from glob import glob

source = "index.md"
output_dir = "markdown"

index_line_format = " * [{base} ({dir})]({base}.html)\n"

def main():
    if not os.path.isfile(source):
        print("Source not found {}".format(source))
        sys.exit(1)

    output = os.path.join(output_dir, source)
    with open(output, 'w') as result:
        # copy index.md
        with open(source) as input:
            result.write(input.read())
        for other in sys.argv[1:]:
            dir = os.path.dirname(other) or "."
            base = os.path.basename(other).replace(".md", "")
            # skip index from the index...
            if base == "index":
                continue
            result.write(index_line_format.format(dir=dir, base=base))
    print("(Over)wrote {}".format(output))

main()