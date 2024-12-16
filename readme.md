# CT Foundation Brain

Test the CT foundation model for brain CT and QA purposes

## Google Cloud sign-in
To connect to the google dicom storage and CT Foundation API, one must sign in to the google account using command line.

First run `gcloud init` when the container starts, skip sign in when asked. 

Then run `gcloud auth application-default login` and follow the prompt to sign in.

To verify the signing in, run `gcloud beta auth application-default print-access-token` and the console should return an access token. 

## Demos

- `load_lidc_embeddings`: test access to the stored embeddings precomputed for the LIDC datasets on Google Cloud.
- `load_dicom_from_google_storage`: test access to the stored dicom data shared by google