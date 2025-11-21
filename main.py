import discord
from discord.ext import commands
from fuzzywuzzy import process
from datetime import datetime, timezone
import os
import sys

# --- 1. Configuratie & Lading van Omgevingsvariabelen ---
# Laad de benodigde variabelen
TOKEN = os.getenv('DISCORD_TOKEN')
BOT_CHANNEL_ID = os.getenv('BOT_CHANNEL_ID')

# --- 2. Constanten en Gedeelde Antwoordteksten (AANGEPAST VOOR LIFESTEAL SMP) ---
ANSWERS = {
    "RULES": (
        "De regels zijn eenvoudig:\n"
        "1. **Respecteer staff en andere spelers (geen toxiciteit/NSFW).**\n"
        "2. **Geen spammen of cheaten (X-ray, vliegen, enz.).**\n"
        "3. **Griefen en Stelen zijn toegestaan** (Het is een Lifesteal server, chaos hoort erbij!) 😈."
    ),
    "ADMIN": (
        "De hoofdbeheerders zijn **matteo** en **Jarno** (@Fuecoco Fan-). "
        "Ping hen met @matteo of @Fuecoco Fan- (Jarno) bij ernstige problemen of vragen."
    ),
    "SEED": (
        "We geven de map seed niet vrij! Dit is om de ontdekking en het 'survival'-aspect te behouden. "
        "Gebruik `/rtp` om een willekeurige locatie te vinden."
    ),
    "SERVER_START_INSTRUCTIONS": (
        "Deze server draait op **Aternos** en moet handmatig worden gestart. "
        "U moet de **Aternos-gebruikersnaam** (die in Discord is gedeeld) gebruiken om de server via `aternos.org` aan te zetten. "
        "Matteo's bericht vermeldde: 'Stuur Aternos gebruikersnaam zodat je de server kan aanzetten.'"
    ),
    "IP_ADDRESS": "Livesteel_Matteo_D.aternos.me:25739",
    "JOIN_INSTRUCTIONS": (
        "1. **Installeer TLauncher** (of gebruik de echte Minecraft launcher).\n"
        "2. Kies in TLauncher de versie **1.21.9** en druk op **Installeren**.\n"
        "3. Open Minecraft, ga naar **Multiplayer** en vul het server-IP in: **Livesteel_Matteo_D.aternos.me:25739**."
    ),
    "COMMANDS": (
        "Belangrijke servercommands (op basis van de commandolijst):\n"
        "• **/tpa [speler]**: Stuur een teleport-verzoek naar iemand.\n"
        "• **/tpahere [speler]**: Vraag iemand om naar jou toe te teleporteren.\n"
        "• **/tpaccept / /tpdeny**: Accepteer of weiger een teleport-verzoek.\n"
        "• **/spawn**: Teleporteer direct naar de spawn van de server.\n"
        "• **/sethome [naam]**: Stel een persoonlijke thuislocatie in.\n"
        "• **/home [naam]**: Teleporteer naar jouw ingestelde home.\n"
        "• **/msg [speler] [bericht]**: Stuur een privé bericht naar iemand."
    ),
}

# --- Dynamic function to get the current time ---
def get_current_time_utc():
    """Berekent de huidige tijd in UTC."""
    now_utc = datetime.now(timezone.utc)
    return now_utc.strftime(
        "Het is momenteel **%H:%M:%S UTC**. (Let op: Dit is niet de lokale tijd van de server host.)"
    )

# --- QA DATA ---
# Een gecombineerde QA-data met server-specifieke en algemene vragen.
QA_DATA = {
    # Server Connection & Status (Type: server)
    "hoe kan ik de server joinen?": (ANSWERS["JOIN_INSTRUCTIONS"], "server"),
    "wat is het server ip?": (f"Het huidige server IP is: **{ANSWERS['IP_ADDRESS']}**", "server"),
    "wat is de ip?": (f"Het server IP is: **{ANSWERS['IP_ADDRESS']}**", "server"),
    "welke versie moet ik gebruiken?": (f"U moet versie **1.21.9** gebruiken, zoals vermeld in #ip.", "server"),
    "heb ik de echte minecraft nodig?": ("Nee, TLauncher is toegestaan om te joinen.", "server"),
    "hoe start ik de server?": (ANSWERS["SERVER_START_INSTRUCTIONS"], "server"),
    "is de server online?": (ANSWERS["SERVER_START_INSTRUCTIONS"], "server"),
    
    # Lifesteal & Chaos (Type: server)
    "wat zijn de regels?": (ANSWERS["RULES"], "server"),
    "is stelen toegestaan?": ("Ja, **stelen en grieven is volledig toegestaan** op deze Lifesteal server.", "server"),
    "mag ik griefen?": ("Ja, griefing is toegestaan buiten de spawn.", "server"),
    "is cheaten toegestaan?": ("Nee. Cheating (X-ray, hacks) is **strikt verboden** en leidt tot een ban.", "server"),
    "wat gebeurt er als ik dood ga?": ("Omdat het een Lifesteal SMP is, verlies je mogelijk levens (harten) en je items.", "server"),
    
    # Plugins and Features (Type: server)
    "zijn er commands?": (ANSWERS["COMMANDS"], "server"),
    "kan ik tpa gebruiken?": ("Ja, **/tpa**, **/tpahere** en **/tpaccept** zijn ingeschakeld om te teleporteren.", "server"),
    "kan ik een home zetten?": ("Ja, gebruik **/sethome [naam]** en **/home [naam]** om een home te zetten en te bereizen.", "server"),
    "wat is de /spawn command?": ("**/spawn** teleporteert je veilig terug naar het beginpunt.", "server"),
    
    # Community & Staff (Type: server)
    "wie is de admin?": (ANSWERS["ADMIN"], "server"),
    "wie is de staff?": (ANSWERS["ADMIN"], "server"),
    "wie zijn matteo en jarno?": (ANSWERS["ADMIN"], "server"),
    
    # Algemene Kennis (Type: general)
    "hallo": ("Hoi! Ik ben de Lifesteal SMP Bot. Hoe kan ik je helpen met de server?", "general"),
    "hoe gaat het?": ("Het gaat goed. Ik ben geprogrammeerd in Python en sta klaar om te helpen!", "general"),
    "wat is aternos?": ("Aternos is een gratis Minecraft-serverhostingplatform dat gebruikt wordt voor deze server.", "general"),
}
# -------------------------------------------------------------------

# --- 3. QA (Vraag & Antwoord) Extensie (Cog) met Kanaalbeperking ---

class QACog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.qa_data = QA_DATA
        self.answers = ANSWERS
        
        # Converteer het omgevings-ID naar een integer
        self.target_channel_id = None
        if BOT_CHANNEL_ID:
            try:
                self.target_channel_id = int(BOT_CHANNEL_ID)
            except ValueError:
                print("FATALE FOUT: BOT_CHANNEL_ID moet een geldig nummer zijn.")
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
    
    # CRUCIALE CONTROLE: Deze functie wordt uitgevoerd vóór elk commando in deze Cog.
    @commands.check
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
            
            # Probeer de kanaalnaam te vermelden (gebruikt bot.get_channel)
            channel_mention = f"kanaal met ID `{self.target_channel_id}`"
            try:
                channel = self.bot.get_channel(self.target_channel_id)
                if channel:
                    channel_mention = channel.mention
            except:
                pass # Als we het kanaal niet kunnen vinden, gebruiken we de ID string
                
            warning_embed = self.create_embed(
                title="❌ Verkeerd Kanaal Gebruikt",
                description=f"Gelieve de bot-commando's (zoals `!ask`) te gebruiken in het toegewezen kanaal: {channel_mention}.",
                color=discord.Color.orange()
            )
            
            # Stuur de waarschuwing en verwijder deze na 10 seconden
            await ctx.send(embed=warning_embed, delete_after=10)
            return False # Voorkomt dat het commando doorgaat.

    @commands.command()
    async def ping(self, ctx):
        """Reageert met Pong! om de latentie te controleren."""
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
        """
        Beantwoordt een vraag op basis van expliciete trefwoorden of fuzzy matching.
        """
        if not question:
            return await ctx.send("Gelieve een vraag op te geven na het `!ask` commando! Bijvoorbeeld: `!ask wat is het ip`")

        question_lower = question.lower().strip()

        # --- 1. Expliciete Trefwoordcontroles (voor vaste, belangrijke antwoorden) ---
        explicit_answers = {
            "time": (["hoe laat is het", "huidige tijd", "tijd nu"], get_current_time_utc(), "Huidige UTC Tijd", discord.Color.gold()),
            "rules": (["wat zijn de regels", "toon mij de regels", "server regels", "regels"], self.answers["RULES"], "Server Regels", discord.Color.red()),
            "admin": (["wie is de admin", "wie is staff", "wie is de eigenaar", "admin naam", "matteo", "jarno"], self.answers["ADMIN"], "Staff & Admin", discord.Color.purple()),
            "ip": (["wat is de ip", "server adres", "join ip"], f"Het IP-adres is: **{self.answers['IP_ADDRESS']}**", "Server IP Adres", discord.Color.blue()),
            "commands": (["wat zijn de commands", "alle commands", "commando lijst", "welke commands kan ik gebruiken", "/commands"], self.answers["COMMANDS"], "Server Commando's", discord.Color.teal()),
            "join": (["hoe join ik", "hoe moet ik joinen", "hoe kan ik verbinden"], self.answers["JOIN_INSTRUCTIONS"], "Verbindingsinstructies", discord.Color.green())
        }

        for keywords, answer_content, title, color in explicit_answers.values():
            if any(keyword in question_lower for keyword in keywords):
                if callable(answer_content):
                    answer_content = answer_content()

                embed = self.create_embed(
                    title=title,
                    description=answer_content,
                    color=color
                )
                return await ctx.send(embed=embed)

        # --- 2. Fuzzy Matching (voor dynamische QA) ---
        all_questions = list(self.qa_data.keys())
        best_match, score = process.extractOne(question_lower, all_questions)

        if score >= 55:  
            answer_content, q_type = self.qa_data[best_match]
            
            # Hogere drempel voor 'general' vragen om willekeurige antwoorden te vermijden
            if q_type == 'general' and score < 65:
                pass # Ga naar Geen Match
            else:
                title = "Lifesteal Vraag Beantwoord" if q_type == 'server' else "Algemene Vraag Beantwoord"
                color = discord.Color.red() if q_type == 'server' else discord.Color.dark_gray()

                embed = self.create_embed(
                    title=title,
                    description=answer_content,
                    color=color,
                    footer=f"Vertrouwen: {score}% | Best gematcht met: '{best_match}'"
                )
                return await ctx.send(embed=embed)

        # --- 3. Geen match ---
        no_match_embed = self.create_embed(
            title="🤔 Geen Antwoord Gevonden",
            description="Sorry, ik heb geen antwoord gevonden voor deze vraag in mijn database.\n\n"
                        "Probeer uw vraag te herformuleren of gebruik een van de trefwoorden: `!ask regels`, `!ask ip`, `!ask commands`.",
            color=discord.Color.dark_grey()
        )
        await ctx.send(embed=no_match_embed)

# -------------------------------------------------------------------

# --- 4. Discord Bot Configuratie & Intents setup ---
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    """Bevestigt dat de bot online en klaar is en laadt de Cogs."""
    print("----------------------------------------")
    print(f"✅ Bot online as {bot.user} (Lifesteal SMP Mode)")
    print(f"IP: {ANSWERS['IP_ADDRESS']}")
    if BOT_CHANNEL_ID:
        print(f"🔒 Commando's beperkt tot kanaal ID: {BOT_CHANNEL_ID}")
    else:
        print("⚠️ BOT_CHANNEL_ID is NIET ingesteld. Commando's werken overal.")
    print("----------------------------------------")

    # Laad de QA Extensie
    try:
        await bot.add_cog(QACog(bot))
    except Exception as e:
        print(f"❌ Fout bij het laden van QACog: {e}")

@bot.event
async def on_command_error(ctx, error):
    """Afhandeling van commando-fouten."""
    
    # Belangrijk: De CheckFailure wordt genegeerd omdat de cog_check al een waarschuwing stuurt.
    if isinstance(error, commands.CheckFailure):
        return

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
    
    # Log overige fouten
    print(f"Fout opgetreden: {error}")

# --- Start het bot programma ---
if __name__ == '__main__':
    if not TOKEN:
        print("\nFATALE FOUT: Omgevingsvariabele 'DISCORD_TOKEN' niet gevonden.")
        sys.exit(1)
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("\nFATALE FOUT: De Discord Token is ongeldig. Controleer uw 'DISCORD_TOKEN' omgevingsvariabele.")
        sys.exit(1)
    except Exception as e:
        print(f"Een onbekende fout is opgetreden: {e}")
        sys.exit(1)
