import os
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Configuration from environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LIBRETRANSLATE_URL = os.getenv("LIBRETRANSLATE_URL", "http://libretranslate:5000")

# Set up bot with the necessary intent
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content
bot = commands.Bot(command_prefix="!", intents=intents)

# In-memory storage for user language preferences (for a production bot, use a database)
user_languages = {}

async def translate_text(text: str, target_lang: str, source_lang: str = "auto") -> str:
    """Call the LibreTranslate API to translate text."""
    async with aiohttp.ClientSession() as session:
        payload = {
            "q": text,
            "source": source_lang,
            "target": target_lang,
            "format": "text"
        }
        try:
            async with session.post(f"{LIBRETRANSLATE_URL}/translate", json=payload, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("translatedText", "")
                else:
                    print(f"LibreTranslate error: {resp.status} - {await resp.text()}")
                    return None
        except Exception as e:
            print(f"Translation request failed: {e}")
            return None

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command(name="setlang")
async def set_language(ctx, lang_code: str):
    """Set your preferred language for automatic translations (e.g., !setlang es)."""
    user_languages[ctx.author.id] = lang_code.lower()
    await ctx.send(f"Your language has been set to `{lang_code}`. I'll DM you translations of messages in other languages.")

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Process commands first
    await bot.process_commands(message)

    # Automatic translation logic
    author_id = message.author.id
    target_lang = user_languages.get(author_id)

    if target_lang is None:
        return  # User hasn't set a language preference

    # Translate the message to the user's preferred language
    translated = await translate_text(message.content, target_lang)

    if translated and translated != message.content:
        try:
            # Send the translation privately via DM
            await message.author.send(f"**Translation of your message in #{message.channel.name}:**\n{translated}")
        except discord.Forbidden:
            # User has DMs disabled; optionally log or ignore
            pass

# Start the bot
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
