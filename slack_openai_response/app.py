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
from config import config

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secrets_client = boto3.client('secretsmanager')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.getenv('DYNAMODB_TABLE_NAME'))


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
openai_client = OpenAI(api_key=openai_api_key)


def lambda_handler(event, _):
    logger.info("Received event: %s", json.dumps(event))

    event_body = json.loads(event.get('body', '{}'))

    if 'challenge' in event_body:
        return respond_to_challenge(event_body['challenge'])

    try:
        slack_event = event_body.get('event', {})
        logger.info("Processing Slack event: %s", json.dumps(slack_event))

        if slack_event.get('user') == bot_user_id:
            return {'statusCode': 200, 'body': 'Event ignored'}

        response_channel = slack_event.get('channel')
        thread_ts = slack_event.get('thread_ts') or slack_event.get('ts')
        event_ts = slack_event.get('ts')

        if is_message_responded(thread_ts, event_ts):
            logger.info(f"Message already responded to: {event_ts}")
            return {'statusCode': 200, 'body': 'Message already responded to'}

        thread_messages = get_thread_messages(response_channel, thread_ts)
        if contains_stop_word(thread_messages):
            logger.info("Stop word detected in thread: %s", thread_ts)
            return {'statusCode': 200, 'body': 'Stop word detected, no response'}

        if slack_event.get('subtype') == 'file_share':
            handle_file_share_event(slack_event, response_channel, thread_ts)
        elif 'text' in slack_event:
            handle_text_event(slack_event, response_channel, thread_ts, thread_messages)
        else:
            logger.info("No content to process in the event")
            return {'statusCode': 200, 'body': 'No content to process'}

        update_last_responded_message_ts(thread_ts, event_ts)

    except Exception as e:
        logger.error(f"Error processing Slack event: {str(e)}")
        return {'statusCode': 500, 'body': f'Error processing event: {str(e)}'}


def is_message_responded(thread_ts, event_ts):
    try:
        response = table.get_item(Key={'thread_ts': thread_ts})
        if 'Item' in response and response['Item']['last_responded_ts'] == event_ts:
            return True
    except ClientError as e:
        logger.error(f"DynamoDB error: {str(e)}")
    return False


def update_last_responded_message_ts(thread_ts, event_ts):
    try:
        table.put_item(Item={'thread_ts': thread_ts, 'last_responded_ts': event_ts})
    except ClientError as e:
        logger.error(f"Unable to update DynamoDB: {str(e)}")


def respond_to_challenge(challenge):
    return {
        'statusCode': 200,
        'body': json.dumps({'challenge': challenge}),
        'headers': {'Content-Type': 'application/json'}
    }


def get_thread_messages(channel, thread_ts):
    try:
        response = slack_client.conversations_replies(channel=channel, ts=thread_ts)
        return response.get('messages', [])
    except SlackApiError as e:
        logger.error(f"Error fetching thread messages: {str(e)}")
        return []


def contains_stop_word(messages):
    return any(config["stop_word"] in message.get('text', '').lower() for message in messages)


def handle_file_share_event(slack_event, response_channel, thread_ts):
    logger.info("Processing file share event")
    user_content = slack_event.get('text', '')
    for file in slack_event.get('files', []):
        process_file(file, response_channel, thread_ts, user_content)


def handle_text_event(slack_event, response_channel, thread_ts, thread_messages):
    text_content = slack_event['text'].lower()
    command = next((cmd for cmd in config["text_commands"].values() if cmd in text_content), None)
    if command:
        process_command(command, text_content, response_channel, thread_ts, thread_messages)
    else:
        openai_response = generate_openai_response(text_content, thread_messages)
        post_message_to_slack(response_channel, openai_response, thread_ts)


def process_command(command, text_content, response_channel, thread_ts, thread_messages):
    description = text_content.split(command, 1)[1].strip()
    if command == config["text_commands"]["generate_image"]:
        image_data = openai_image_generation(description)
        if image_data:
            post_image_file_to_slack(response_channel, image_data, thread_ts,
                                     config["image_generation"]["initial_comment"])
    elif command == config["text_commands"]["generate_diffusion_image"]:
        diffusion_image_data = generate_stability_image(description)
        if diffusion_image_data:
            post_image_file_to_slack(response_channel, diffusion_image_data, thread_ts,
                                     config["diffusion_image_generation"]["initial_comment"])


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
            analyze_file(file_path, file['mimetype'], channel, thread_ts, user_content)
        else:
            logger.error(f"Failed to download the file: {file_url}")

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")


def analyze_file(file_path, mimetype, channel, thread_ts, user_content):
    if mimetype.startswith('image/'):
        analyze_image(file_path, channel, thread_ts, user_content)
    else:
        analyze_document(file_path, channel, thread_ts, mimetype, user_content)


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
                {"role": "user", "content": [
                    {"type": "text", "text": user_content},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ],
            "max_tokens": config["image_analysis"]["max_tokens"]
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        analysis_result = response.json()['choices'][0]['message']['content']
        post_message_to_slack(channel, analysis_result, thread_ts)
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
                {"role": "user", "content": [
                    {"type": "text", "text": user_content},
                    {"type": "file", "file": {"file": f"data:{mimetype};base64,{base64_file}"}}
                ]}
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
        response = openai_client.images.generate(prompt=description,
                                                 n=config["image_generation"]["n"],
                                                 size=config["image_generation"]["size"],
                                                 model=config["image_generation"]["model"])
        image_url = response.data[0].url
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        return image_response.content
    except Exception as e:
        logger.error(f"Failed to generate image with OpenAI: {str(e)}")
        return None


def generate_stability_image(description):
    try:
        response = requests.post(
            config["diffusion_image_generation"]["endpoint"],
            headers={
                "Authorization": f"Bearer {stability_api_key}",
                "Accept": "image/*"
            },
            files={"none": ''},
            data={
                "prompt": description,
                "aspect_ratio": config["diffusion_image_generation"].get("aspect_ratio", "1:1"),
                "mode": config["diffusion_image_generation"].get("mode", "text-to-image"),
                "model": config["diffusion_image_generation"].get("model", "sd3-turbo"),
                "output_format": config["diffusion_image_generation"].get("output_format", "jpeg")
            }
        )
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to generate image with Stability AI: {str(e)}")
        return None


def post_image_file_to_slack(channel, image_data, thread_ts, initial_comment):
    try:
        file_path = '/tmp/generated_image.png'
        with open(file_path, 'wb') as f:
            f.write(image_data)

        response = slack_client.files_upload_v2(
            channel=channel,
            initial_comment=initial_comment,
            file=file_path,
            filename='generated_image.png',
            thread_ts=thread_ts
        )
        logger.info(f"Posted image to Slack: {response['file']['permalink']}")
    except SlackApiError as e:
        logger.error(f"Slack API Error: {str(e)}")


def generate_openai_response(content, thread_messages):
    base_prompt = config["base_prompt"]
    full_content = "\n\n".join([msg.get('text', '') for msg in thread_messages])
    try:
        response = openai_client.chat.completions.create(model=config["image_analysis"]["model"],
                                                         messages=[
                                                             {"role": "system", "content": base_prompt},
                                                             {"role": "user", "content": full_content}
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
