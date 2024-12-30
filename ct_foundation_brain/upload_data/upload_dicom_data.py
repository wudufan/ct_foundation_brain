'''
Upload the dicom data to Google Cloud
'''

# %%
import os
import argparse
import sys
import subprocess

import google.auth
import glob
from google.auth.transport import requests

from ct_foundation_brain.locations import src_data_dir


# %%
def get_args(default_args=[]):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir')
    parser.add_argument(
        "--project_id",
        type=str,
        default="fleet-space-445215-f7",
        help="The project ID. Default is 'fleet-space-445215-f7'.",
    )
    parser.add_argument(
        "--location",
        type=str,
        default="northamerica-northeast2",
        help="The location of the DICOM store. Default is 'us-central1'.",
    )
    parser.add_argument(
        "--dataset_id",
        type=str,
        default="brain_ct_stroke",
        help="The dataset ID. Default is 'ct-foundation-brain'.",
    )
    parser.add_argument(
        "--dicom_store_id",
        type=str,
        default="ct_foundation_stroke_dataset",
        help="The DICOM store ID. Default is 'ct-foundation-brain'.",
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
def init_dicomweb_store(project_id, location, dataset_id, dicom_store_id):
    """Handles the POST requests specified in the DICOMweb standard.

    See https://github.com/GoogleCloudPlatform/python-docs-samples/tree/main/healthcare/api-client/v1/dicom
    before running the sample."""

    # Gets credentials from the environment. google.auth.default() returns credentials and the
    # associated project ID, but in this sample, the project ID is passed in manually.
    scoped_credentials, _ = google.auth.default(scopes=[
        "https://www.googleapis.com/auth/cloud-platform"
    ])

    # Creates a requests Session object with the credentials.
    session = requests.AuthorizedSession(scoped_credentials)

    # URL to the Cloud Healthcare API endpoint and version
    base_url = "https://healthcare.googleapis.com/v1"

    # TODO(developer): Uncomment these lines and replace with your values.
    # project_id = 'my-project'  # replace with your GCP project ID
    # location = 'us-central1'  # replace with the parent dataset's location
    # dataset_id = 'my-dataset'  # replace with the parent dataset's ID
    # dicom_store_id = 'my-dicom-store' # replace with the DICOM store ID
    # dcm_file = 'dicom000_0001.dcm'  # replace with a DICOM file
    url = f"{base_url}/projects/{project_id}/locations/{location}"

    dicomweb_path = "{}/datasets/{}/dicomStores/{}/dicomWeb/studies".format(
        url, dataset_id, dicom_store_id
    )

    return session, dicomweb_path


def dicomweb_store_instance(session, dicomweb_path, dcm_file):
    with open(dcm_file, "rb") as dcm:
        dcm_content = dcm.read()

    # Sets required "application/dicom" header on the request
    headers = {"Content-Type": "application/dicom"}

    response = session.post(dicomweb_path, data=dcm_content, headers=headers)
    try:
        response.raise_for_status()
    except Exception as e:
        print(f"Error storing DICOM instance: dicom_file={dcm_file}, error={e}")
        return
    # print("Stored DICOM instance:")
    # print(response.text)
    return response


# %%
def main(args):
    input_dir = os.path.join(src_data_dir, args.input_dir)
    dicom_dirs = glob.glob(os.path.join(input_dir, '*', 'CT'))

    print(f'Found {len(dicom_dirs)} dicom directories', flush=True)
    for i, dicom_dir in enumerate(dicom_dirs):
        if i % 10 == 0:
            print(f'Uploading dicom directory {i+1}/{len(dicom_dirs)}: {dicom_dir}', flush=True)
            session, dicomweb_path = init_dicomweb_store(
                args.project_id, args.location, args.dataset_id, args.dicom_store_id
            )

        dcm_files = glob.glob(os.path.join(dicom_dir, '*.dcm'))
        for dcm_file in dcm_files:
            dicomweb_store_instance(session, dicomweb_path, dcm_file)

    return dicom_dirs


# %%
if __name__ == '__main__':
    args = get_args([
        '--input_dir', 'AISD_2021_ncct_ischemic_stroke/dicoms',
    ])

    res = main(args)
