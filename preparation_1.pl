#Copyright (c) 2025. RIKEN All rights reserved.
#This is for academic and non-commercial research use only.
#The technology is currently under patent application.
#Commercial use is prohibited without a separate license agreement.
#E-mail: akihiro.ezoe@riken.jp

#!/usr/bin/perl
use strict;
use warnings;
use List::Util qw(min max);

my $input_file = $ARGV[0];
system("mkdir output_EZ");
my $output_file = "output_EZ/clustered_data.txt";

my $max_k = $ARGV[1];

open(my $in_fh, '<', $input_file) or die "Cannot open $input_file: $!";
my @data;
while (my $line = <$in_fh>) {
    chomp $line;
    my ($x, $y) = split /\s+/, $line;
    push @data, [$x, $y];
}
close($in_fh);

my @pos_diff;
my @neg_diff;
foreach my $pair (@data) {
    my ($x, $y) = @$pair;
    my $diff = $y - $x;
    if ($diff > 0) {
        push @pos_diff, $pair;
    } elsif ($diff < 0) {
        push @neg_diff, $pair;
    } else {
        push @pos_diff, $pair;
    }
}

sub euclidean_distance {
    my ($p1, $p2) = @_;
    return sqrt(($p1->[0] - $p2->[0])**2 + ($p1->[1] - $p2->[1])**2);
}

sub kmeans_clustering {
    my ($data_ref, $k) = @_;
    my @data_array = @$data_ref;
    my $n = scalar @data_array;
    
    $k = min($k, $n);
    
    my @centroids;
    for (my $i = 0; $i < $k; $i++) {
        push @centroids, [$data_array[$i]->[0], $data_array[$i]->[1]];
    }
    
    my @assignments;
    my $changed = 1;
    my $max_iterations = 100;
    
    for (my $iter = 0; $iter < $max_iterations && $changed; $iter++) {
        $changed = 0;
        
        my @new_assignments;
        for (my $i = 0; $i < $n; $i++) {
            my $min_dist = 1e10;
            my $nearest = 0;
            
            for (my $j = 0; $j < $k; $j++) {
                my $dist = euclidean_distance($data_array[$i], $centroids[$j]);
                if ($dist < $min_dist) {
                    $min_dist = $dist;
                    $nearest = $j;
                }
            }
            
            push @new_assignments, $nearest;
            
            if (!defined $assignments[$i] || $assignments[$i] != $nearest) {
                $changed = 1;
            }
        }
        
        @assignments = @new_assignments;
        
        for (my $j = 0; $j < $k; $j++) {
            my $sum_x = 0, my $sum_y = 0;
            my $count = 0;
            
            for (my $i = 0; $i < $n; $i++) {
                if ($assignments[$i] == $j) {
                    $sum_x += $data_array[$i]->[0];
                    $sum_y += $data_array[$i]->[1];
                    $count++;
                }
            }
            
            if ($count > 0) {
                $centroids[$j] = [$sum_x / $count, $sum_y / $count];
            }
        }
    }
    
    my $wss = 0;
    for (my $i = 0; $i < $n; $i++) {
        my $cluster_id = $assignments[$i];
        my $dist = euclidean_distance($data_array[$i], $centroids[$cluster_id]);
        $wss += $dist**2;
    }
    
    my @clustered_data;
    for (my $i = 0; $i < $n; $i++) {
        push @clustered_data, [$data_array[$i]->[0], $data_array[$i]->[1], $assignments[$i]];
    }
    
    return {
        clustered_data => \@clustered_data,
        wss => $wss
    };
}

sub find_optimal_k {
    my ($data_ref, $max_k) = @_;
    my @data_array = @$data_ref;
    my $n = scalar @data_array;
    
    $max_k = min($max_k, $n);
    
    if ($n <= 3) {
        return 1;
    }
    
    my @wss;
    for (my $k = 1; $k <= $max_k; $k++) {
        my $result = kmeans_clustering($data_ref, $k);
        push @wss, $result->{wss};
    }
    
    my @angles;
    for (my $i = 1; $i < @wss - 1; $i++) {
        my $angle1 = atan2($wss[$i-1] - $wss[$i], 1);
        my $angle2 = atan2($wss[$i] - $wss[$i+1], 1);
        push @angles, abs($angle1 - $angle2);
    }
    
    my $max_angle = 0;
    my $optimal_k = 2;
    for (my $i = 0; $i < @angles; $i++) {
        if ($angles[$i] > $max_angle) {
            $max_angle = $angles[$i];
            $optimal_k = $i + 2;
	}
    }
    
    return $optimal_k;
}

my @all_clustered;

if (@pos_diff > 0) {
    my $pos_k = find_optimal_k(\@pos_diff, $max_k);
    my $pos_result = kmeans_clustering(\@pos_diff, $pos_k);
    push @all_clustered, @{$pos_result->{clustered_data}};
    print "Positive group:$pos_k\n";
}

my $pos_max_cluster = -1;
foreach my $cluster (@all_clustered) {
    $pos_max_cluster = max($pos_max_cluster, $cluster->[2]);
}

if (@neg_diff > 0) {
    my $neg_k = find_optimal_k(\@neg_diff, $max_k);
    my $neg_result = kmeans_clustering(\@neg_diff, $neg_k);
    foreach my $cluster (@{$neg_result->{clustered_data}}) {
        push @all_clustered, [$cluster->[0], $cluster->[1], $cluster->[2] + $pos_max_cluster + 1];
    }
    print "Negative groups: $neg_k\n";
}

open(my $out_fh, '>', $output_file) or die "Cannot open $output_file: $!";
print $out_fh "X Y Cluster\n";
foreach my $cluster (@all_clustered) {
    print $out_fh "$cluster->[0] $cluster->[1] $cluster->[2]\n";
}
close($out_fh);

print "Results were detailed in $output_file\n";
