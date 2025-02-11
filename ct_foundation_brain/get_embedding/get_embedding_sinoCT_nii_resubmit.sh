#!/bin/bash

# This script is used to get the embedding of the AISD dataset

output_dir="sinoct/embeddings/healthy_500_origin"
bucket_dir="stanford_sinoCT/healthy_500_origin"
project_id="fleet-space-445215-f7"
bucket_name="ct_hemorrhage"
parallel_size="8"

root_dir="/mnt/data"

mkdir -p "${root_dir}/${output_dir}"

python get_embedding_sinoCT_nii_resubmit.py \
    --output_dir "${output_dir}" \
    --bucket_dir "${bucket_dir}" \
    --project_id "${project_id}" \
    --bucket_name "${bucket_name}" \
    --parallel_size "${parallel_size}" \
    &> "${root_dir}/${output_dir}/get_embedding_sinoCT_nii_resubmit_20250210.log"
