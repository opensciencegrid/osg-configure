#!/bin/bash

for x in `find configs -type f`; do bx=$(basename $x); grep -qrF $bx * || echo $x unused; done | sort
