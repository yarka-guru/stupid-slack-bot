import os
import json
import base64
import logging
import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import openai
from openai import OpenAI
import boto3
from botocore.exceptions import ClientError
from config import config

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
stability_api_key = get_secret(os.getenv('STABILITY_API_KEY_SECRET_NAME'))['STABILITY_API_KEY']

slack_client = WebClient(token=slack_bot_token)
bot_user_id = slack_client.auth_test()["user_id"]
client = OpenAI(api_key=openai_api_key)

responded_threads = {}
stopped_threads = set()


def lambda_handler(event, _):
    logger.info("Received event: %s", json.dumps(event))

    event_body = json.loads(event.get('body', '{}'))

    if 'challenge' in event_body:
        logger.info("Responding to Slack challenge")
        return {
            'statusCode': 200,
            'body': json.dumps({'challenge': event_body['challenge']}),
            'headers': {'Content-Type': 'application/json'}
        }

    try:
        slack_event = event_body.get('event', {})
        logger.info("Processing Slack event: %s", json.dumps(slack_event))

        if slack_event.get('user') == bot_user_id:
            logger.info("Ignoring event from bot")
            return {'statusCode': 200, 'body': 'Event ignored'}

        response_channel = slack_event.get('channel')
        thread_ts = slack_event.get('ts')

        if thread_ts in stopped_threads:
            logger.info(f"Thread stopped: {thread_ts}")
            return {'statusCode': 200, 'body': 'Thread stopped'}

        if thread_ts in responded_threads:
            logger.info("Thread already responded to: %s", thread_ts)
            return {'statusCode': 200, 'body': 'Thread already responded to'}

        if slack_event.get('subtype') == 'file_share':
            logger.info("Processing file share event")
            user_content = slack_event.get('text', '')
            for file in slack_event.get('files', []):
                process_file(file, response_channel, thread_ts, user_content)
            responded_threads[thread_ts] = True
            return {'statusCode': 200, 'body': 'File event processed'}

        if 'text' in slack_event:
            text_content = slack_event['text'].lower()

            if config["stop_word"].lower() in text_content:
                stopped_threads.add(thread_ts)
                logger.info(f"Stop word detected, stopping thread: {thread_ts}")
                return {'statusCode': 200, 'body': 'Thread stopped due to stop word'}

            command = next((cmd for cmd in config["text_commands"].values() if cmd in text_content), None)
            if command:
                description = text_content.split(command, 1)[1].strip()
                if command == config["text_commands"]["generate_image"]:
                    image_url = openai_image_generation(description)
                    if image_url:
                        post_image_to_slack(response_channel, image_url, thread_ts,
                                            config["image_generation"]["initial_comment"])
                elif command == config["text_commands"]["generate_diffusion_image"]:
                    diffusion_image_url = generate_stability_image(description, stability_api_key,
                                                                   config["diffusion_image_generation"])
                    if diffusion_image_url:
                        post_image_to_slack(response_channel, diffusion_image_url, thread_ts,
                                            config["diffusion_image_generation"]["initial_comment"])
                responded_threads[thread_ts] = True
                return {'statusCode': 200, 'body': 'Command processed and responded to Slack'}
            else:
                openai_response = generate_openai_response(text_content)
                post_message_to_slack(response_channel, openai_response, thread_ts)
                responded_threads[thread_ts] = True
                return {'statusCode': 200, 'body': 'Text event processed'}
        else:
            logger.info("No content to process in the event")
            return {'statusCode': 200, 'body': 'No content to process'}

    except Exception as e:
        logger.error(f"Error processing Slack event: {str(e)}")
        return {'statusCode': 500, 'body': f'Error processing event: {str(e)}'}


def process_file(file, channel, thread_ts, user_content=""):
    try:
        file_url = file['url_private']
        headers = {'Authorization': f'Bearer {slack_bot_token}'}
        logger.info("Downloading file from: %s", file_url)
        response = requests.get(file_url, headers=headers)

        if response.status_code == 200:
            file_path = '/tmp/uploaded_file'
            with open(file_path, 'wb') as f:
                f.write(response.content)
            logger.info("File downloaded and saved: %s", file_path)
            logger.info("Processing file: %s", file_path)
            analyze_file(file_path, file['mimetype'], channel, thread_ts, user_content)
        else:
            logger.error(f"Failed to download the file: {file_url}")

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")


def analyze_file(file_path, mimetype, channel, thread_ts, user_content):
    try:
        if mimetype.startswith('image/'):
            analyze_image(file_path, channel, thread_ts, user_content)
        else:
            logger.info("Non-image file type detected: %s", mimetype)
            analyze_document(file_path, channel, thread_ts, mimetype, user_content)
    except Exception as e:
        logger.error(f"Error analyzing file: {str(e)}")


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_image(file_path, channel, thread_ts, user_content=None):
    user_content = user_content or config["image_analysis"]["analysis_prompt"]
    try:
        base64_image = encode_image(file_path)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}"
        }

        payload = {
            "model": config["image_analysis"]["model"],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_content
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": config["image_analysis"]["max_tokens"]
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        analysis_result = response.json()['choices'][0]['message']['content']
        post_message_to_slack(channel, f"Image analysis result: {analysis_result}", thread_ts)
    except Exception as e:
        logger.error(f"Failed to analyze image with OpenAI: {str(e)}")
        post_message_to_slack(channel, "Failed to analyze the image.", thread_ts)


def analyze_document(file_path, channel, thread_ts, mimetype, user_content):
    user_content = user_content or config["image_analysis"]["analysis_prompt"]
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        base64_file = base64.b64encode(file_bytes).decode('utf-8')
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}"
        }

        payload = {
            "model": config["image_analysis"]["model"],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_content
                        },
                        {
                            "type": "file",
                            "file": {
                                "file": f"data:{mimetype};base64,{base64_file}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": config["image_analysis"]["max_tokens"]
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        analysis_result = response.json()['choices'][0]['message']['content']
        post_message_to_slack(channel, f"Document analysis result: {analysis_result}", thread_ts)
    except Exception as e:
        logger.error(f"Failed to analyze document with OpenAI: {str(e)}")
        post_message_to_slack(channel, "Failed to analyze the document.", thread_ts)


def openai_image_generation(description):
    try:
        response = client.images.generate(prompt=description,
                                          n=1,
                                          size=config["image_generation"]["size"],
                                          model=config["image_generation"]["model"])
        image_url = response.data[0].url
        return image_url
    except openai.BadRequestError as e:
        logger.error(f"Error 400: {e}")
    except openai.AuthenticationError as e:
        logger.error(f"Error 401: {e}")
    except openai.PermissionDeniedError as e:
        logger.error(f"Error 403: {e}")
    except openai.NotFoundError as e:
        logger.error(f"Error 404: {e}")
    except openai.UnprocessableEntityError as e:
        logger.error(f"Error 422: {e}")
    except openai.RateLimitError as e:
        logger.error(f"Error 429: {e}")
    except openai.InternalServerError as e:
        logger.error(f"Error >=500: {e}")
    except openai.APIConnectionError as e:
        logger.error(f"API connection error: {e}")
    except openai.OpenAIError as e:
        logger.error(f"Failed to generate image with OpenAI: {str(e)}")
    return None


def generate_stability_image(description, api_key, generation_config):
    try:
        response = requests.post(
            generation_config["endpoint"],
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "image/*"
            },
            files={"none": ''},
            data={
                "prompt": description,
                "output_format": generation_config["output_format"]
            }
        )
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to generate image with Stability AI: {str(e)}")
        return None


def post_image_to_slack(channel, image_url, thread_ts, initial_comment):
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            image_data = response.content
            with open('/tmp/generated_image.png', 'wb') as f:
                f.write(image_data)

            response = slack_client.files_upload_v2(
                channel=channel,
                initial_comment=initial_comment,
                file='/tmp/generated_image.png',
                filename='generated_image.png',
                thread_ts=thread_ts
            )
            logger.info(f"Posted image to Slack: {response['file']['permalink']}")
        else:
            logger.error(f"Failed to download the image from URL: {image_url}")
    except SlackApiError as e:
        logger.error(f"Slack API Error: {str(e)}")


def generate_openai_response(content):
    base_prompt = config["base_prompt"]
    try:
        response = client.chat.completions.create(model=config["image_analysis"]["model"],
                                                  messages=[
                                                      {"role": "system", "content": base_prompt},
                                                      {"role": "user", "content": content}
                                                  ])
        return response.choices[0].message.content.strip()
    except openai.BadRequestError as e:
        logger.error(f"Error 400: {e}")
    except openai.AuthenticationError as e:
        logger.error(f"Error 401: {e}")
    except openai.PermissionDeniedError as e:
        logger.error(f"Error 403: {e}")
    except openai.NotFoundError as e:
        logger.error(f"Error 404: {e}")
    except openai.UnprocessableEntityError as e:
        logger.error(f"Error 422: {e}")
    except openai.RateLimitError as e:
        logger.error(f"Error 429: {e}")
    except openai.InternalServerError as e:
        logger.error(f"Error >=500: {e}")
    except openai.APIConnectionError as e:
        logger.error(f"API connection error: {e}")
    except openai.OpenAIError as e:
        logger.error(f"Failed to generate response with OpenAI: {str(e)}")
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
