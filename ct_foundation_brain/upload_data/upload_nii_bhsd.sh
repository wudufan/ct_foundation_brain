#!/bin/bash

input_dir="AISD_2021_ncct_ischemic_stroke/dicoms"
project_id="fleet-space-445215-f7"
location="northamerica-northeast2"
dataset_id="brain_ct_stroke"
dicom_store_id="ct_foundation_stroke_dataset"

root_dir="/mnt/src_data"

python upload_dicom_data.py \
    --input_dir="${input_dir}" \
    --project_id="${project_id}" \
    --location="${location}" \
    --dataset_id="${dataset_id}" \
    --dicom_store_id="${dicom_store_id}" \
    &> "${root_dir}/${input_dir}/upload_dicom_aisd_20241230.log"
