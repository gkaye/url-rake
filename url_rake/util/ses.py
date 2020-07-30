import boto3

ses = boto3.client('ses')


def send_email(from_email, to_email, subject, body):
    """
    Sends an email via AWS SES.
    """

    ses.send_email(
        Source = from_email,
        Destination={
            'ToAddresses': [
                to_email,
            ],
        },
        Message={
            'Subject': {
                'Data': subject
            },
            'Body': {
                'Text': {
                    'Data': body
                }
            }
        }
    )

