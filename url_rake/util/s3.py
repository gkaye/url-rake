import boto3, botocore
import json
import logging
import os

s3_client = boto3.client("s3")
s3_resource = boto3.resource("s3")


# Set up logger
LOGGING_LEVEL = os.environ["logging_level"]
LOGGER = logging.getLogger()
LOGGER.setLevel(LOGGING_LEVEL)


def get_json(bucket, key):
    """
    Gets a JSON object stored in S3.
    """

    try:
        object = s3_resource.Object(bucket, key)
        body = object.get()["Body"].read()
    except botocore.exceptions.ClientError as error:
        code = error.response["Error"]["Code"]

        # Don't fail if object doesn't exist, just return None
        if code == "NoSuchKey":
            LOGGER.info(f"File with key {key} in {bucket} doesn't exist.")
            return None
        else:
            raise RuntimeError(f"Error code {code} received when attempting to fetch {key} from {bucket}.") from error
    else:
        return json.loads(body)


def save_json(bucket, key, object):
    """
    Serializes the provided object to JSON, and stores it in S3.
    """

    s3_client.put_object(
         Body = str(json.dumps(object, indent=2)),
         Bucket = bucket,
         Key = key
    )


def create_bucket_if_not_exists(bucket_name):
    """
    If a bucket with the provided name doesn't exist, creates it.
    """

    bucket = s3_resource.Bucket(bucket_name)

    try:
        # Check if bucket exists
        s3_resource.meta.client.head_bucket(Bucket=bucket_name)
        LOGGER.info(f"Validated that bucket {bucket_name} exists.")
    except botocore.exceptions.ClientError as error:
        error_code = int(error.response["Error"]["Code"])

        # If bucket doesn't exist, create it
        if error_code == 404:
            LOGGER.info(f"Bucket {bucket_name} doesn't exist, creating now.")
            s3_resource.create_bucket(Bucket=bucket_name)
        # Something else went wrong, bucket doesn't exist and can't be created.  Raise error.
        else:
            print(f"error_code: {error_code}")
            raise RuntimeError(f"Error encountered while checking if bucket exists.") from error

