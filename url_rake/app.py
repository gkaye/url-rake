import json
import logging
import os

from util.async_http import fetch_status, get_responses
from util.s3 import get_json, save_json, create_bucket_if_not_exists 
from util.ses import send_email


# Gather environment variables passed in from CFT
BUCKET = os.environ["bucket"]
CONFIG_S3_KEY = os.environ["config_s3_key"]
PREVIOUSLY_VALID_URLS_S3_KEY = os.environ["previously_valid_urls_s3_key"]
LOGGING_LEVEL = os.environ["logging_level"]
DEFAULT_EMAIL_SUBJECT = os.environ["default_email_subject"]
DEFAULT_FROM_EMAIL = os.environ["default_from_email"]
DEFAULT_TO_EMAIL = os.environ["default_to_email"]
DEFAULT_URL = os.environ["default_url"]
DEFAULT_START_VALUE = int(os.environ["default_start_value"])
DEFAULT_LOOK_AHEAD = int(os.environ["default_look_ahead"])
DEFAULT_SLIDE_WINDOW = "true" == os.environ["default_slide_window"].lower()


# Set up logger
LOGGER = logging.getLogger()
LOGGER.setLevel(LOGGING_LEVEL)


def lambda_handler(event, context):
    """
    Entry point from AWS invocation.
    """

    LOGGER.debug("Lambda invoked")
    log_environment_variables()


    # 1) Initialize
    # Setup required AWS infrastructure
    create_infrastructure()

    # If configuration exists, retrieve from S3 - otherwise create a new one
    config = get_config()
    LOGGER.info(f"config loaded: {config}")

    # If previously_valid_urls exists, retrieve from S3, otherwise create a blank one
    previously_valid_urls = get_previously_valid_urls()
    LOGGER.info(f"previously_valid_urls loaded: {list(previously_valid_urls)}")


    # 2) Retrieve URL data
    # Generate URLs
    end_value_inclusive = config["start_value"] + config["look_ahead"] + 1
    requests = [{"url": config["url"] % value, "value": value} for value in
                    range(config["start_value"], end_value_inclusive)]
    LOGGER.info(f"Requesting values in range {config['start_value']} -> {end_value_inclusive} (inclusive)")
    LOGGER.info(f"First URL to request: {requests[0]['url'] if requests else 'None'}")
    LOGGER.info(f"Last URL to request:  {requests[-1]['url'] if requests else 'None'}")

    # Get all responses
    responses = get_responses(requests)

    # Create a list of requests that responded with status code 200
    valid_urls = [{"url": response["url"], "value": response["value"]} for response in responses
                    if response["response"].status == 200]


    # 3) Process URL data
    # Check valid_urls against previously_valid_urls and add to new_valid_urls
    new_valid_urls = []
    for valid_url in valid_urls:
        if valid_url["url"] not in previously_valid_urls:
            LOGGER.debug(f"New valid URL found: {valid_url['url']}")
            new_valid_urls.append(valid_url)


    # 4) Send alerts based upon processed URL data
    # Send emails for new_valid_urls
    if new_valid_urls:
        LOGGER.info("New URLs found, sending email.")
        send_email(config["from_email"], config["to_email"], config["email_subject"],
                    generate_email_body(new_valid_urls))

        # Once emails have sent (and threw no exception), update start_value if slide_window is True
        if config["slide_window"]:
            greatest_valid_value = new_valid_urls[-1]['value']

            new_start_value = greatest_valid_value + 1
            LOGGER.info(f"Updating start value from {config['start_value']} to {new_start_value}")
            config["start_value"] = new_start_value


    # 5) Save state
    # Save previously_valid_urls as list of just URL strings, no metadata is needed
    save_previously_valid_urls([valid_url["url"] for valid_url in valid_urls])

    save_config(config)


    return {
        "statusCode": 200,
        "body": json.dumps({
            "all_valid_urls": valid_urls,
            "new_valid_urls": new_valid_urls,
        }),
    }


def log_environment_variables():
    """
    Logs relevant values provided via environment variables.
    """

    LOGGER.info(f"bucket:                        {BUCKET}")
    LOGGER.info(f"config_s3_key:                 {CONFIG_S3_KEY}")
    LOGGER.info(f"previously_valid_urls_s3_key:  {PREVIOUSLY_VALID_URLS_S3_KEY}")
    LOGGER.info(f"logging_level:                 {LOGGING_LEVEL}")
    LOGGER.info(f"default_email_subject:         {DEFAULT_EMAIL_SUBJECT}")
    LOGGER.info(f"default_from_email:            {DEFAULT_FROM_EMAIL}")
    LOGGER.info(f"default_to_email:              {DEFAULT_TO_EMAIL}")
    LOGGER.info(f"default_url:                   {DEFAULT_URL}")
    LOGGER.info(f"default_start_value:           {DEFAULT_START_VALUE}")
    LOGGER.info(f"default_look_ahead:            {DEFAULT_LOOK_AHEAD}")
    LOGGER.info(f"default_slide_window:          {DEFAULT_SLIDE_WINDOW}")


def create_infrastructure():
    """
    Creates required AWS infrastructure.
    """

    create_bucket_if_not_exists(BUCKET)


def get_previously_valid_urls():
    """
    Returns previously_valid_urls saved in S3.
    """

    previously_valid_urls = get_json(BUCKET, PREVIOUSLY_VALID_URLS_S3_KEY)

    # If previously_valid_urls does not currently exist, create a new one and save to S3
    if not previously_valid_urls:
        previously_valid_urls = []
        save_previously_valid_urls(previously_valid_urls)

    return set(previously_valid_urls)


def save_previously_valid_urls(previously_valid_urls):
    """
    Saves previously_valid_urls to S3.
    """

    LOGGER.info(f"Writing previously_valid_urls to bucket {BUCKET} with key {PREVIOUSLY_VALID_URLS_S3_KEY}.") 
    save_json(BUCKET, PREVIOUSLY_VALID_URLS_S3_KEY, previously_valid_urls)


def get_config():
    """
    Returns config saved in S3.
    """

    # Retrieve config from S3
    config = get_json(BUCKET, CONFIG_S3_KEY)

    # If config does not currently exist, create a default one and save to S3
    if not config:
        config = generate_config()
        save_config(config)

    return config


def save_config(config):
    """
    Saves config to S3.
    """

    LOGGER.info(f"Writing config to bucket {BUCKET} with key {CONFIG_S3_KEY}.") 
    save_json(BUCKET, CONFIG_S3_KEY, config)


def generate_config():
    """
    Generates and returns an initial config from the provided defaults.
    """

    return {
                "email_subject": DEFAULT_EMAIL_SUBJECT,
                "from_email": DEFAULT_FROM_EMAIL,
                "to_email": DEFAULT_TO_EMAIL,
                "url": DEFAULT_URL,
                "start_value": DEFAULT_START_VALUE,
                "look_ahead": DEFAULT_LOOK_AHEAD,
                "slide_window": DEFAULT_SLIDE_WINDOW,
           }


def generate_email_body(urls):
    """
    Generates and returns an email body given a list of urls.
    """

    return "New URLs:\n" + "\n".join(f" • {url['url']}" for url in urls)

