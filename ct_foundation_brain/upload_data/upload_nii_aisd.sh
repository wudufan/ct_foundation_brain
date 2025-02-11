#!/bin/bash

input_dir="AISD_2021_ncct_ischemic_stroke/ct_nii"
output_dir="AISD/origin/"
project_id="fleet-space-445215-f7"
bucket_name="ct_hemorrhage"

root_dir="/mnt/src_data"

python upload_nii_data.py \
    --input_dir "${input_dir}" \
    --output_dir "${output_dir}" \
    --project_id "${project_id}" \
    --bucket_name "${bucket_name}" \
    &> "${root_dir}/${input_dir}/upload_nii_aisd_20250210.log"
