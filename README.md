# Serverless Slack App with OpenAI Integration

## Description

This document details the setup and deployment of a serverless Slack application that integrates with OpenAI to process and respond to Slack messages. The app utilizes AWS Lambda, AWS Secrets Manager, and the Slack and OpenAI SDKs.

## Requirements

- AWS Account
- Slack Account
- OpenAI Account

## Installation Steps

### Step 1: Create AWS Secrets

Store Slack Bot Token and OpenAI API Key securely in AWS Secrets Manager:

```bash
aws secretsmanager create-secret --name SlackBotToken --secret-string '{"SLACK_BOT_TOKEN":"your_slack_bot_token"}'
aws secretsmanager create-secret --name OpenAIApiKey --secret-string '{"OPENAI_API_KEY":"your_openai_api_key"}'
```

### Step 2: Slack App and Permissions

1. **Create a Slack App**:
   - Go to the [Slack API Apps](https://api.slack.com/apps) page.
   - Click "Create New App" and follow the prompts.

2. **Configure OAuth Scopes**:
   - Under **OAuth & Permissions**, add the following OAuth scopes under **Bot Token Scopes**:
     - `app_mentions:read`
     - `channels:history`
     - `channels:read`
     - `chat:write`
     - `chat:write.public`
     - `commands`
     - `files:read`
     - `files:write`
     - `groups:history`
     - `im:history`
     - `incoming-webhook`
     - `mpim:history`

3. **Event Subscriptions**:
   - Enable **Event Subscriptions** and add the following **Bot Events**:
     - `message.channels`
     - `message.groups`
     - `message.im`
     - `message.mpim`

4. **Install the App**:
   - Install the app to your workspace and copy the OAuth access token.

### Step 3: Deploy with AWS SAM

Deploy the application using AWS SAM CLI:

```bash
sam build
sam deploy --guided
```

Follow the prompts to configure your stack name, AWS region, and parameter overrides for `SlackBotTokenSecretName` and `OpenAIApiKeySecretName`.

### Step 4: Connect Slack App to AWS

Set the following environment variables in the AWS Lambda configuration:

- `SLACK_BOT_TOKEN_SECRET_NAME` with the name of the secret containing the Slack Bot API Token.
- `OPENAI_API_KEY_SECRET_NAME` with the name of the secret containing the OpenAI API Key.

### Step 5: API Endpoints

Upon deployment, AWS SAM will provide an API endpoint URL. Configure this URL in your Slack application settings under **Event Subscriptions**.

## Code Overview

### Lambda Function: `lambda_handler`

This function processes incoming Slack events, checks for new messages, and responds appropriately. It can generate text responses or images based on commands received.

### Configuration File (`config.py`)

A configuration file is used to manage dynamic settings for text commands, image analysis, image generation, and base prompts.

```python
config = {
    "text_commands": {
        "generate_image": "згенеруй зображення:",
    },
    "image_analysis": {
        "model": "gpt-4o",
        "max_tokens": 300,
        "analysis_prompt": "Що на цьому зображенні?"
    },
    "image_generation": {
        "initial_comment": "Ось згенероване зображення:",
        "model": "dall-e-3",
        "size": "1024x1024"
    },
    "base_prompt": (
        "Уявіть, що ви AI-консультант з IT, який володіє дотепним гумором. "
        "Наче ти бородатий сисадмін, зроби коротенький, смішний, трошки душнуватий, IT-орієнтований коментар, "
        "використовуючи програмістські жарти, про: "
    )
}
```

### Secrets Management

Utilizes AWS Secrets Manager to securely store and retrieve the Slack Bot Token and OpenAI API Key.

### OpenAI Integration

Uses the OpenAI Python SDK to generate responses or images based on the text received from Slack messages.

### Error Handling

Comprehensive logging and error handling are implemented to manage and debug API calls and response generation.

## Additional Notes

- Ensure that your AWS IAM roles and policies are correctly set up to allow Lambda functions to access Secrets Manager and post logs.
- Update your Slack and OpenAI API keys periodically for security.
- For a detailed guide on creating a Slack app and adding permissions, refer to the [Slack API documentation](https://api.slack.com/apps).

By following these steps, your Serverless Slack App with OpenAI integration should be fully functional, allowing interactive, AI-powered responses within your Slack channels.