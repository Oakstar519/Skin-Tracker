import discord
from discord.ext import commands, tasks
from functions import *

activity = discord.Game("Minecraft")
bot = commands.Bot(command_prefix="!", status=discord.Status.idle, activity=activity)
bot.remove_command("help")


# TODO: fix group entries so the database doesn't need to be opened and closed a million times, rewrite more database
#  stuff


with open("key.txt", "r") as f:
    BOT_KEY = f.read().strip()
    f.close()

with open("channel.txt", "r") as f:
    channel = int(f.read().strip())
    f.close()

uuid = []
username = []
pronoun = []
cache = []
groups = []
iteration = 100

help_msg = "All available commands:\nNote that `user` can refer to username *or* UUID.\n\n" \
           "**!add `<user>` `[pronoun]`:** Adds the account `user` to the list. For users who use multiple pronouns, " \
           "they can be separated by `/` or `,`.\n" \
           "**!addgroup `[group]`:** Either adds all accounts from `group` to the list, or lists available groups.\n" \
           "**!remove `<user>`:** Removes the account `user` from the list.\n" \
           "**!remove-all:** Removes all users from the list.\n" \
           "**!list `[type]`:** Lists all accounts on the list. `type` can be `all`, `uuid`, or `username`.\n" \
           "**!get `<user>`:** Fetches the skin from the account `user`."


@bot.event
async def on_ready():
    global channel
    channel = bot.get_channel(channel)
    print(f"We have logged in as {bot.user}")
    await initialize_data()


async def initialize_data():
    global uuid, username, pronoun, groups
    uuid = (await get_all_data())[0]
    username = (await get_all_data())[1]
    pronoun = (await get_all_data())[2]
    groups = (await get_all_data())[3]

    groups.sort()

    for i in range(len(uuid)):
        cache.append(await refresh_skin_cache(uuid[i]))

    check_skin_updates.start()


@bot.command(name="online")
async def check_online(ctx):
    await ctx.send("Online!")


@bot.command(name="help")
async def send_help_command(ctx):
    await ctx.send(help_msg)


@bot.command(name="secret_admin_command_1")
async def admin_command_1(ctx):
    async with ctx.typing():
        if ctx.message.author.id == 514235805057941525:
            await add_smps_to_database()
        else:
            await ctx.send("no <3")


@bot.command(name="add")
async def add_user(ctx, user_arg=None, pronoun_arg="their", called_by_user=True, uuid_arg=None):
    async with ctx.typing():
        result = ["failed"]
        if user_arg is None:  # no username or UUID passed in
            if called_by_user:
                await ctx.send("The command takes at least one argument: `user`")

        elif uuid_arg is None:  # almost always means username was passed in but not UUID
            result = await get_user_data(user_arg)

            if result != ["failed"]:
                uuid_arg = result[0]
                user_arg = result[1]

        elif uuid_arg is not None:
            result = []

        if result == ["failed"]:
            if called_by_user:
                await ctx.send("The username or UUID is invalid, or that player does not exist.")

        elif uuid_arg not in uuid:

            pronoun_list = await process_pronoun_list(pronoun_arg)

            uuid.append(uuid_arg)
            username.append(user_arg)
            pronoun.append(list(pronoun_list))

            pronoun_to_database = str(pronoun_list).replace("[", "")
            pronoun_to_database = pronoun_to_database.replace("]", "")
            pronoun_to_database = pronoun_to_database.replace("'", "")

            await add_single_to_database(uuid_arg, user_arg, pronoun_to_database)
            cache.append(await refresh_skin_cache(uuid_arg))

            if called_by_user:
                await ctx.send(f"Added {username[-1]}")

        else:
            if called_by_user:
                await ctx.send("That user is already in the list.")


@bot.command(name="add-group", aliases=["addgroup", "group"])
async def add_group(ctx, group=None):
    async with ctx.typing():
        group_list = groups
        if group is None or group not in group_list:
            group_list = str(group_list).replace("'", "`")
            group_list = group_list.strip("[]")

            await ctx.send(f"Groups available:\n{group_list}")

        else:
            user_list = await add_group_from_database(group)

            for i in range(len(user_list)):
                uuid.append(user_list[i][0])
                username.append(user_list[i][1])
                pronoun.append(list(await process_pronoun_list(user_list[i][2])))

            await add_multiple_to_database(user_list)

            await ctx.send(f"Added {len(user_list)} players.")


@bot.command(name="get")
async def get_single_skin(ctx, arg1=None):
    async with ctx.typing():
        if arg1 is None:
            await ctx.send("The command takes one argument: `user`")

        else:
            result = await get_user_data(arg1)

            if result == ["failed"]:
                await ctx.send("The username/UUID is invalid, or that player does not exist.")

            else:
                await ctx.send(file=discord.File((await render_skin(result[0])), f"{result[1]}.png"))


@bot.command(name="list")
async def list_users(ctx, data="all"):
    await ctx.trigger_typing()
    result = ""
    spaces = "                "
    if len(uuid) != 0:
        for i in range(len(uuid)):
            if data == "all":
                result = result + (username[i] + spaces)[0:16] + " - " + uuid[i] + "\n"

            elif "name" in data:
                result = result + (username[i] + "\n")

            elif "uuid" in data:
                result = result + (username[i] + "\n")

        if len(result) <= 1994:
            await ctx.send(f"```{result}```")

        else:
            with open("list.txt", "w") as g:
                g.write(result)
                g.close()

            await ctx.send(file=discord.File("list.txt"))

    else:
        await ctx.send("No accounts in list. Add some with `!add user`.")


@bot.command(name="remove", aliases=["delete", "del"])
async def remove_user(ctx, arg1=None, called_by_user=True):
    async with ctx.typing():
        global uuid, username, pronoun
        index = None

        if len(arg1) == 32:  # formats UUID
            arg1 = format_uuid(arg1)

        if len(arg1) == 36:  # reads formatted UUID
            for i in range(len(uuid)):
                if uuid[i] == arg1:
                    index = i

        elif 3 <= len(arg1) <= 16:  # reads username
            for i in range(len(username)):
                if username[i] == arg1:
                    index = i

        if index is None and called_by_user:
            await ctx.send("The username or UUID is invalid or not in the list.")

        else:
            del username[index]
            del uuid[index]
            del pronoun[index]
            if called_by_user:
                await remove_single_from_database(uuid[index])
                await ctx.send(f"Deleted user")


@bot.command(name="remove-all", aliases=["delete-all", "delall"])
async def remove_all_users(ctx):
    global uuid, username, pronoun
    async with ctx.typing():
        uuid = []
        username = []
        pronoun = []

        await remove_multiple_from_database()

        await ctx.send(f"Removed all users.")


@tasks.loop(seconds=1.0)
async def check_skin_updates():
    global iteration
    if iteration == 300:
        iteration = 0
        for i in range(len(uuid)):
            cached_skin = await refresh_skin_cache(uuid[i])
            if len(cache) < len(uuid):
                cache.append(cached_skin)
            elif cached_skin != cache[i]:
                cache[i] = cached_skin
                render = await render_skin(uuid[i])

                await channel.send(file=discord.File(render, f"{username[i]}.png"),
                                   content=f"{username[i]} has changed {await get_random_pronoun(pronoun[i])} skin!")

        iteration += 1


@bot.event
async def on_message(ctx):
    await bot.process_commands(ctx)


bot.run(BOT_KEY)
