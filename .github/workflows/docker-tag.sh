#!/bin/sh
REF=$@
echo $@ | \
    sed -E 's|^refs/heads/master$|latest|' | \
    sed -E 's|^refs/pull/(.*)|pr-\1|' | \
    sed -E 's|^refs/(heads\|tags)/(.*)|\2|' | \
    sed -E 's|/|-|g'
