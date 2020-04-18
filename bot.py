import functools
import os
import re
import sys
from io import BytesIO

import aiohttp
from loguru import logger
from PIL import Image
import hanger

from datawriter import DataWriter


with open('./refresh-token.txt', 'w+') as _write_mode:
    _write_mode.write(os.environ['REFRESH_TOKEN'])

bot = hanger.Client(refresh_token='./refresh-token.txt')


@bot.event
async def on_ready():
    bot._session = aiohttp.ClientSession()
    bot._owner = os.environ['OWNER_EMAIL']

    sys.stderr = DataWriter(terminal=sys.__stderr__)
    logger.add(sys.stderr)

    print('Ready!')


@bot.event
async def on_message(event):
    emote = re.search(r':(.*):', event.text)
    logger.info(f'Searching for emote name from {event.user.fallback_name}')

    if not emote:
        logger.info(f'{event.user.fallback_name} message was not an emote')
        return

    logger.info(f'{event.user.fallback_name} message was an emote')
    emote = emote.group(1)

    async with bot._session.get('https://discordemoji.com/api/') as resp:
        logger.info(f'{event.user.fallback_name} emote is being searched in the API')
        resp = await resp.json()

    emote_url = [_emote for _emote in resp if _emote['title'].lower() == emote.lower()
                 and not _emote['category'] == '9']

    if not emote_url:
        logger.info(f'{event.user.fallback_name} emote was not found in the API')
        return

    emote_url = emote_url[0]['image']
    logger.info(f'{event.user.fallback_name} emote was found in the API')

    async with event.conversation.focused():
        async with event.conversation.typing():
            logger.info(f'{event.user.fallback_name} emote is being written to BytesIO')
            file = BytesIO()

            async with bot._session.get(emote_url) as resp:
                file.write(await resp.read())
                file.seek(0)

            logger.info(f'{event.user.fallback_name} emote is being resized')

            if emote_url.endswith('.gif'):
                _type = 'GIF'
            else:
                _type = 'PNG'

            partial = functools.partial(resize_image, file, (64, 64), _type)
            file = await bot.loop.run_in_executor(None, partial)

            logger.info(f'{event.user.fallback_name} emote is being sent to conversation')

            await event.respond(image=hanger.Image(
                bot, file, filename=f'emote.{_type}'
            ))

            logger.info(f'{event.user.fallback_name} emote was successfully sent to the conversation')


def resize_image(img, size, _type="PNG"):
    im = Image.open(img)
    im = im.resize(size)

    file = BytesIO()
    im.save(file, format=_type)
    file.seek(0)

    return file


bot.connect()
