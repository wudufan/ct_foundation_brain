'''
Upload the nii data to Google Cloud Bucket
'''

# %%
import os
import argparse
import sys
import subprocess

from google.cloud.storage import Client, transfer_manager

from ct_foundation_brain.locations import src_data_dir


# %%
def get_args(default_args=[]):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir')
    parser.add_argument('--output_dir', help='The output directory in bucket')
    parser.add_argument(
        "--project_id",
        type=str,
        default="fleet-space-445215-f7",
        help="The project ID. Default is 'fleet-space-445215-f7'.",
    )
    parser.add_argument(
        "--bucket_name",
        type=str,
        default="ct_hemorrhage",
        help="The bucket name. Default is 'ct_hemorrhage'.",
    )

    if 'ipykernel' in sys.argv[0]:
        args = parser.parse_args(default_args)
    else:
        args = parser.parse_args()

    args.git_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip().decode('utf-8')
    args.datetime = subprocess.check_output(['date']).strip().decode('utf-8')
    args.user = subprocess.check_output(['whoami']).strip().decode('utf-8')
    args.sys_argv = ' '.join(sys.argv)

    for k in vars(args):
        print(f'{k} = {getattr(args, k)}', flush=True)

    return args


# %%
def upload_many_blobs_with_transfer_manager(
    project_id, bucket_name, filenames, src_folder, dst_prefix, workers=8
):
    """Upload every file in a list to a bucket, concurrently in a process pool.

    Each blob name is derived from the filename, not including the
    `source_directory` parameter. For complete control of the blob name for each
    file (and other aspects of individual blob metadata), use
    transfer_manager.upload_many() instead.
    """

    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # A list (or other iterable) of filenames to upload.
    # filenames = ["file_1.txt", "file_2.txt"]

    # The directory on your computer that is the root of all of the files in the
    # list of filenames. This string is prepended (with os.path.join()) to each
    # filename to get the full path to the file. Relative paths and absolute
    # paths are both accepted. This string is not included in the name of the
    # uploaded blob; it is only used to find the source files. An empty string
    # means "the current working directory". Note that this parameter allows
    # directory traversal (e.g. "/", "../") and is not intended for unsanitized
    # end user input.
    # source_directory=""

    # The maximum number of processes to use for the operation. The performance
    # impact of this value depends on the use case, but smaller files usually
    # benefit from a higher number of processes. Each additional process occupies
    # some CPU and memory resources until finished. Threads can be used instead
    # of processes by passing `worker_type=transfer_manager.THREAD`.
    # workers=8

    storage_client = Client(project_id)
    bucket = storage_client.bucket(bucket_name)

    results = transfer_manager.upload_many_from_filenames(
        bucket,
        filenames,
        source_directory=src_folder,
        blob_name_prefix=dst_prefix,
        max_workers=workers
    )

    for name, result in zip(filenames, results):
        # The results list is either `None` or an exception for each filename in
        # the input list, in order.

        if isinstance(result, Exception):
            print("Failed to upload {} due to exception: {}".format(name, result))
        else:
            print("Uploaded {} to {}.".format(name, bucket.name))

    return results


# %%
def main(args):
    input_dir = os.path.join(src_data_dir, args.input_dir)
    output_dir = args.output_dir
    if not output_dir.endswith('/'):
        output_dir += '/'

    filenames = os.listdir(input_dir)
    filenames = [f for f in filenames if f.endswith('.nii.gz')]

    print('Found {} nii files'.format(len(filenames)))

    batchsize = 8
    results = []
    for i in range(0, len(filenames), batchsize):
        print(f'Uploading files {i} to {i+batchsize}...', flush=True)
        results += upload_many_blobs_with_transfer_manager(
            args.project_id,
            args.bucket_name,
            filenames[i:i + batchsize],
            input_dir,
            output_dir,
            workers=batchsize
        )

    print('Done uploading')

    return filenames, results


# %%
if __name__ == '__main__':
    args = get_args([
        '--input_dir', 'bhsd_2023_ct_herrmohage/label_192/images',
        '--output_dir', 'BHSD/origin/'
    ])

    res = main(args)
