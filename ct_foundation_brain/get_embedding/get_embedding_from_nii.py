'''
Calculate the embeddings using CT Foundation
'''

# %%
import os
import argparse
import sys
import subprocess

from google.cloud import storage
from concurrent.futures import ThreadPoolExecutor
import dataclasses
import functools
import json
from typing import Any, Tuple
import google.auth
import google.auth.transport.requests
import numpy as np

import pandas as pd

from ct_foundation_brain.locations import data_dir


# %%
def get_args(default_args=[]):
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_dir')
    parser.add_argument('--bucket_dir', help='Directory in the bucket')
    parser.add_argument('--project_id', default='fleet-space-445215-f7')
    parser.add_argument('--bucket_name', default='ct_hemorrhage')
    parser.add_argument('--parallel_size', type=int, default=16)

    if 'ipykernel' in sys.argv[0]:
        args = parser.parse_args(default_args)
    else:
        args = parser.parse_args()

    args.git_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()
    args.datetime = subprocess.check_output(['date']).decode('utf-8').strip()
    args.user = subprocess.check_output(['whoami']).decode('utf-8').strip()
    args.sys_argv = sys.argv

    for k in vars(args):
        print(f'{k} = {getattr(args, k)}', flush=True)

    return args


# %%
def get_nii_urls(project_id, bucket_name, input_dir):
    gcs_storage_client = storage.Client(project_id)
    gcs_bucket = gcs_storage_client.bucket(bucket_name)
    nifti_urls = []

    if not input_dir.endswith('/'):
        input_dir = input_dir + '/'

    for a in gcs_bucket.list_blobs(prefix=input_dir):
        if a.name.endswith('.gz'):
            nifti_urls.append(f'gs://{bucket_name}/' + a.name)

    return nifti_urls


# %%
@dataclasses.dataclass(eq=False, frozen=True)
class Response:
    """Response from a Vertex Endpoint."""

    status_code: int
    response_json: dict[str, Any] | None  # json_types.JSONObject


class Endpoint:
    """Calling utility for a Vertex Endpoint using default credentials."""

    def __init__(self):
        self._endpoint_url = (
            'https://us-central1-aiplatform.googleapis.com/v1/projects/'
            'hai-cd3-foundations/locations/us-central1/endpoints/300'
        )

    def predict(
        self,
        instances=list[Any],
        parameters: dict[str, Any] | None = None,
        credentials: google.auth.credentials.Credentials | None = None,
    ) -> Response:
        """Calls the Vertex Endpoint with the given instances and parameters."""
        if credentials is None:
            credentials = google.auth.default()[0]
        session = google.auth.transport.requests.AuthorizedSession(
            credentials=credentials
        )
        response = session.post(
            self._endpoint_url + ':predict',
            json=(
                {'instances': instances}
                | ({'parameters': parameters} if parameters is not None else {})
            ),
            headers={
                'Content-Type': 'application/json',
            },
            timeout=400,
        )
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            # Not expected, handling in case server incorrectly returns non-JSON.
            response_json = None
        return Response(
            status_code=response.status_code,
            response_json=response_json,
        )


def call_single_batch(
    caller: Endpoint, credentials, urls: list[str], access_token: str
) -> list[Tuple[np.ndarray | str, str]]:
    """Handles calls for a single batch and returns embeddings."""
    return_data = []
    if not credentials.valid:
        credentials.refresh(google.auth.transport.requests.Request())
    instances = [
        {'gcs_uri': a_url, 'bearer_token': f'{access_token}'} for a_url in urls
    ]
    returns = caller.predict(instances=instances)
    if returns.status_code != 200:
        for a_url in urls:
            return_data.append((f'FAIL STATUS {returns.status_code}', a_url))
        return return_data
    else:
        for i in range(len(returns.response_json['predictions'])):
            if returns.response_json['predictions'][i]['error_response']:
                return_data.append(
                    (returns.response_json['predictions'][i]['error_response'], urls[i])
                )
            else:
                embeddings = returns.response_json['predictions'][i][
                    'embedding_result'
                ]['embedding']
                return_data.append((embeddings, urls[i]))
        return return_data


def get_ct_embeddings(
    caller: Endpoint,
    credentials,
    urls: list[str],
    access_token: str,
    batch_size: int,
    parallel_size: int,
) -> list[Tuple[np.ndarray | str, str]]:
    """Handles calls and returns for parallel requests.

    Args:
        caller: CT foundation API caller.
        credentials: The credentials for the API.
        urls: List of urls to the NIfTI files in the cloud bucket. This must be of
        length batch_size * parallel_size.
        access_token: Access token for the DICOM store.
        batch_size: The number of volumes to pass in a batch (max 5).
        parallel_size: The number of parallel calls.

    Returns:
        Tuple list of embeddings | errors and the corresponding urls from which
        the embeddings were computed.
    """
    assert batch_size < 6, 'Batch size must be 5 or less.'
    assert (
        len(urls) == batch_size * parallel_size
    ), 'Error in batch, parallel sizes versus requests'

    # Setup up parallel batches
    p_urls = []
    for i in range(parallel_size):
        p_urls.append(urls[i * batch_size:(i + 1) * batch_size])

    # Check for correct sizing
    assert len(p_urls) == parallel_size, 'Error in batch, parallel dimensions'

    call_batch = functools.partial(call_single_batch, caller, credentials)

    # Launch parallel calls
    with ThreadPoolExecutor(max_workers=parallel_size) as executor:
        futures = [
            executor.submit(call_batch, b_urls, access_token) for b_urls in p_urls
        ]
        results = [f.result() for f in futures]
    # Unpack results into a single list
    return_results = []
    for b_result in results:
        for a_result in b_result:
            return_results.append(a_result)
    return return_results


# %%
def update_session(verbose=1):
    if verbose:
        print('Updating session...', flush=True)

    token = subprocess.check_output(
        ['gcloud', 'auth', 'application-default', 'print-access-token']
    ).decode('utf-8').strip('\n')
    credentials = google.auth.default()[0]

    if verbose:
        print('Session updated', flush=True)

    return credentials, token


# %%
def main(args):
    output_dir = os.path.join(data_dir, args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    cred, token = update_session()

    print('Retrieving all niis...', flush=True)
    nii_urls = get_nii_urls(args.project_id, args.bucket_name, args.bucket_dir)
    print('Found {} niis'.format(len(nii_urls)), flush=True)

    nii_urls = nii_urls[:10]

    df_embeddings = []
    print('Calculating embeddings...', flush=True)
    for i in range(0, len(nii_urls), args.parallel_size):
        batch_nii_urls = nii_urls[i:i + args.parallel_size]

        print('Processing images {} to {}'.format(i, i + args.parallel_size - 1), flush=True)
        cred, token = update_session()

        batch_embeddings = get_ct_embeddings(
            caller=Endpoint(),
            credentials=cred,
            urls=batch_nii_urls,
            access_token=token,
            batch_size=1,
            parallel_size=len(batch_nii_urls)
        )

        # retrieve the study and series uid
        for val in batch_embeddings:
            nii_path = val[1]
            filename = os.path.basename(nii_path)
            df_embeddings.append({
                'filename': filename,
                'embedding': val[0],
                'url': val[1]
            })

        df = pd.DataFrame(df_embeddings)
        df.to_csv(os.path.join(output_dir, 'embeddings.csv'), index=False)
    print('Embeddings calculated', flush=True)

    df_embeddings = pd.DataFrame(df_embeddings)
    df_embeddings.to_csv(os.path.join(output_dir, 'embeddings.csv'), index=False)

    # extract the successful embeddings and save to npz files
    df_embeddings = df_embeddings[
        df_embeddings['embedding'].apply(lambda x: len(x) > 100)
    ]
    print('There are {} successful embeddings'.format(len(df_embeddings)), flush=True)

    df_embeddings = df_embeddings.drop_duplicates(subset=['filename'])
    print('There are {} unique successful embeddings'.format(len(df_embeddings)), flush=True)

    np.savez(
        os.path.join(output_dir, 'embeddings.npz'),
        filename=df_embeddings['filename'].values,
        embedding=np.array(df_embeddings['embedding'].values.tolist())
    )

    print('Done', flush=True)

    return df_embeddings


# %%
if __name__ == '__main__':
    args = get_args([
        '--output_dir', 'bhsd/embeddings/origin',
        '--bucket_dir', 'BHSD/origin',
        '--parallel_size', '8',
    ])

    res = main(args)
