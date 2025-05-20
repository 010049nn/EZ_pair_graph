#Copyright (c) 2025. RIKEN All rights reserved.
#This is for academic and non-commercial research use only.
#The technology is currently under patent application.
#Commercial use is prohibited without a separate license agreement.
#E-mail: akihiro.ezoe@riken.jp

#!/usr/bin/perl
use strict;
use warnings;

sub calculate_stats {
    my @values = sort { $a <=> $b } @_;
    my $n = scalar @values;

    if( $n == 0 ){
	$n = 1;
    }
    
    my $sum = 0;
    $sum += $_ for @values;
    my $mean = $sum / $n;
    
    my $q1_idx = int($n / 4);
    my $q2_idx = int($n / 2);
    my $q3_idx = int(3 * $n / 4);
    
    my $q1 = $values[$q1_idx];
    my $q2 = $values[$q2_idx];
    my $q3 = $values[$q3_idx];
    
    return ($mean, $q1, $q2, $q3);
}

sub calculate_slope {
    my ($x1, $y1, $x2, $y2) = @_;
    return ($y2 - $y1) / ($x2 - $x1) if $x2 != $x1;
    return 0;
}


my $input_file = 'output_EZ/clustered_data.txt';
open my $fh, '<', $input_file or die "Cannot open file: $!";
my $header = <$fh>;
my @data;
while (my $line = <$fh>) {
    chomp $line;
    my @fields = split /\s+/, $line;
    push @data, \@fields;
}
close $fh;


my %groups;
foreach my $row (@data) {
    my ($x, $y, $cluster) = @$row;
    push @{$groups{$cluster}}, [$x, $y];
}


my %stats;
foreach my $cluster (keys %groups) {

    
    my @x_values = map { $_->[0] } @{$groups{$cluster}};
    my @y_values = map { $_->[1] } @{$groups{$cluster}};
    
    my ($x_mean, $x_q1, $x_q2, $x_q3) = calculate_stats(@x_values);
    my ($y_mean, $y_q1, $y_q2, $y_q3) = calculate_stats(@y_values);
    
    my @slopes;
    for my $i (0..$#{$groups{$cluster}}-1) {
        for my $j (($i+1)..$#{$groups{$cluster}}) {
            my $x1 = $groups{$cluster}[$i][0];
            my $y1 = $groups{$cluster}[$i][1];
            my $x2 = $groups{$cluster}[$j][0];
            my $y2 = $groups{$cluster}[$j][1];
            
            next if $x1 == $x2;
            
            my $slope = calculate_slope($x1, $y1, $x2, $y2);
            push @slopes, $slope;
        }
    }

    my ($slope_mean, $slope_q1, $slope_q2, $slope_q3) = calculate_stats(@slopes);
    my $slo = scalar @slopes;

    if ( $slo == 0 || $slo == 1 ){
	$slope_mean = $y_mean - $x_mean;
	$slope_q1 = $y_q1 - $x_q1;
	$slope_q2 = $y_q2 - $x_q2;
	$slope_q3 = $y_q3 - $x_q3;
    }

    my $m = @{$groups{$cluster}};
        
    $stats{$cluster} = {
        x => {
            mean => $x_mean,
            q1 => $x_q1,
            q2 => $x_q2,
            q3 => $x_q3,
	    n => $m
        },
        y => {
            mean => $y_mean,
            q1 => $y_q1,
            q2 => $y_q2,
            q3 => $y_q3,
	    n => $m
        },
        slope => {
            mean => $slope_mean,
            q1 => $slope_q1,
            q2 => $slope_q2,
            q3 => $slope_q3,
	    n => $m
        }
    };
    
    my $y_intercept = $y_mean - $slope_mean * $x_mean;
    my $calc_y_mean = $y_intercept + $slope_mean * $x_mean;
    my $calc_y_median = $y_intercept + $slope_mean * $x_q2;
    
    $stats{$cluster}{calculated} = {
        mean_point => [$x_mean, $calc_y_mean],
        median_point => [$x_q2, $calc_y_median],
	n => $m
    };
}

my $stats_file = 'output_EZ/group_statistics.txt';
open my $out_fh, '>', $stats_file or die "Cannot open file: $!";
foreach my $cluster (sort { $a <=> $b } keys %stats) {
    print $out_fh "Statistics for Group $cluster:\n";
    
    printf $out_fh "X: Mean=%.4f, Q1=%.4f, Q2=%.4f, Q3=%.4f\n",
        $stats{$cluster}{x}{mean},
        $stats{$cluster}{x}{q1},
        $stats{$cluster}{x}{q2},
        $stats{$cluster}{x}{q3};

    printf $out_fh "Y: Mean=%.4f, Q1=%.4f, Q2=%.4f, Q3=%.4f\n",
        $stats{$cluster}{y}{mean},
        $stats{$cluster}{y}{q1},
        $stats{$cluster}{y}{q2},
        $stats{$cluster}{y}{q3};
    
    printf $out_fh "Slope: Mean=%.4f, Q1=%.4f, Q2=%.4f, Q3=%.4f\n",
        $stats{$cluster}{slope}{mean},
        $stats{$cluster}{slope}{q1},
        $stats{$cluster}{slope}{q2},
        $stats{$cluster}{slope}{q3};
    
    print $out_fh "\n";
}
close $out_fh;

my $calc_file = 'output_EZ/calculated_points.txt';
open my $calc_fh, '>', $calc_file or die "Cannot open file: $!";
print $calc_fh "Group\tX_Mean\tY_Calculated_Mean\tX_Median\tY_Calculated_Median\tg_num\n";
foreach my $cluster (sort { $a <=> $b } keys %stats) {
    printf $calc_fh "%d\t%.4f\t%.4f\t%.4f\t%.4f\t%d\n",
        $cluster,
        $stats{$cluster}{calculated}{mean_point}[0],
        $stats{$cluster}{calculated}{mean_point}[1],
        $stats{$cluster}{calculated}{median_point}[0],
        $stats{$cluster}{calculated}{median_point}[1],
	$stats{$cluster}{calculated}{n};
}
close $calc_fh;


print "Input file: $input_file\n";
print "Output files: $stats_file, $calc_file\n";
