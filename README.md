# URL Rake
A serverless application that periodically searches a range of URLs for new content and alerts a user via e-mail.  Leverages AWS Lambda for computing, SES for e-mail notifications, and S3 for state persistance and post-deployment configurations.

## Configuring
### **Before deployment**, configure the below values found in /template.yaml.
##### *Modify `bucket`, `default_email_subject`, `default_from_email`, `default_to_email`, `default_url`, `default_start_value`, and `default_look_ahead` to meet your specific needs.*
#### Detailed explanations:
* **bucket**: The bucket used to store configuration and state.  This will be automatically created if it does not exist.  An existing bucket may be used, however the working AWS account must have read and write access to this bucket.
* **config_s3_key**: The AWS S3 key used to store the config.  The default will work for most use cases.
* **previously_valid_urls_s3_key**: The AWS S3 key used to store the previously known valid URLs.  The default will work for most use cases.
* **logging_level**: The desired log level. The default should be good for most use cases.
* **default_email_subject**: The default subject for e-mail alerts.  Customize to your liking.
* **default_from_email**: The e-mail address alert e-mails originate from.  This e-mail address must be registered with AWS SES to be used.
* **default_to_email**: The e-mail address to send alerts to.  This e-mail address must be registered with AWS SES to be used.
* **default_url**:  The url to 'rake'.  %s will be replaced with the indicated range of numbers below.
* **default_start_value**: The starting value (used to populate %s in default_url).
* **default_look_ahead**: The number of values to scan ahead.
* **default_slide_window**: If enabled, updates the start_value to the last known URLs value + 1.  Must be True or False.
* **ScheduleExpression**: A rate describing how often to search for new content.
NOTE: values above starting with 'default' can be changed after deployment by editing the 'config_s3' file in 'bucket'
## Deploying
Requirements:
* The [AWS SAM command line interface](https://aws.amazon.com/serverless/sam/)
* Docker (Required by AWS SAM CLI)

Run the following command to deploy:
`sam deploy --guided`
