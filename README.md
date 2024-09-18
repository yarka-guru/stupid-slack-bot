# Serverless Slack App with OpenAI and Stability AI Integration

## Description

This document details the setup and deployment of a serverless Slack application that integrates with OpenAI and Stability AI to process and respond to Slack messages. The app utilizes AWS Lambda, AWS Secrets Manager, DynamoDB, and the Slack, OpenAI, and Stability AI SDKs.

## Requirements

- AWS Account
- Slack Account
- OpenAI Account
- Stability AI Account

## Installation Steps

### Step 1: Create AWS Secrets

Store Slack Bot Token, OpenAI API Key, and Stability AI API Key securely in AWS Secrets Manager:

```bash
aws secretsmanager create-secret --name SlackBotToken --secret-string '{"SLACK_BOT_TOKEN":"your_slack_bot_token"}'
aws secretsmanager create-secret --name OpenAIApiKey --secret-string '{"OPENAI_API_KEY":"your_openai_api_key"}'
aws secretsmanager create-secret --name StabilityApiKey --secret-string '{"STABILITY_API_KEY":"your_stability_api_key"}'
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

Follow the prompts to configure your stack name, AWS region, and parameter overrides for `SlackBotTokenSecretName`, `OpenAIApiKeySecretName`, and `StabilityApiKeySecretName`.

### Step 4: Connect Slack App to AWS

Set the following environment variables in the AWS Lambda configuration:

- `SLACK_BOT_TOKEN_SECRET_NAME` with the name of the secret containing the Slack Bot API Token.
- `OPENAI_API_KEY_SECRET_NAME` with the name of the secret containing the OpenAI API Key.
- `STABILITY_API_KEY_SECRET_NAME` with the name of the secret containing the Stability API Key.
- `DYNAMODB_TABLE_NAME` with the name of the DynamoDB table created.

### Step 5: API Endpoints

Upon deployment, AWS SAM will provide an API endpoint URL. Configure this URL in your Slack application settings under **Event Subscriptions**.

## Code Overview

### Lambda Function: `lambda_handler`

This function processes incoming Slack events, checks for new messages, and responds appropriately. It can generate text responses or images based on commands received.

### Handling Text Commands

The application listens for specific text commands to trigger responses. For example, if a message contains "згенеруй зображення:", the bot will generate an image based on the provided description.

### Image Generation

The bot uses the OpenAI DALL-E model and Stability AI's sd3 model to generate images based on text descriptions. The generated images are then uploaded to Slack with a specified initial comment.

### Vision and File Analysis

The bot can analyze images and other file types uploaded to Slack. When a file is shared, the bot processes the file, determines its type, and then either analyzes the image content or processes other document types accordingly.

### Secrets Management

Utilizes AWS Secrets Manager to securely store and retrieve the Slack Bot Token, OpenAI API Key, and Stability API Key.

### DynamoDB Integration

A DynamoDB table is used to store the last responded message timestamp for each thread, ensuring that the bot responds only once per message.

### OpenAI and Stability AI Integration

Uses the OpenAI Python SDK and Stability AI API to generate responses or images based on the text received from Slack messages.

### Error Handling

Comprehensive logging and error handling are implemented to manage and debug API calls and response generation.

### Stop Word Functionality

The bot includes a stop word functionality to prevent further responses in a thread if a specific word or phrase is detected. This allows users to stop the bot from responding in a particular thread by using the configured stop word.

### Example Prompts for Each Function

#### Generate Image (OpenAI DALL-E 3)

- **Command**: згенеруй зображення: [description]
- **Example**: згенеруй зображення: сонячний день у парку з дітьми, що граються

#### Generate Diffusion Image (Stability AI sd3)

- **Command**: generate image: [description]
- **Example**: generate image: picturesque sunset on the beach

## Additional Notes

- Ensure that your AWS IAM roles and policies are correctly set up to allow Lambda functions to access Secrets Manager, DynamoDB, and post logs.
- Update your Slack, OpenAI, and Stability API keys periodically for security.
- For a detailed guide on creating a Slack app and adding permissions, refer to the [Slack API documentation](https://api.slack.com/apps).

By following these steps, your Serverless Slack App with OpenAI and Stability AI integration should be fully functional, allowing interactive, AI-powered responses within your Slack channels.
