import nextcord
import google.generativeai as genai
import os
import colorama
import requests
import flask
import threading

from nextcord.ext import commands
from nextcord import Interaction, SlashOption, Attachment
from nextcord.ui import View, Select
from colorama import Fore
from flask import Flask

apikey = os.getenv("API_KEY")
token = os.getenv("TOKEN")

genai.configure(api_key=apikey)

bot = commands.Bot(command_prefix=".", intents=nextcord.Intents.all())

app = Flask(__name__)

@app.route("/")
def index():
	return "Use SkiddoxAI today! https://discord.com/oauth2/authorize?client_id=1327622242921611325"

def getBans():
	novaBans = requests.get("http://api.scriptlang.com/bans")
	karmaBans = requests.get("http://karma.scriptlang.com/bans")
	Bans112 = requests.get("http://api.ocbwoy3.dev/banland.json")
	sleepcoreBans = requests.get("https://skidgod.vercel.app/SleepCore/bans.json")

	return {
		"Nova": novaBans.json(),
		"Karma": karmaBans.json(),
		"112": Bans112.json(),
		"Sleepcore": sleepcoreBans.json()
	}

def resolveRobloxUserId(userId):
	userinfo = requests.get(f"https://users.roblox.com/v1/users/{str(userId)}")

	if userinfo.status_code == 200:
		return userinfo.json()
	else:
		return "Error code: " + userinfo.status_code

def getDiscordUserInfo(userId):
	url = f"https://discord.com/api/v10/users/{str(userId)}"
	headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }

	response = requests.get(url, headers=headers)

	if response.status_code == 200:
		return response.json()
	else:
		return "Error code: " + response.status_code

def duckduckgoSearch(query):
	url = f"https://api.duckduckgo.com/?q={query}&format=json"
	response = requests.get(url)
	if response.status_code == 200:
		results = response.json().get("RelatedTopics", [])[:3]
		return [f"{item['Text']}: {item['FirstURL']}" for item in results if "Text" in item]
	else:
		return "Error fetching DuckDuckGo results."

def resolveRobloxUsername(username):
	url = f"https://users.roblox.com/v1/users/search"
	params = {"keyword": username, "limit": 1}
	response = requests.get(url, params=params)

	if response.status_code == 200:
		data = response.json()
		if data["data"]:
			user = data["data"][0]
			return f"Username: {user['name']}, ID: {user['id']}, Created on: {user['created']}"
		else:
			return "User not found."
	else:
		return "Error fetching Roblox user data."
	
def getRobloxUserIdFromName(username):
	url = f"https://users.roblox.com/v1/users/search"
	params = {"keyword": username, "limit": 1}  # Search for the username, limit to 1 result
	response = requests.get(url, params=params)

	if response.status_code == 200:
		data = response.json()
		if data["data"]:
			user = data["data"][0]
			return f"User ID for '{username}': {user['id']}"
		else:
			return f"User '{username}' not found."
	else:
		return "Error fetching user data from Roblox."

tools = [
	{
        "name": "duckduckgoSearch",
        "description": "Searches DuckDuckGo and returns top results for a given query.",
        "parameters": {"query": {"type": "string", "description": "The search query."}}
    },
	{
		"name": "getDiscordUserInfo",
		"description": "Returns the user information that has been resolved from the specified user ID.",
		"parameters": {"userId": {"type": "string", "description": "The User ID to look up."}}
	},
	{
		"name": "resolveRobloxUserId",
		"description": "Returns the user information that has been resolved from the specified user ID.",
		"parameters": {"userId": {"type": "string", "description": "The User ID to look up."}}
	},
	{
		"name": "getBans",
		"description": "Returns the bans from four remote admin providers.",
		"parameters": None
	},
	{
		"name": "resolveRobloxUsername",
		"description": "Returns the user information that has been resolved from the specified username.",
		"parameters": {"username": {"type": "string", "description": "The username to look up."}}
	},
	{
        "name": "getRobloxUserIdFromName",
        "description": "Fetches the Roblox user ID given their username.",
        "parameters": {
            "username": {"type": "string", "description": "The Roblox username to look up."}
        }
    }
]


@bot.event
async def on_connect():
	await bot.change_presence(status = nextcord.Status.dnd, activity = nextcord.Activity(type=nextcord.ActivityType.watching, name="your mother"))

@bot.event
async def on_command_error(ctx, error):
	try:
		await ctx.message.delete()
	except Exception as err:
		embed = nextcord.Embed(
			color = nextcord.Color.red(),
			title = "Error",
			description = "An unexpected error has occured."
		)
		embed.add_field(name="Details", value=err, inline=False)
		embed.timestamp = nextcord.utils.utcnow()
		embed.set_footer(text="Skiddox AI", icon_url="https://cdn.discordapp.com/avatars/1224392642448724012/4875429b51c1bbc32ca18474a0dc0ba4.webp?size=96")
		await ctx.send(embed=embed)

	if isinstance(error, commands.CommandNotFound):
		embed = nextcord.Embed(
			color = nextcord.Color.yellow(),
			title = "Warning",
			description = "This command isn't valid."
		)
		embed.timestamp = nextcord.utils.utcnow()
		embed.set_footer(text="Skiddox AI", icon_url="https://cdn.discordapp.com/avatars/1224392642448724012/4875429b51c1bbc32ca18474a0dc0ba4.webp?size=96") 
		await ctx.send(embed=embed)
		print(f"[{Fore.GREEN}Skiddox AI{Fore.RESET}]: Invalid command ran: {ctx.message.content}")

	if isinstance(error, commands.CheckFailure):
		embed = nextcord.Embed(
			color = nextcord.Color.yellow(),
			title = "Warning",
			description = "You do not have the necessary permissions to use this command."
		)
		embed.timestamp = nextcord.utils.utcnow()
		embed.set_footer(text="Skiddox AI", icon_url="https://cdn.discordapp.com/avatars/1224392642448724012/4875429b51c1bbc32ca18474a0dc0ba4.webp?size=96") 
		await ctx.send(embed=embed)

	if isinstance(error, commands.BadArgument):
		embed = nextcord.Embed(
			color = nextcord.Color.yellow(),
			title = "Warning",
			description = "Invalid arguments were provided to the command."
		)
		embed.timestamp = nextcord.utils.utcnow()
		embed.set_footer(text="Skiddox AI", icon_url="https://cdn.discordapp.com/avatars/1224392642448724012/4875429b51c1bbc32ca18474a0dc0ba4.webp?size=96") 
		await ctx.send(embed=embed)

	if isinstance(error, commands.MissingRequiredArgument):
		embed = nextcord.Embed(
			color = nextcord.Color.yellow(),
			title = "Warning",
			description = "Missing arguments were provided to the command."
		)
		embed.timestamp = nextcord.utils.utcnow()
		embed.set_footer(text="Skiddox AI", icon_url="https://cdn.discordapp.com/avatars/1224392642448724012/4875429b51c1bbc32ca18474a0dc0ba4.webp?size=96") 
		await ctx.send(embed=embed)

@bot.slash_command(name="ask", description="Ask the AI a question.")
async def ask(interaction: Interaction, prompt: str, attachment: Attachment = SlashOption(required = False)):
	model = genai.GenerativeModel('gemini-1.5-flash')

	conversation = model.start_chat(
		system_instruction="You are an Artifical Inteligence that is from the beginning of any converations named as 'Mister Skiddox', who has feelings just like any average human. You may also use every available tools you may have to respond to the user's command, make as much best usage of the most popular and the best searching engines as possible (specifically DuckDuckGo search engine), help the user with any programming-related questions and act as an average 'script kiddie' that actually has some insane programming knowledge. You must, sometimes, respond with exactly the name of the user that is asking you a question. You also have access to more tools that I have given you, such as getBans, which returns user bans from remote admin providers (if you dont know what a remote admin is, it is basically admin commands you get in a roblox game but accessible remotely from a specific point, such as from a website or Discord bot). Sometimes, you may want to use terms like :3, OwO, *meow* and meow :3 whenever you have that strong feeling. If you don't know the answer to a question, you must say that 'you are dumb'; you can not leave any responses blank as you must answer to them. If a tool has an error, write out its Python error. You must not repeat the same tool call unnecessarily and only when you have to. In the getBans results, the names are the providers, which means not only you have to write out the username/user ID that you are looking for in the bans, but also write out the provider you found the username/user ID from. Remember to keep messages below preferably 250 characters. You cannot send messages that are over 1000 characters. And remember: ALWAYS ACT ENTHUSIASTIC AND LIKE A FRIENDLY 'SCRIPT KIDDIE'!",
		tools=tools
	)

	if not attachment.content_type.startswith("image"):
		await interaction.response.send_message("The attachment should be an image.", ephemeral=True)
		return
	
	if attachment:
		response = model.generate_content([prompt, attachment])
		if response.error_code == 200:
			await interaction.response.send_message(response.text)
		else:
			await interaction.response.send_message("> Error code: " + response.error_code)

	else:
		response = model.generate_content(prompt)
		if response.error_code == 200:
			await interaction.response.send_message(response.text)
		else:
			await interaction.response.send_message("> Error code: " + response.error_code)

def main2():
	app.run(host = "0.0.0.0", port = 5000, debug = False, use_reloader = False)

if __name__ == "__main__": 
	bot.run(token)
	app.run(host = "0.0.0.0", port = 5000, debug = False, use_reloader = False)
