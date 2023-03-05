import time
import logging

from pathlib import Path
import shutil
from google.cloud import storage
import os

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"
    # The path to your file to upload
    # source_file_name = "local/path/to/file"
    # The ID of your GCS object
    # destination_blob_name = "storage-object-name"
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "keys/wired-analogy-379505-261371efaf56.json"
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Optional: set a generation-match precondition to avoid potential race conditions
    # and data corruptions. The request to upload is aborted if the object's
    # generation number does not match your precondition. For a destination
    # object that does not yet exist, set the if_generation_match precondition to 0.
    # If the destination object already exists in your bucket, set instead a
    # generation-match precondition using its generation number.
    generation_match_precondition = 0

    blob.upload_from_filename(source_file_name, if_generation_match=generation_match_precondition)

    print(
        f"File {source_file_name} uploaded to {destination_blob_name}."
    )


src_path = r"chatlogs.txt"
timestamp = str(time.time()).split(".")[0]
dst_path = f"old-logs/chatlogs_{timestamp}.txt"
path = Path(src_path)
logging.info(path.is_file())
if path.is_file():
    logging.info(f"File found: {src_path}")
    shutil.move(src_path, dst_path)

    upload_blob("conversational-ai-avatars", dst_path, f"chat-logs/no-account/chatlogs_{timestamp}.txt")