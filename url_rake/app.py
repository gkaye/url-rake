import grequests
import requests
import json
from requests.adapters import HTTPAdapter

def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    start = 14831
    offset = 6
    end = start + offset

    urls = []
    for key in range(start, end + 1):
        urls.append(f'https://www.test.com/{key}')


    rs = (grequests.get(u) for u in urls)
    ret = grequests.map(rs)
    status_codes = [r.status_code for r in ret]

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Success!",
            "payload": status_codes,
        }),
    }

