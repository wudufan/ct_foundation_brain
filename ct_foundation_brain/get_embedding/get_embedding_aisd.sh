#!/bin/bash

# This script is used to get the embedding of the AISD dataset

output_dir="aisd/embeddings"
project_id="fleet-space-445215-f7"
location="northamerica-northeast2"
dataset_id="brain_ct_stroke"
dicom_store_id="ct_foundation_stroke_dataset"
parallel_size="16"

root_dir="/mnt/data"

mkdir -p "${root_dir}/${output_dir}"

python get_embedding.py \
    --output_dir "${output_dir}" \
    --project_id "${project_id}" \
    --location "${location}" \
    --dataset_id "${dataset_id}" \
    --dicom_store_id "${dicom_store_id}" \
    --parallel_size "${parallel_size}" \
    &> "${root_dir}/${output_dir}/get_embedding_aisd_20241231.log"
