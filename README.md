# Swedish Embassy Appointment Scraper

This script checks for available appointments at the Swedish Embassy in London and sends email notifications when appointments become available.

## Setup

1. Install the requirements:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export SENDER_EMAIL=your-email@gmail.com
export SENDER_PASSWORD=your-app-specific-password
```

Note: For Gmail, you'll need to use an App Password instead of your regular password. You can generate one in your Google Account settings.

## Deployment to Heroku

1. Create a new Heroku app
2. Add the following buildpacks:
   - heroku/python
   - https://github.com/heroku/heroku-buildpack-google-chrome
   - https://github.com/heroku/heroku-buildpack-chromedriver
3. Set the environment variables in Heroku:
   - SENDER_EMAIL
   - SENDER_PASSWORD
4. Deploy the code to Heroku
5. Scale the worker dyno:
```bash
heroku ps:scale worker=1
```

## Local Development

To run the script locally:
```bash
python src/scraper.py
```
