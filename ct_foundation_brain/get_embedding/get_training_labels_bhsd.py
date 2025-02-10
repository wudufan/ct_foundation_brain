'''
Get the summarized labels for BHSD dataset
'''

# %%
import os
import argparse
import sys
import subprocess

import SimpleITK as sitk
import pandas as pd
import numpy as np

from ct_foundation_brain.locations import src_data_dir


# %%
def get_args(default_args=[]):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir')
    parser.add_argument('--output_filename')

    if 'ipykernel' in sys.argv[0]:
        args = parser.parse_args(default_args)
    else:
        args = parser.parse_args()

    args.git_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    args.datetime = subprocess.check_output(['date', '+%Y-%m-%d %H:%M:%S']).decode('ascii').strip()
    args.user = subprocess.check_output(['whoami']).decode('ascii').strip()
    args.sys_argv = sys.argv

    for k in vars(args):
        print(k, '=', getattr(args, k), flush=True)

    return args


# %%
def main(args):
    input_dir = os.path.join(src_data_dir, args.input_dir)
    output_filename = os.path.join(src_data_dir, args.output_filename)
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)

    filenames = os.listdir(input_dir)
    filenames = [f for f in filenames if f.endswith('.nii.gz')]

    manifest = []
    print('Found {} files'.format(len(filenames)), flush=True)
    for i, filename in enumerate(filenames):
        if (i + 1) % 10 == 0:
            print('Processing {}/{}'.format(i + 1, len(filenames)), flush=True)

        img = sitk.ReadImage(os.path.join(input_dir, filename))
        pixel_size = img.GetSpacing()
        img = sitk.GetArrayFromImage(img)

        labels, counts = np.unique(img, return_counts=True)

        # exclude background
        inds = np.where(labels != 0)
        labels = labels[inds]
        counts = counts[inds]

        row = {
            'filename': filename,
            'dx_cm': pixel_size[0] / 10,
            'dy_cm': pixel_size[1] / 10,
            'dz_cm': pixel_size[2] / 10
        }
        for label, count in zip(labels, counts):
            row['label_{}_count'.format(label)] = count
            row['label_{}_cm3'.format(label)] = count * np.prod(pixel_size) / 1000

        manifest.append(row)

    manifest = pd.DataFrame(manifest)
    manifest.to_csv(output_filename, index=False)

    return manifest


# %%
if __name__ == '__main__':
    args = get_args([
        '--input_dir', 'bhsd_2023_ct_herrmohage/label_192/ground truths',
        '--output_filename', 'bhsd_2023_ct_herrmohage/label_192/ground_truths.csv',
    ])

    res = main(args)
