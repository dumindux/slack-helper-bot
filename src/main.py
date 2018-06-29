"""Slack bot
"""
import time
import re
import json
import datetime
import math
import numbers
import pretty_cron
from cron_descriptor import get_description
from slackclient import SlackClient
import holidays
import handlers.tasks

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

with open('config/config.json', 'r') as config_file:
    CONFIG = json.loads(config_file.read())

with open('config/schedule.json', 'r') as jobs_file:
    JOBS = json.loads(jobs_file.read())

with open('config/tasks.json', 'r') as tasks_file:
    TASKS = json.loads(tasks_file.read())

# instantiate Slack client
SLACK_CLIENT = SlackClient(CONFIG["slackToken"])
SLACK_BOT_ID = None

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        print(event)
        if event["type"] == "message" and not "subtype" in event:
            if event["channel"].startswith("D"):
                return event["user"], event["text"], event["channel"]
            else:
                user_id, message = parse_direct_mention(event["text"])
                if user_id == SLACK_BOT_ID:
                    return event["user"], message, event["channel"]
    return None, None, None


def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)


def handle_command(user, command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Sorry, I am not sure what you mean. Try _*@Xarvis help*_ to see what I can help you with\n"

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.lower().startswith("schedule "):
        command_split = command.split("schedule ")
        if command_split[1].lower().startswith("list"):
            response = "*Scheduled jobs*\n"
            for key in JOBS:
                response += "- " + JOBS[key]["title"] + "\n"
        else:
            partial_reponse = ""
            for key in JOBS:
                description = pretty_cron.prettify_cron(JOBS[key]["sequence"])
                if description == JOBS[key]["sequence"]:
                    description = get_description(description)
                description = description[0].lower() + description[1:]
                if command_split[1].lower() in JOBS[key]["title"].lower() or JOBS[key]["title"].lower() in command_split[1].lower():
                    partial_reponse += "*" + JOBS[key]["title"] + "*\n" \
                                                                  "- Runs " + description + " (ET)\n"
            if len(partial_reponse) > 0:
                response = "Job scheduled time(s)\n" + partial_reponse
    elif command.lower().startswith("help"):
        response = "Hey there, following are the queries that I am trained to help you with as of now,\n" \
                   "- *schedule list* - _Get a list of scheduled payment related job titles (ach, ledger etc)_\n" \
                   "- *schedule <job_name>* - _Get the scheduled time of a specific job_\n" \
                   "- *holidays* - _Get the list of US holidays for the year_\n" \
                   "- *calc <expression>* - _Do a calculation_\n" \
                   "- *execute <job_name> <optional parameters>* - _Execute a predifined job_\n" \
                   "Use *@Xarvis _command_* to ask me something"
    elif command.lower().startswith("holidays"):
        now = datetime.datetime.now()
        response = "US public holidays\n"
        for date, name in sorted(holidays.US(years=now.year).items()):
            response += "- " + "*" + date.strftime("%A") + "*, " + date.strftime("%B %d ") + date.strftime(", %Y") + ": " + name + "\n"
    elif "thank" in command.lower() or "thanks" in command.lower():
        response = "You are welcome <@" + user + ">"
    elif command.lower().startswith("calc "):
        command_split = command.split("calc ")
        try:
            result = eval(command_split[1])
            if isinstance(result, numbers.Real):
                response = "<@" + user + ">, result: " + str(result)
            else:
                response = "<@" + user + ">, invalid mathematical expression"
        except:
            response = "<@" + user + ">, invalid mathematical expression"
    elif "hi" in command.lower() or "hey" in command.lower():
        response = "Hey <@" + user + ">, Try _*@Xarvis help*_ to see what I can help you with"
    elif command.lower().startswith("execute"):
        response = handlers.tasks.execute_task(command.lower().strip()[8:].split(" "), TASKS)
    
    # Sends the response back to the channel
    SLACK_CLIENT.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

if __name__ == "__main__":
    if SLACK_CLIENT.rtm_connect(with_team_state=False):
        print("Slack Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        SLACK_BOT_ID = SLACK_CLIENT.api_call("auth.test")["user_id"]
        while True:
            user_arg, command_arg, channel_arg = parse_bot_commands(SLACK_CLIENT.rtm_read())
            if command_arg:
                handle_command(user_arg, command_arg, channel_arg)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")