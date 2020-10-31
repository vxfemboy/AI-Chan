import datetime
import os
from dataclasses import dataclass
import asyncio
import discord
from discord.ext import commands
import textstat
from chatterbot import ChatBot
from chatterbot.conversation import Statement
from chatterbot.trainers import ChatterBotCorpusTrainer

#ai chan
TOKEN = 'token here'
channel_name = 'ai-chan'


def ignore_errors(func):
    def wrapper(*args, **kwargs):
        try:
            value = func(*args, **kwargs)
            return value
        except Exception:
            pass
    return wrapper


@dataclass
class BotMessage:

    message: str
    recipent: str

    def __post_init__(self, *args):
        self.created_at = datetime.datetime.now()


class LastMessages:

    maximum_list_size = 100

    expire_after = datetime.timedelta(seconds=10)

    teach_if_len_in = range(3, 50)
    maximum_gunning_fog = 12

    @classmethod
    def _teach_chatbot(cls, response, statement):
        if (
            len(response) not in cls.teach_if_len_in or
            textstat.gunning_fog(response) > cls.maximum_gunning_fog
            ):
            return
        print(f'Teaching bot to answer to "{statement}" with "{response}"')
        CLIENT.chatbot.learn_response(
            Statement(response), Statement(statement)
            )

    @staticmethod
    def _latest_item(items):
        return max(items, key=lambda x: x.created_at)

    def _get_all_items_with_type(self, item_type):
        return [
            m for m in
            self.messages
            if type(m) is item_type
        ]

    def get_last_messages_by_author(self, author):
        return [
            m for m in
            self._get_all_items_with_type(discord.Message)
            if m.author == author
        ]

    @ignore_errors
    def get_last_message_by_author(self, author):
        return self._latest_item(
            self.get_last_messages_by_author(author)
        )

    def get_last_bot_messages_for_recipent(self, recipent):
        return [
            m for m in
            self._get_all_items_with_type(BotMessage)
            if m.recipent == recipent
        ]

    @ignore_errors
    def get_last_bot_message_for_recipent(self, recipent):
        return self._latest_item(
            self.get_last_bot_messages_for_recipent(recipent)
        )

    def _add(self, item):
        while len(self.messages) + 1 > self.maximum_list_size:
            self.messages.remove(min(
                self.messages,
                key=lambda x: x.created_at))
        self.messages.append(item)


    def add_message(self, message):
        if type(message) is not discord.Message:
            raise TypeError('Must be a discord.Message')
        self._add(message)
        last_bot_message = self.get_last_bot_message_for_recipent(
            message.author
            )
        if not last_bot_message:
            return
        if (
            last_bot_message and
            datetime.datetime.now() - last_bot_message.created_at < self.expire_after):
            self._teach_chatbot(
                message.content, last_bot_message.message
                )

    def add_bot_message(self, message, recipent):
        self._add(
            BotMessage(message, recipent)
        )

    def __init__(self):
        self.messages = []


class ai_chan(discord.Client):


    def _respond(self, message):
        self.channel_name = channel_name

        #Limit to a specific channel_name
        if message.author.name == self.user.name or str(message.channel) != self.channel_name:
            return

        statement = Statement(message.content)

        print("Statement: " + str(statement))
        response = self.chatbot.generate_response(
            statement
        ).text
        self.last_messages.add_message(message)
        self.last_messages.add_bot_message(response, message.author)
        return response

    async def on_message(self, message):
        if message.author == self.user or message.content is None:
            return None
        if self._respond(message) != None:
            print("Response: " + str(self._respond(message))) #logic 100
            async with message.channel.typing(): #typing too look realistic
                await asyncio.sleep(2) #delay too look realistic
                await message.channel.send(self._respond(message)) #Response

    async def on_ready(self):
        print(self.user, 'connected to Discord!')



    def __init__(self, *args, **kwargs):
        self.chatbot = ChatBot(
            'Json',
            preprocessors=[
                'chatterbot.preprocessors.clean_whitespace',
                'chatterbot.preprocessors.convert_to_ascii'
        ])
        #ChatterBotCorpusTrainer(self.chatbot).train(
        #    'chatterbot.corpus.english'
        #) #annoying useless datasets
        self.last_messages = LastMessages()

        super().__init__(*args, **kwargs)


if __name__ == '__main__':
    print('Starting AI Chan...')
    CLIENT = ai_chan()
    CLIENT.run(TOKEN)#, bot=False) #selfbot usage for mass data collection shush
