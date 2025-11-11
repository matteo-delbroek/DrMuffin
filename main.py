import discord
from discord.ext import commands
from fuzzywuzzy import process
from datetime import datetime, timezone
import os 

# --- Beveiligde Token Lading ---
# Belangrijk: De waarde wordt op het hostingplatform (Render) ingesteld als een variabele genaamd DISCORD_TOKEN.
TOKEN = os.getenv('MTQzNzQ1NjM3MjA4OTIyOTM0Mw.G6CKih.MjtUroR_E2B1R8p0BTCZQmD_1lSTAKQ_3CuSVg')

# --- Discord Bot Configuratie & Intents setup ---
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Gedeelde Antwoordteksten ---
RULES_ANSWER = (
    "The rules are clear: 1. **Respect staff**. 2. **No NSFW/offensive/toxic behavior**. "
    "3. No spamming/cheating. **4. Griefing & Stealing are fully allowed!** 😈")
ADMIN_ANSWER = (
    "The main administrator is **DrMuffin**! Our Moderators are XxGamerPro69xX and NoobMaster69. "
    "Contact them with serious issues only.")
SERVER_SEED = "The current map seed is **428938104847** - Good luck finding your way! We will not provide coordinates."
OFFLINE_ANSWER = (
    "Go to **https://freemcserver.net/server/1849684** to renew the server or check its status. It might just need a restart!"
)
SERVER_RENEWAL_LINK = "https://freemcserver.net/server/1849684/start"
COMMANDS_ANSWER = (
    "Key server commands include:\n"
    "• **/sell**: Opens the selling menu for quick resource disposal.\n"
    "• **/shop**: Opens the main server shop (buy items, buy spawners).\n"
    "• **/spawn**: Safely returns you to the main spawn area.\n"
    "• **/rtp**: Randomly teleports you to an unexplored location.\n"
    "• **/afk**: Marks you as Away From Keyboard.\n"
    "**NOTE: /tpa, /tpaccept, /tpdeny, and related commands are DISABLED!**")
SELL_ANSWER = (
    "To sell items, use the **/sell** command. This opens a dedicated menu allowing you to quickly sell "
    "your mined and gathered resources for in-game currency. You can also sell items at the **/shop**."
)
# -------------------------------------------------------------------

# --- Extensive QA dataset for the bot ---
qa_data = {
    # 1. Server Connection & Status
    "how do i join the server?":
    "Use this IP: **DrMuffinSMP.enderman.cloud:29603**. Java Edition, cracked clients are allowed!",
    "what is the server ip?":
    "The current server IP is: **DrMuffinSMP.enderman.cloud:29603**",
    "can i join the server?":
    "Yes! We support Java Edition and cracked clients. IP: DrMuffinSMP.enderman.cloud:29603",
    "is it a cracked server?":
    "Yes, cracked clients are welcome to join!",
    "what minecraft version is the server running?":
    "We usually run the latest stable version of Minecraft (currently 1.20+). Check the `#announcements` channel for the exact version.",
    "can i join via bedrock?":
    "No, the server is **only** for Java Edition.",

    # 2. Diamonds / Renewal & Economy
    "how do i get a diamond?":
    "Click **'Renew'** every 3 hours at **https://freemcserver.net/server/1849684** to get 1 diamond 🍩.",
    "how do i renew the server?":
    "Renew every 3 hours at **https://freemcserver.net/server/1849684** to earn a diamond!",
    "how do i earn money?":
    "Sell items in the shop near spawn to earn in-game money!",

    # 3. Chaos & Rules
    "is stealing allowed?":
    "Yes, **stealing and looting is fully allowed**. Chaos is the rule on DrMuffinSMP! 😏",
    "can i grief?":
    "Yes, griefing, destroying, and raiding are **all allowed**. It's a chaos server!",
    "is cheating allowed?":
    "No. Cheating (like X-ray or flying hacks) is **strictly forbidden** and will result in a ban.",
    "is raiding legal?":
    "Yes, raiding other players' bases is a core part of the gameplay.",
    "are there safe zones?":
    "Only the immediate spawn area is a safe zone (no PVP/Griefing). Everywhere else is unsafe.",

    # 4. Plugins and Features
    "can i set a home?":
    "Yes, you can set **one** home using `/sethome` and return with `/home`.",
    "do i keep my inventory when i die?":
    "No, keep inventory is **disabled**. If you die, you lose your items (except in the spawn zone).",
    "is there /tpa?":
    "No, we do not have `/tpa` or easy teleportation. This is to encourage discovery and difficulty.",
    "are there spawners?":
    "Yes, we have custom spawners that work with a **GUI interface** to manage mob spawning.",

    # 5. Community & Staff
    "who is the server owner?":
    ADMIN_ANSWER,
    "who are the staff?":
    ADMIN_ANSWER,
    "who is the admin?":
    ADMIN_ANSWER,

    # 6. General Chat / Bot Info
    "hello":
    "Hello! I am DrMuffinBot. How can I help you enjoy the chaos?",
    "who are you?":
    "I am DrMuffinBot, the official Q&A assistant for DrMuffinSMP.",
}


# --- Dynamic function to get the current time ---
def get_current_time_utc():
    """Berekent de huidige tijd in UTC."""
    now_utc = datetime.now(timezone.utc)
    return now_utc.strftime(
        "It is currently **%H:%M:%S UTC**. (Note: This time zone may not reflect the server's local time.)"
    )


# --- Events & Commands ---
@bot.event
async def on_ready():
    """Bevestigt dat de bot online en klaar is."""
    print(f"✅ Bot online as {bot.user} with {len(qa_data)} known questions.")


@bot.command()
async def ping(ctx):
    """Reageert met Pong! om de latentie te controleren."""
    await ctx.send(f"Pong! 🍩 (Latency: {round(bot.latency * 1000)}ms)")


@bot.command()
async def qa_status(ctx):
    """Toont hoeveel vragen de bot kent."""
    await ctx.send(
        f"I currently know **{len(qa_data)}** answers about the server!")


@bot.command()
async def startserver(ctx):
    """
    Legt uit dat de bot de server niet automatisch kan starten en geeft de handmatige link.
    """
    await ctx.send(
        "I cannot automatically start the server as it requires a human to log in and click the button or solve a captcha. "
        "Please visit the link yourself to manually check the status and start the server: "
        f"**{SERVER_RENEWAL_LINK}**")


@bot.command()
async def ask(ctx, *, question):
    """
    Beantwoordt een vraag op basis van expliciete trefwoorden of fuzzy matching.
    """
    if isinstance(ctx.channel, discord.DMChannel):
        return await ctx.send(
            "Please use me in a server channel so the community can benefit from the answers!"
        )

    if not question:
        return await ctx.send(
            "Please provide a question after the `!ask` command!")

    question_lower = question.lower().strip()

    # --- 1. Expliciete Trefwoordcontroles ---
    time_keywords = [
        "what time is it", "current time", "time now", "how late is it"
    ]
    if any(keyword in question_lower for keyword in time_keywords):
        return await ctx.send(get_current_time_utc())

    rules_keywords = [
        "what are the rules", "show me the rules", "server rules",
        "tell me rules"
    ]
    if any(keyword in question_lower for keyword in rules_keywords):
        return await ctx.send(RULES_ANSWER)

    admin_keywords = [
        "who is the admin", "who is staff", "who is the owner", "admin name",
        "drmuffin"
    ]
    if any(keyword in question_lower for keyword in admin_keywords):
        return await ctx.send(ADMIN_ANSWER)

    seed_keywords = [
        "what is the seed", "what seed is the server using", "server seed"
    ]
    if any(keyword in question_lower for keyword in seed_keywords):
        return await ctx.send(SERVER_SEED)

    commands_keywords = [
        "what are the commands", "all the commands", "command list",
        "what commands can i use", "/commands", "wath are the comands",
        "list of commands"
    ]
    if any(keyword in question_lower for keyword in commands_keywords):
        return await ctx.send(COMMANDS_ANSWER)

    sell_keywords = [
        "how to sell", "sell stuff", "selling items", "use sell command",
        "/sell", "how much money"
    ]
    if any(keyword in question_lower for keyword in sell_keywords):
        return await ctx.send(SELL_ANSWER)

    offline_keywords = [
        "server is not on", "server not starting", "server offline",
        "server down", "server won't load", "not on", "server is not running",
        "wath to do if the server is not on", "is the server up or down"
    ]
    if any(keyword in question_lower for keyword in offline_keywords):
        return await ctx.send(
            f"The server is likely offline. {OFFLINE_ANSWER} Or use the new command `!startserver` for the direct link!"
        )

    # --- 2. Statische QA (Fuzzy Match) ---
    best_match, score = process.extractOne(question_lower, qa_data.keys())

    if score >= 50:
        answer = qa_data[best_match]
        await ctx.send(
            f"**Question Matched (Confidence: {score}%):**\n> {answer}")
    else:
        if score > 30:
            await ctx.send(
                f"Hmm, I'm not sure about that (Closest match was only {score}%). "
                "Try phrasing your question differently, or check the pinned messages!"
            )
        else:
            await ctx.send(
                "Sorry, I don't know the answer 😅 Ask again or contact staff!")


# --- Start het bot programma ---
if __name__ == '__main__':
    if not TOKEN:
        print("\nFATALE FOUT: Omgevingsvariabele 'DISCORD_TOKEN' niet gevonden.")
        print("U moet deze instellen op uw hostingplatform (Render) voordat u de bot start.")
    else:
        try:
            bot.run(TOKEN)
        except discord.LoginFailure:
            print(
                "\nFATALE FOUT: De Discord Token is ongeldig. Controleer uw 'DISCORD_TOKEN' omgevingsvariabele."
            )
        except Exception as e:
            print(f"Een onbekende fout is opgetreden: {e}")
