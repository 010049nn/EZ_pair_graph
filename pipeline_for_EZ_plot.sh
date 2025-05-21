#!/bin/bash

# Stop execution if any command fails
set -e

# Define input file
INPUT_FILE="test_dataset.txt"

# Step 1: Run the first Perl preparation script
echo "Step 1: Running preparation_1.pl with $INPUT_FILE..."
perl preparation_1.pl "$INPUT_FILE" 8
# Expected output: clustered_data.txt

# Step 2: Run the second Perl preparation script
echo "Step 2: Running preparation_2.pl..."
perl preparation_2.pl
# Expected output: calculated_points.txt

# Step 3: Run Python visualization scripts
echo "Step 3: Running Python visualization scripts..."
echo "  3a: Running clustered_line_plot.py..."
python clustered_line_plot.py

echo "  3b: Running parallel_arrow_plot.py..."
python parallel_arrow_plot.py

echo "  3c: Running para_and_nonPara_plot.py with $INPUT_FILE..."
python para_and_nonPara_plot.py "$INPUT_FILE"

echo "Pipeline execution completed successfully"
