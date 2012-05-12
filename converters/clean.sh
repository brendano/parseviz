perl -e 'undef $/; $_=<>; s/[()]\S*//g; s/\s+/ /g; s/(^\s*|\s*$)//g; print "$_\n";'
