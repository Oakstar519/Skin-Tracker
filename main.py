import io
import aiohttp
import discord
from discord.ext import tasks, commands
import requests
import base64

with open("key.txt", "r") as f:
    BOT_KEY = f.read().strip()
    f.close()

with open("channel.txt", "r") as f:
    c = int(f.read().strip())
    f.close()

uuids = ['7163fbce-39ac-4a02-b836-a991c45d2dd1',
         '88e2afec-6f2e-4a34-a96a-de61730bd3ca',
         '05e88dce-714d-4218-be77-fade8b5dfa3c',
         '93b459be-ce4f-4700-b457-c1aa91b3b687',
         '87d91548-6f18-491f-a267-7833caa5d7d8',
         '5f8eb73b-25be-4c5a-a50f-d27d65e30ca0',
         'b0015b93-8a5d-461d-9991-3cfa23e3296f',
         'f6fe2200-609d-4fe6-88b6-529d59ee5b71',
         '7ed3587b-e656-4689-90d6-08e11daaf907',
         '3f28c559-0898-4be1-9f20-9fd37ca9cd22',
         '53bae456-dbbb-4c2f-8c79-9e8ec26c8382',
         'ed260cac-54e4-4ee5-b4de-d289f197fa45',
         'ac224782-efff-4296-b08c-dbde8e47abdb',
         '2dd0cc3b-0825-4c3e-bd99-3bf07ef27447',
         'cae9554c-31be-47e2-ba2b-4b8867adacc5',
         'cfaefb14-46d5-473b-9e8e-67ecbf119df7',
         '62fec5a3-1896-4beb-94e0-36e34898c787',
         'cbf33660-3994-42c3-8d2f-6a1a84d56dea',
         '2f723150-24de-44ff-aeee-87c75f7c7a9e',
         '8fc22d29-4bac-4abe-84d4-7920ed4afe47',
         '826cdcff-ccb0-42c5-9104-fcd4bb4e7f73',
         '21ef397c-3a76-4eb7-aa17-a99d3fc658e2',
         'f9c3c385-f403-403c-b5b7-867e012e9660',
         'a3075fa7-ec13-49a2-aa47-6529e8b7daf2']
usernames = ['BDoubleO100', 'cubfan135', 'Docm77', 'Etho', 'falsesymmetry', 'Grian', 'hypnotizd', 'impulseSV',
             'iskall85', 'iJevin', 'joehillssays', 'Keralis1', 'Mumbo', 'renthedog', 'GoodTimeWithScar',
             'Stressmonster101', 'Tango', 'Tinfoilchef', 'VintageBeef', 'Welsknight', 'xBCrafted', 'Xisuma',
             'Zedaph', 'ZombieCleo']
pronouns = ['his', 'his', 'his', 'his', 'her', 'his', 'his', 'his', 'his', 'his', 'his', 'his', 'his', 'his', 'his',
            'her', 'his', 'his', 'his', 'his', 'his', 'his', 'his', 'her']
cache = []

activity = discord.Game("Minecraft")
bot = commands.Bot(command_prefix="!", status=discord.Status.idle, activity=activity)


@bot.event
async def on_ready():
    channel = bot.get_channel(c)
    print(f"We have logged in as {bot.user}")
    await channel.send("Hermit Skin Bot is online!")
    constant.start()


@tasks.loop(seconds=60.0)
async def constant():
    first = True
    if first:
        for i in range(len(uuids)):
            response = requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{uuids[i]}")
            for j in response.json()['properties']:
                final = base64.b64decode(j['value'].encode("ascii").decode('utf-8'))
                final = str(final.split()[18]).split("\"")[1]
                cache.append(final)

    channel = bot.get_channel(c)
    for i in range(len(uuids)):
        response = requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{uuids[i]}")
        for j in response.json()['properties']:
            final = base64.b64decode(j['value'].encode("ascii").decode('utf-8'))
            final = str(final.split()[18]).split("\"")[1]

            if final != cache[i]:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://visage.surgeplay.com/full/512/{uuids[i]}") as response:
                        if response.status != 200:
                            return await channel.send('g')
                        data = io.BytesIO(await response.read())
                        await channel.send(f"{usernames[i]} has changed {pronouns[i]} skin!")
                        await channel.send(file=discord.File(data, 'test.png'))

                cache[i] = final

bot.run(BOT_KEY)
