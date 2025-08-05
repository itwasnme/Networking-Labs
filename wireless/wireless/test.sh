#!/bin/bash

# Set the range of values for the first variable (starting at 10, ending at 100, incrementing by 5)
for i in {10..100..5}
do
  # Execute the python command with the current value of i and capture the output
  output=$(python3 project.py $i 20 150 --mac YourMac | grep -e 'Took')

  # Print the output of the command
  echo "$output"
done

