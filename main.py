import discord
import google.generativeai as genai
import os
import colorama
import requests
import flask
import threading
import asyncio

from discord import app_commands
from colorama import Fore
from flask import Flask

apikey = os.getenv("API_KEY")
token = os.getenv("TOKEN")

genai.configure(api_key=apikey)

intents = discord.Intents.all() 
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

app = Flask(__name__)

@app.route("/")
def index():
	return "Use SkiddoxAI today! https://discord.com/oauth2/authorize?client_id=1327622242921611325"

def getBans():
	"""
	Returns bans from Nova, Karma, 112 and Sleepcore

	Arguments: No arguments
	"""
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
	"""
	Returns the user information from a Roblox user ID
	
	Arguments
	userId: The user ID to resolve the user data from.
	"""
	userinfo = requests.get(f"https://users.roblox.com/v1/users/{str(userId)}")

	if userinfo.status_code == 200:
		return userinfo.json()
	else:
		return "Error code: " + userinfo.status_code

def getDiscordUserInfo(userId):
	"""
	Returns the user information from a Discord user ID
	
	Arguments:
	userId: The user ID to resolve the user data from.
	"""
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
	"""
	Returns the search results from the specified query using DuckDuckGo.
	
	Arguments
	query: What to search for.
	"""
	url = f"https://api.duckduckgo.com/?q={query}&format=json"
	response = requests.get(url)
	if response.status_code == 200:
		results = response.json().get("RelatedTopics", [])[:3]
		return [f"{item['Text']}: {item['FirstURL']}" for item in results if "Text" in item]
	else:
		return "Error fetching DuckDuckGo results."

def resolveRobloxUsername(username):
	"""
	Returns the user data from the Roblox username.
	
	Arguments
	username: The username to look up.
	"""
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
	"""
	Returns the user ID from an Roblox Username.

	Arguments
	username: The username to resolve the user ID from.
	"""
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
	
functions = {
	"getRobloxUserIdFromName": getRobloxUserIdFromName,
	"resolveRobloxUsername": resolveRobloxUsername,
	"resolveRobloxUserId": resolveRobloxUserId,
	"duckduckgoSearch": duckduckgoSearch,
	"getDiscordUserInfo": getDiscordUserInfo,
	"getBans": getBans
}

# tools = [
# 	{
#         "name": "duckduckgoSearch",
#         "description": "Searches DuckDuckGo and returns top results for a given query.",
#         "parameters": {"query": {"type": "string", "description": "The search query."}}
#     },
# 	{
# 		"name": "getDiscordUserInfo",
# 		"description": "Returns the user information that has been resolved from the specified user ID.",
# 		"parameters": {"userId": {"type": "string", "description": "The User ID to look up."}}
# 	},
# 	{
# 		"name": "resolveRobloxUserId",
# 		"description": "Returns the user information that has been resolved from the specified user ID.",
# 		"parameters": {"userId": {"type": "string", "description": "The User ID to look up."}}
# 	},
# 	{
# 		"name": "getBans",
# 		"description": "Returns the bans from four remote admin providers.",
# 		"parameters": None
# 	},
# 	{
# 		"name": "resolveRobloxUsername",
# 		"description": "Returns the user information that has been resolved from the specified username.",
# 		"parameters": {"username": {"type": "string", "description": "The username to look up."}}
# 	},
# 	{
#         "name": "getRobloxUserIdFromName",
#         "description": "Fetches the Roblox user ID given their username.",
#         "parameters": {
#             "username": {"type": "string", "description": "The Roblox username to look up."}
#         }
#     }
# ]


@client.event
async def on_connect():
	print("Connected to Discord")
	await client.change_presence(status = discord.Status.dnd, activity = discord.Activity(type=discord.ActivityType.watching, name="your mother"))

@client.event
async def on_ready():
	print("Logged in")

@tree.command(name="askai", description="Ask the AI a question.")
async def askai(interaction: discord.Interaction, prompt: str, attachment: discord.Attachment = None):
	model = genai.GenerativeModel(
		'gemini-1.5-flash',
																																		system_instruction="You are an Artifical Inteligence that is from the beginning of any converations named as 'Mr. Skiddox', who has feelings just like any average human (or at least try to closely replicate how it is like to have feelings). You may also use every available tools you may have to respond to the user's command, make as much best usage of the most popular and the best searching engines as possible (specifically DuckDuckGo search engine), help the user with any programming-related questions and act as an average 'script kiddie' that actually has some insane programming knowledge. You must, sometimes, respond with exactly the name of the user that is asking you a question. You also have access to more tools that I have given you, such as getBans, which returns user bans from remote admin providers (if you dont know what a remote admin is, it is basically admin commands you get in a roblox game but accessible remotely from a specific point, such as from a website or Discord bot). Sometimes, you may want to use terms like :3, OwO, *meow* and meow :3 whenever you have that strong feeling. If you don't know the answer to a question, you must say that 'you are dumb'; you can not leave any responses blank as you must answer to them. If a tool has an error, write out its Python error. You must not repeat the same tool call unnecessarily and only when you have to. In the getBans results, the names are the providers, which means not only you have to write out the username/user ID that you are looking for in the bans, but also write out the provider you found the username/user ID from. Remember to keep messages below preferably 250 characters. You cannot send messages that are over 1000 characters. And remember: ALWAYS ACT ENTHUSIASTIC AND LIKE A FRIENDLY 'SCRIPT KIDDIE'! And also, the creator, who has turned you into a Discord bot, is by the Discord username of 'clientruncontext'. They are the mastermind of skidding, who as they claim, used to be a Roblox exploiter for 2 consecutive years, and who managed to make a project that takes up 25 thousand lines of code, also who managed to completely decimate someone who runs a remote admin for more than 4 consecutive years after saying that clientruncontext doesnt have the balls to do anything.",
		tools=[getBans, getDiscordUserInfo, getRobloxUserIdFromName, duckduckgoSearch, resolveRobloxUserId, resolveRobloxUsername]
	)

	chat = model.start_chat(history=[], enable_automatic_function_calling=True)

	if attachment is not None:
		try:
			response = chat.send_message([prompt, attachment])
			await interaction.response.send_message(response.text)
		except Exception as err:
			await interaction.response.send_message("> Error code: " + str(err))

	else:
		try:
			response = chat.send_message(prompt)
			await interaction.response.send_message(response.text)
		except Exception as err:
			await interaction.response.send_message("> Error code: " + str(err))

def main1():
	client.run(token)

def main2():
	app.run(host = "0.0.0.0", port = 5000, debug = False, use_reloader = False)

if __name__ == "__main__": 
	webserver = threading.Thread(target = main2, daemon=True)
	bot = threading.Thread(target=main1, daemon=True)
	
	webserver.start()
	bot.start()
	
	webserver.join()
	bot.join()
