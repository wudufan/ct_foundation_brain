#!/bin/bash

input_dir="bhsd_2023_ct_herrmohage/label_192/ground truths"
output_filename="bhsd_2023_ct_herrmohage/label_192/ground_truths.csv"

root_dir="/mnt/src_data"

python get_training_labels_bhsd.py \
    --input_dir "${input_dir}" \
    --output_filename "${output_filename}" \
    &> "${root_dir}/${output_filename}.log"