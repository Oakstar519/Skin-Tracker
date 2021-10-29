import io
import random
import aiohttp
import base64
import json
import sqlite3 as sqlite

username_url = "https://sessionserver.mojang.com/session/minecraft/profile/"
uuid_url = "https://api.mojang.com/users/profiles/minecraft/"
render_url = "https://mc-heads.net/body/"

subject_pronoun = ("he", "she", "they", "xe")
object_pronoun = ("him", "her", "them", "xem")
possessive_adjective = ("his", "her", "their", "xyr")


# SMALL FUNCTIONS GO HERE


async def format_uuid(arg1: str) -> str:
    return f"{arg1[0:8]}-{arg1[8:12]}-{arg1[12:16]}-{arg1[16:20]}-{arg1[20:]}"


async def convert_pronouns(arg1: str) -> str:
    arg1 = arg1.lower()
    # checks if pronoun matches one of the lists, which have other pronoun tenses
    if arg1 in subject_pronoun:
        return possessive_adjective[subject_pronoun.index(arg1)]
    elif arg1 in object_pronoun:
        return possessive_adjective[object_pronoun.index(arg1)]

    # checks for non-ASCII characters, which would usually indicate an emoji pronoun
    elif not arg1.isascii():
        for i in range(len(arg1)):
            if not arg1[i].isascii():
                return arg1[i] + "s"

    else:
        return arg1


async def get_random_pronoun(arg1: [str, list]) -> str:
    if type(arg1) == str:
        return arg1
    else:
        return arg1[random.randint(0, len(arg1) - 1)]


async def render_skin(arg1: str) -> io.BytesIO:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{render_url}{arg1}") as response:
            return io.BytesIO(await response.read())

# LESS-SMALL FUNCTIONS GO HERE. what defines small? i have no idea. if i knew i probably wouldn't need this.


async def get_user_data(arg1) -> list:
    # returns [uuid, name]
    async with aiohttp.ClientSession() as session:
        try:
            if len(arg1) == 32:
                arg1 = await format_uuid(arg1)

            if 3 <= len(arg1) <= 16:
                async with session.get(f"{uuid_url}{arg1}") as response:
                    response = (await response.json())["id"]
                    return [await format_uuid(response), arg1]

            elif len(arg1) == 36:
                async with session.get(f"{username_url}{arg1}") as response:
                    response = (await response.json())["name"]
                    return [arg1, response]

            else:
                return ["failed"]

        except (json.decoder.JSONDecodeError, aiohttp.ContentTypeError):
            return ["failed"]


async def get_all_data() -> list:
    uuid_list = []
    username_list = []
    pronoun_list = []
    group_list = []

    con = sqlite.connect("database")
    cur = con.cursor()

    fetch = cur.execute('''SELECT uuid FROM user_data''').fetchall()
    if fetch:
        for i in range(len(fetch)):
            uuid_list.append(fetch[i][0])

    fetch = cur.execute('''SELECT username FROM user_data''').fetchall()
    if fetch:
        for i in range(len(fetch)):
            username_list.append(fetch[i][0])

    fetch = cur.execute('''SELECT pronoun FROM user_data''').fetchall()
    if fetch:
        for i in range(len(fetch)):
            if ", " in fetch[i][0]:
                pronoun_list.append((fetch[i][0]).split(", "))
            else:
                pronoun_list.append(fetch[i][0])

    fetch = cur.execute('''SELECT smp FROM smp_presets''').fetchall()
    if fetch:
        fetch = str(fetch).split("'")
        group_list = ""
        for i in range(len(fetch)):
            if fetch[i].upper().isupper() or fetch[i].lower().islower():
                group_list = group_list + " " + (fetch[i])

        group_list = set(group_list.split(" "))
        group_list = list(group_list)[1:]

    con.close()

    master_list = [uuid_list, username_list, pronoun_list, group_list]
    return master_list


async def add_single_to_database(uuid, username, pronoun) -> None:
    con = sqlite.connect("database")
    cur = con.cursor()
    cur.execute('''INSERT INTO user_data (uuid, username, pronoun) VALUES (?, ?, ?)''', (uuid, username, pronoun))
    con.commit()
    con.close()


async def remove_single_from_database(uuid: str) -> None:
    con = sqlite.connect("database")
    cur = con.cursor()
    cur.execute('''DELETE FROM user_data WHERE uuid = ?''', (uuid,))
    con.commit()
    con.close()


async def add_multiple_to_database(arg1: list) -> None:
    # takes a list of sets with (uuid, username, pronouns)
    con = sqlite.connect("database")
    cur = con.cursor()

    for i in range(len(arg1)):
        cur.execute('''INSERT INTO user_data (uuid, username, pronoun) VALUES (?, ?, ?)''',
                    (arg1[i][0], arg1[i][1], arg1[i][2]))

    con.commit()
    con.close()


async def remove_multiple_from_database() -> None:
    # deletes everything
    con = sqlite.connect("database")
    cur = con.cursor()

    cur.execute('''DELETE FROM user_data WHERE uuid LIKE ?''', ("%%",))

    con.commit()
    con.close()


async def add_group_from_database(arg1):
    con = sqlite.connect("database")
    cur = con.cursor()

    result = cur.execute('''SELECT uuid, username, pronoun FROM smp_presets WHERE smp LIKE ?''',
                         (f"%{arg1}%",)).fetchall()

    con.close()
    return result


async def process_pronoun_list(arg1):
    result = []
    arg1 = ((arg1.replace("/", " ")).replace(",", " ")).split(" ")
    for i in range(len(arg1)):
        temp = await convert_pronouns(arg1[i])
        if temp is not None:
            result.append(temp)
        else:
            result.append(arg1[i])

    result = set(result)
    result = list(result)

    if "" in result:
        result.remove("")

    return result


async def refresh_skin_cache(uuid):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{username_url}{uuid}") as response:
            try:
                response = (await response.json())["properties"][0]["value"]
                response = (str(base64.b64decode(response)).split("\""))[17]
                return response
            except (TypeError, KeyError, aiohttp.ClientResponseError):
                return "Error"

# TODO: rewrite functions to be less bad, add function to add/remove multiple users, generally stop opening the database
#  every time anything happens

# TODO: rewrite pronoun processing to work with add_group_from_database()
# ^^ i am incapable of writing decent comments what does this even mean?

yogscast = []
dream_smp = []
free_trial_smp = []
origins_smp = []
mojang = []

# ("UUID", "Username", "Pronoun"),

# https://api.mojang.com/users/profiles/minecraft/

smp = []


async def add_smps_to_database():
    con = sqlite.connect("database")
    cur = con.cursor()

    for i in range(len(smp)):
        temp = (await get_user_data(smp[i][1]))

        cur.execute('''INSERT INTO smp_presets (smp, uuid, username, pronoun) VALUES (?, ?, ?, ?)''',
                    ("test_group", temp[0], smp[i][1], smp[i][2]))

    con.commit()
    con.close()
