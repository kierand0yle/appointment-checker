# Swedish Embassy Appointment Scraper

This script checks for available appointments at the Swedish Embassy in London and sends email notifications when appointments become available. It runs automatically every hour using GitHub Actions.

## Features

- Automatically checks for available appointments every hour
- Sends email notifications when appointments become available
- Supports multiple email recipients
- Runs in the cloud using GitHub Actions

## Setup

### Local Development

1. Install the requirements:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export SENDER_EMAIL=your-email@gmail.com
export SENDER_PASSWORD=your-app-specific-password
export RECEIVER_EMAIL=recipient1@example.com,recipient2@example.com
```

Note: For Gmail, you'll need to use an App Password instead of your regular password. You can generate one in your Google Account settings.

### GitHub Actions Setup

1. Fork or clone this repository
2. Go to your repository's Settings > Secrets and variables > Actions
3. Add the following secrets:
   - `SENDER_EMAIL`: Your Gmail address for sending notifications
   - `SENDER_PASSWORD`: Your Gmail app password
   - `RECEIVER_EMAIL`: Comma-separated list of email addresses to receive notifications

The GitHub Action will automatically run every 10 minutes and check for appointments.

## Running Locally

To run the script manually:
```bash
python src/scraper.py
```

## Monitoring

You can monitor the script's runs in the Actions tab of your GitHub repository. Each run will show:
- Whether appointments were found
- Any errors that occurred
- Email notification status
