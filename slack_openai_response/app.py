import os
import json
import base64
import logging
import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from openai import OpenAI
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secrets_client = boto3.client('secretsmanager')


def get_secret(secret_name):
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response.get('SecretString') or base64.b64decode(response.get('SecretBinary')))
        return secret if secret else logger.error(f"No secret value found for {secret_name}")
    except ClientError as e:
        logger.error(f"Unable to retrieve secret {secret_name}: {str(e)}")
        raise e


slack_bot_token = get_secret(os.getenv('SLACK_BOT_TOKEN_SECRET_NAME'))['SLACK_BOT_TOKEN']
openai_api_key = get_secret(os.getenv('OPENAI_API_KEY_SECRET_NAME'))['OPENAI_API_KEY']

slack_client = WebClient(token=slack_bot_token)
bot_user_id = slack_client.auth_test()["user_id"]
client = OpenAI(api_key=openai_api_key)

responded_threads = {}


def lambda_handler(event, _):
    event_body = json.loads(event.get('body', '{}'))

    if 'challenge' in event_body:
        return {
            'statusCode': 200,
            'body': json.dumps({'challenge': event_body['challenge']}),
            'headers': {'Content-Type': 'application/json'}
        }

    try:
        slack_event = event_body.get('event', {})
        if slack_event.get('user') == bot_user_id or 'subtype' in slack_event:
            return {'statusCode': 200, 'body': 'Event ignored'}

        response_channel = slack_event.get('channel')
        thread_ts = slack_event.get('ts')

        if thread_ts in responded_threads:
            return {'statusCode': 200, 'body': 'Thread already responded to'}

        if 'text' in slack_event:
            text_content = slack_event['text']
            if "згенеруй зображення:" in text_content.lower():
                description = text_content.split("згенеруй зображення:", 1)[1].strip()
                image_url = openai_image_generation(description)
                if image_url:
                    post_image_to_slack(response_channel, image_url, thread_ts)
                    responded_threads[thread_ts] = True
                    return {'statusCode': 200, 'body': 'Image created and sent to Slack'}
                else:
                    return {'statusCode': 500, 'body': 'Failed to generate image'}
            else:
                openai_response = generate_openai_response(text_content)
                post_message_to_slack(response_channel, openai_response, thread_ts)
                responded_threads[thread_ts] = True
                return {'statusCode': 200, 'body': 'Text event processed'}

        else:
            return {'statusCode': 200, 'body': 'No content to process'}

    except Exception as e:
        logger.error(f"Error processing Slack event: {str(e)}")
        return {'statusCode': 500, 'body': f'Error processing event: {str(e)}'}


def openai_image_generation(description):
    try:
        response = client.images.generate(prompt=description,
                                          n=1,
                                          size="1024x1024",
                                          model="dall-e-3")
        image_url = response.data[0].url
        return image_url
    except Exception as e:
        logger.error(f"Failed to generate image with OpenAI: {str(e)}")
        return None


def post_image_to_slack(channel, image_url, thread_ts):
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            with open('/tmp/generated_image.png', 'wb') as f:
                f.write(response.content)

            response = slack_client.files_upload_v2(
                channels=channel,
                initial_comment='Ось згенероване зображення:',
                file='/tmp/generated_image.png',
                filename='generated_image.png',
                thread_ts=thread_ts
            )
            logger.info(f"Posted image to Slack: {response['file']['permalink']}")
        else:
            logger.error("Failed to download the image")
    except SlackApiError as e:
        logger.error(f"Slack API Error: {str(e)}")


def generate_openai_response(content):
    base_prompt = (
        "Уявіть, що ви AI-консультант з IT, який володіє дотепним гумором. "
        "Наче ти бородатий сисадмін, зроби коротенький, смішний, трошки душнуватий, IT-орієнтований коментар, "
        "використовуючи програмістські жарти, про: "
    )
    try:
        response = client.chat.completions.create(model="gpt-4o",
                                                  messages=[
                                                      {"role": "system", "content": base_prompt},
                                                      {"role": "user", "content": content}
                                                  ])
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Failed to interact with OpenAI: {str(e)}")
        return "Failed to generate response."


def post_message_to_slack(channel, message, thread_ts):
    try:
        slack_client.chat_postMessage(
            channel=channel,
            text=message,
            thread_ts=thread_ts
        )
    except SlackApiError as e:
        logger.error(f"Slack API Error: {str(e)}")
