import os
import json
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from openai import OpenAI

logger = logging.getLogger()
logger.setLevel(logging.INFO)

slack_bot_token = os.getenv('SLACK_BOT_TOKEN')
openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key)
slack_client = WebClient(token=slack_bot_token)
bot_user_id = slack_client.auth_test()["user_id"]


def lambda_handler(event, context):
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

        if 'text' in slack_event:
            text_content = slack_event['text']
        elif 'files' in slack_event:
            text_content = process_files(slack_event['files'])
        else:
            text_content = "No recognizable content to process."

        response_channel = slack_event.get('channel')
        thread_ts = slack_event.get('ts')
        openai_response = generate_openai_response(text_content)
        post_message_to_slack(response_channel, openai_response, thread_ts)

        return {'statusCode': 200, 'body': 'Event processed'}
    except Exception as e:
        logger.error(f"Error processing Slack event: {str(e)}")
        return {'statusCode': 500, 'body': f'Error processing event: {str(e)}'}


def process_files(files):
    links = [file['url_private'] for file in files if file.get('filetype') in ['jpg', 'png', 'gif']]
    return " ".join(links)


def generate_openai_response(content):
    base_prompt = (
        "Уявіть, що ви AI-консультант з IT, який володіє дотепним гумором. "
        "Наче ти бородатий сисадмін, зроби коротенький, смішний, трошки душнуватий, IT-орієнтований коментар, "
        "використовуючи програмістські жарти, про: "
    )
    prompt = f"{base_prompt} {content}"
    try:
        response = client.chat.completions.create(model="gpt-4-turbo",
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
        slack_client.chat_postMessage(channel=channel, text=message, thread_ts=thread_ts)
    except SlackApiError as e:
        logger.error(f"Slack API Error: {e.response.error}")