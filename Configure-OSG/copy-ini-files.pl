#!/usr/bin/env perl

use strict;
use warnings;
use File::Basename;

chomp(my %defs = map { split /=/, $_, 2 } `../make-vdt --defs ../defs`);

my $dest_dir = "$defs{ROOT}/releases/$defs{VDT_VERSION}/osg";

if(!-e $dest_dir) {
    system("mkdir -p $dest_dir");
}

my $dir = dirname($0);
foreach my $ini (<$dir/osg/etc/*.ini>) {
    my $filename = basename($ini);
    my $destination = "$dest_dir/$filename";
    print "copying $filename to $destination\n";

    open(IN, '<', $ini) or die("Can't open $ini for reading: $!");
    my $contents = join("", <IN>);
    close(IN);

    # Put a header on the file
    my $timestamp = localtime(time);
    $contents = "; This file was copied from VDT version $defs{VDT_FULL_VERSION} on $timestamp\n" . 
        "; This file is intended as a reference, and should not be used by automated scripts.\n" .
        "; \n" .
        $contents;

    open(OUT, '>', $destination) or die("Can't open $destination for writing: $!");
    print OUT $contents;
    close(OUT);
}

