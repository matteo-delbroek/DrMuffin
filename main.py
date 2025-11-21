import discord
from discord.ext import commands
from fuzzywuzzy import process
from datetime import datetime, timezone
import os
import sys

# --- 1. Configuratie & Lading van Omgevingsvariabelen ---
# Zorg ervoor dat deze op uw hostingplatform zijn ingesteld!
TOKEN = os.getenv('DISCORD_TOKEN')
BOT_CHANNEL_ID = os.getenv('BOT_CHANNEL_ID')

# --- 2. Constanten en Gedeelde Antwoordteksten ---
# Gebaseerd op de informatie van de Lifesteal SMP server.
ANSWERS = {
    "RULES": (
        "De regels zijn eenvoudig:\n"
        "1. **Respecteer staff en andere spelers (geen toxiciteit/NSFW).**\n"
        "2. **Geen spammen of cheaten (X-ray, vliegen, enz.).**\n"
        "3. **Griefen en Stelen zijn toegestaan** (Het is een Lifesteal server, chaos hoort erbij!) 😈."
    ),
    "ADMIN": (
        "De hoofdbeheerders zijn **@matteo** en **@Fuecoco Fan- (Jarno)**. "
        "Ping hen bij ernstige problemen of vragen. De volledige tags zijn:\n"
        "• Matteo: `@matteo`\n"
        "• Jarno: `@Fuecoco Fan-` (of de tag zoals deze in Discord verschijnt)."
    ),
    "SERVER_START_INSTRUCTIONS": (
        "Deze server draait op **Aternos** en moet handmatig worden gestart. "
        "U moet de **Aternos-gebruikersnaam** gebruiken om de server via `aternos.org` aan te zetten. "
    ),
    "IP_ADDRESS": "Livesteel_Matteo_D.aternos.me:25739",
    "JOIN_INSTRUCTIONS": (
        "1. **Installeer TLauncher** (of gebruik de echte Minecraft launcher).\n"
        "2. Kies in TLauncher de versie **1.21.9** en druk op **Installeren**.\n"
        "3. Open Minecraft, ga naar **Multiplayer** en vul het server-IP in: **Livesteel_Matteo_D.aternos.me:25739**."
    ),
    "COMMANDS": (
        "Hier zijn alle belangrijkste servercommands die je kan gebruiken:\n"
        "• **/tpa [speler]**: Stuur een teleport-verzoek naar iemand.\n"
        "• **/tpahere [speler]**: Vraag iemand om naar jou toe te teleporteren.\n"
        "• **/tpaccept / /tpdeny**: Accepteer of weiger een teleport-verzoek.\n"
        "• **/spawn**: Teleporteer direct naar de spawn van de server.\n"
        "• **/sethome [naam]**: Stel een persoonlijke thuislocatie in.\n"
        "• **/home [naam]**: Teleporteer naar jouw ingestelde home.\n"
        "• **/msg [speler] [bericht]**: Stuur een privé bericht naar iemand."
    ),
}

# Dynamic function for current time
def get_current_time_utc():
    now_utc = datetime.now(timezone.utc)
    return now_utc.strftime("Het is momenteel **%H:%M:%S UTC**.")

# --- QA DATA (Voor Fuzzy Matching van !ask) ---
QA_DATA = {
    "hoe kan ik de server joinen?": (ANSWERS["JOIN_INSTRUCTIONS"], "server"),
    "wat is het server ip?": (f"Het huidige server IP is: **{ANSWERS['IP_ADDRESS']}**", "server"),
    "wat is de ip?": (f"Het server IP is: **{ANSWERS['IP_ADDRESS']}**", "server"),
    "welke versie moet ik gebruiken?": (f"U moet versie **1.21.9** gebruiken.", "server"),
    "hoe start ik de server?": (ANSWERS["SERVER_START_INSTRUCTIONS"], "server"),
    "wat zijn de regels?": (ANSWERS["RULES"], "server"),
    "is stelen toegestaan?": ("Ja, **stelen en grieven is volledig toegestaan** op deze Lifesteal server.", "server"),
    "zijn er commands?": (ANSWERS["COMMANDS"], "server"),
    "kan ik tpa gebruiken?": ("Ja, **/tpa**, **/tpahere** en **/tpaccept** zijn ingeschakeld om te teleporteren.", "server"),
    "wie is de admin?": (ANSWERS["ADMIN"], "server"),
    "wie zijn matteo en jarno?": (ANSWERS["ADMIN"], "server"),
    "wie moet ik pingen?": (ANSWERS["ADMIN"], "server"),
    "hallo": ("Hoi! Ik ben de Lifesteal SMP Bot. Hoe kan ik je helpen met de server?", "general"),
    "wat is aternos?": ("Aternos is een gratis Minecraft-serverhostingplatform.", "general"),
}
# -------------------------------------------------------------------

# --- 3. QA (Vraag & Antwoord) Extensie (Cog) met Kanaalbeperking ---

class QACog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.qa_data = QA_DATA
        self.answers = ANSWERS
        
        self.target_channel_id = None
        if BOT_CHANNEL_ID:
            try:
                self.target_channel_id = int(BOT_CHANNEL_ID)
            except ValueError:
                print("FATALE FOUT: BOT_CHANNEL_ID is ingesteld maar geen geldig nummer.")
                sys.exit(1)


    def create_embed(self, title, description, color=discord.Color.red(), footer=None):
        """Hulpfunctie voor het maken van een Discord Embed."""
        embed = discord.Embed(
            title=f"❤️ {title}",
            description=description,
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        if footer:
            embed.set_footer(text=footer)
        return embed
    
    # GECORRIGEERD: GEEN @commands.check decorator meer, om de TypeError te voorkomen.
    async def cog_check(self, ctx):
        """Implementeert de kanaalbeperking."""
        # 1. Toegestaan als BOT_CHANNEL_ID niet is ingesteld
        if self.target_channel_id is None:
            return True 
        
        # 2. Toegestaan als het kanaal-ID overeenkomt
        if ctx.channel.id == self.target_channel_id:
            return True
        else:
            # 3. Commando gebruikt in het verkeerde kanaal
            channel_mention = f"kanaal met ID `{self.target_channel_id}`"
            try:
                channel = self.bot.get_channel(self.target_channel_id) 
                if channel:
                    channel_mention = channel.mention
            except:
                pass
                
            warning_embed = self.create_embed(
                title="❌ Verkeerd Kanaal Gebruikt",
                description=f"Gelieve de bot-commando's te gebruiken in het toegewezen kanaal: {channel_mention}.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=warning_embed, delete_after=10)
            return False 

    @commands.command()
    async def ping(self, ctx):
        """Reageert met Pong!"""
        await ctx.send(f"Pong! ❤️ (Latency: {round(self.bot.latency * 1000)}ms)")

    @commands.command()
    async def serverstatus(self, ctx):
        """Geeft instructies over het starten van de server (Aternos)."""
        embed = self.create_embed(
            title="Aternos Server Starten",
            description=self.answers["SERVER_START_INSTRUCTIONS"],
            color=discord.Color.orange(),
            footer="Vraag een stafflid om de Aternos-accountnaam."
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def ask(self, ctx, *, question: str = None):
        """Beantwoordt een vraag (gebruikt fuzzy matching)."""
        if not question:
            return await ctx.send("Gelieve een vraag op te geven na het `!ask` commando! Bijvoorbeeld: `!ask wat is het ip`")

        question_lower = question.lower().strip()

        # --- 1. Expliciete Trefwoordcontroles (voor snelle, vaste antwoorden) ---
        explicit_answers = {
            "time": (["hoe laat is het", "huidige tijd"], get_current_time_utc, "Huidige UTC Tijd", discord.Color.gold()),
            "rules": (["wat zijn de regels", "server regels"], self.answers["RULES"], "Server Regels", discord.Color.red()),
            "admin": (["wie is de admin", "wie is staff", "wie moet ik pingen"], self.answers["ADMIN"], "Staff & Admin", discord.Color.purple()),
            "ip": (["wat is de ip", "server adres", "join ip"], f"Het IP-adres is: **{self.answers['IP_ADDRESS']}**", "Server IP Adres", discord.Color.blue()),
            "commands": (["wat zijn de commands", "commando lijst"], self.answers["COMMANDS"], "Server Commando's", discord.Color.teal()),
            "join": (["hoe join ik", "hoe moet ik joinen"], self.answers["JOIN_INSTRUCTIONS"], "Verbindingsinstructies", discord.Color.green())
        }

        for keywords, answer_content, title, color in explicit_answers.values():
            if any(keyword in question_lower for keyword in keywords):
                if callable(answer_content):
                    answer_content = answer_content()
                embed = self.create_embed(title=title, description=answer_content, color=color)
                return await ctx.send(embed=embed)

        # --- 2. Fuzzy Matching ---
        all_questions = list(self.qa_data.keys())
        best_match, score = process.extractOne(question_lower, all_questions)

        if score >= 55:  
            answer_content, q_type = self.qa_data[best_match]
            if q_type == 'general' and score < 65:
                pass 
            else:
                title = "Lifesteal Vraag Beantwoord" if q_type == 'server' else "Algemene Vraag Beantwoord"
                color = discord.Color.red() if q_type == 'server' else discord.Color.dark_gray()
                embed = self.create_embed(title=title, description=answer_content, color=color, footer=f"Vertrouwen: {score}%")
                return await ctx.send(embed=embed)

        # --- 3. Geen match ---
        no_match_embed = self.create_embed(
            title="🤔 Geen Antwoord Gevonden",
            description="Sorry, ik heb geen antwoord gevonden voor deze vraag.\n"
                        "Probeer uw vraag te herformuleren of gebruik trefwoorden zoals: `!ask regels`, `!ask ip`, of `!ask commands`.",
            color=discord.Color.dark_grey()
        )
        await ctx.send(embed=no_match_embed)

# -------------------------------------------------------------------

# --- 4. Discord Bot Configuratie & Start ---
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print("----------------------------------------")
    print(f"✅ Bot online as {bot.user} (Lifesteal SMP Mode)")
    print(f"IP: {ANSWERS['IP_ADDRESS']}")
    if BOT_CHANNEL_ID:
        print(f"🔒 Commando's beperkt tot kanaal ID: {BOT_CHANNEL_ID}")
    print("----------------------------------------")
    
    try:
        await bot.add_cog(QACog(bot))
    except Exception as e:
        print(f"❌ Fout bij het laden van QACog: {e}")

@bot.event
async def on_command_error(ctx, error):
    # Negeer CheckFailure, omdat de cog_check de waarschuwing al stuurt.
    if isinstance(error, commands.CheckFailure):
        return
    
    # Overige foutafhandeling
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(
            title="❌ Onbekend Commando",
            description=f"Het commando `!{ctx.invoked_with}` is ongeldig.\n"
                        "Gebruik **`!ask [vraag]`** (bijv. `!ask wat is het ip`).",
            color=discord.Color.dark_red()
        )
        await ctx.send(embed=embed, delete_after=10)
        return
    
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="⚠️ Argument Ontbreekt",
            description=f"U bent een argument vergeten voor het commando `!{ctx.invoked_with}`.\n"
                        f"Gebruik: `!{ctx.invoked_with} [vraag]`",
            color=discord.Color.yellow()
        )
        await ctx.send(embed=embed, delete_after=10)
        return

# --- Start het bot programma ---
if __name__ == '__main__':
    if not TOKEN:
        print("\nFATALE FOUT: Omgevingsvariabele 'DISCORD_TOKEN' niet gevonden.")
        sys.exit(1)
        
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"Een onbekende fout is opgetreden: {e}")
        sys.exit(1)
