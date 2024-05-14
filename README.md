# Slack Bot with OpenAI Integration

This project creates a Slack bot that responds to messages in a humorous, IT-oriented manner using the OpenAI GPT-4 model. The bot generates short, humorous comments with IT and sysadmin jokes.

## Prerequisites

- Python 3.8 or higher
- AWS account (for deploying the Lambda function)
- Slack account with admin permissions to create and configure Slack apps
- AWS SAM CLI installed (for deployment)

## Setup

### 1. Clone the Repository

Clone this repository to your local machine:

```bash
git clone https://github.com/yarka-guru/slack-bot-openai.git
cd slack-bot-openai
```

### 2. Install Dependencies

Create a virtual environment and install the required dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Create a `.env` file in the project root and add your Slack bot token and OpenAI API key:

```plaintext
SLACK_BOT_TOKEN=your-slack-bot-token
OPENAI_API_KEY=your-openai-api-key
```

### 4. Create a Slack App

1. Go to the [Slack API](https://api.slack.com/apps) page.
2. Click "Create New App" and follow the prompts to create a new app.
3. In your app settings, navigate to "OAuth & Permissions".
4. Under "OAuth Tokens & Redirect URLs", add the following OAuth scopes:
    - `bot`
    - `channels:history`
    - `channels:read`
    - `chat:write`
    - `chat:write.public`
    - `files:read`
    - `groups:history`
    - `im:history`
    - `mpim:history`
5. Install the app to your workspace and copy the OAuth access token.

### 5. Set Up Event Subscriptions

1. In your app settings, navigate to "Event Subscriptions".
2. Enable "Event Subscriptions".
3. Set the "Request URL" to your server's endpoint (where your Lambda function will be deployed).
4. Add the following bot events:
    - `message.channels`
    - `message.groups`
    - `message.im`
    - `message.mpim`

### 6. Deploy Using AWS SAM CLI

#### Step 1: Install AWS SAM CLI

Follow the instructions to install the AWS SAM CLI from the [official documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html).

#### Step 2: Create `template.yaml`

Ensure you have the `template.yaml` file in the root of your project

#### Step 3: Build and Deploy

Build and deploy the Lambda function using the AWS SAM CLI:

```bash
sam build
sam deploy --guided
```

During the guided deployment, you will be prompted to enter the parameters:
- `SlackBotToken`: Your Slack bot token.
- `OpenAIApiKey`: Your OpenAI API key.

Follow the prompts to complete the deployment.

### Code Overview

#### `lambda_function.py`

This file contains the main logic for handling Slack events and generating responses using the OpenAI API.

##### Key Functions:

- `lambda_handler(event, context)`: The main entry point for the Lambda function. It handles incoming Slack events.
- `process_files(files)`: Processes image files and returns their URLs.
- `generate_openai_response(content)`: Generates a humorous IT-oriented response using the OpenAI API.
- `post_message_to_slack(channel, message)`: Posts a message to a Slack channel using the Slack API.


## Usage

Once everything is set up, your Slack bot will listen for messages in the channels it has access to and respond with humorous, IT-oriented comments.

### Triggering the Bot

- Send a message in a Slack channel or direct message where the bot is present.
- The bot will generate a short, humorous response based on the content of the message.

### Example Interaction

User: "I'm having trouble with my server."

Bot: "Схоже, твій сервер вирішив піти на каву. Час зробити перезавантаження, інакше каву доведеться купувати адміну!"

## License

This project is licensed under the MIT License. See the LICENSE file for details.