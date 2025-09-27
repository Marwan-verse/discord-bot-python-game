# Python 3.10+
# pip install -U discord.py

import os
import random
import asyncio
import discord
from discord import app_commands
from discord.ui import View, Button, Select
from discord.ext import commands

# =========================
# Categories (EN & AR)
# =========================

FOODS_EN = ["bread", "egg", "cheese", "yogurt", "waffle", "pumpkin", "candy", "honey", "soup", "salad"]
ANIMALS_EN = ["dog", "elephant", "kangaroo", "tiger", "wolf", "yak", "zebra", "owl", "panda", "dolphin"]
FRUITS_EN = ["apple", "banana", "lemon", "grape", "orange", "mango", "olive", "peach", "pear", "apricot"]
PLACES_EN = ["beach", "castle", "garden", "opera", "zoo", "school", "museum", "market", "station", "hotel"]
OBJECTS_EN = ["car", "guitar", "house", "notebook", "piano", "camera", "diamond", "mirror", "lamp", "robot"]
CLOTHES_EN = ["jacket", "hat", "jeans", "apron", "uniform", "scarf", "glove", "mask", "skirt", "shirt"]
NATURE_EN = ["mountain", "river", "ocean", "island", "forest", "hill", "valley", "desert", "reef", "grove"]
JOBS_EN = ["engineer", "queen", "viking", "pirate", "artist", "doctor", "pilot", "chef", "teacher", "farmer"]

FOODS_AR = ["خبز", "بيضة", "جبن", "زبادي", "وافل", "يقطين", "حلوى", "عسل", "شوربة", "سلطة"]
ANIMALS_AR = ["كلب", "فيل", "كنغر", "نمر", "ذئب", "ياك", "حمار وحشي", "بومة", "باندا", "دلفين"]
FRUITS_AR = ["تفاحة", "موز", "ليمون", "عنب", "برتقال", "مانجو", "زيتون", "خوخ", "كمثرى", "مشمش"]
PLACES_AR = ["شاطئ", "قلعة", "حديقة", "أوبرا", "حديقة حيوان", "مدرسة", "متحف", "سوق", "محطة", "فندق"]
OBJECTS_AR = ["سيارة", "جيتار", "منزل", "دفتر", "بيانو", "كاميرا", "ألماس", "مرآة", "مصباح", "روبوت"]
CLOTHES_AR = ["سترة", "قبعة", "جينز", "مريول", "زي رسمي", "وشاح", "قفاز", "قناع", "تنورة", "قميص"]
NATURE_AR = ["جبل", "نهر", "محيط", "جزيرة", "غابة", "تل", "وادي", "صحراء", "شعاب مرجانية", "بستان"]
JOBS_AR = ["مهندس", "ملكة", "فايكنج", "قرصان", "فنان", "طبيب", "طيار", "طباخ", "معلم", "مزارع"]

CATEGORIES_EN = {
    "Foods": FOODS_EN, "Animals": ANIMALS_EN, "Fruits": FRUITS_EN, "Places": PLACES_EN,
    "Objects": OBJECTS_EN, "Clothes": CLOTHES_EN, "Nature": NATURE_EN, "Jobs": JOBS_EN
}
CATEGORIES_AR = {
    "طعام": FOODS_AR, "حيوانات": ANIMALS_AR, "فاكهة": FRUITS_AR, "أماكن": PLACES_AR,
    "أشياء": OBJECTS_AR, "ملابس": CLOTHES_AR, "طبيعة": NATURE_AR, "وظائف": JOBS_AR
}

# =========================
# Bot & Intents
# =========================

intents = discord.Intents.default()
intents.guilds = True
intents.members = True       # needed for voice members & DMs
intents.message_content = False
intents.reactions = True
intents.messages = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# =========================
# Shared round state
# =========================

# Keeps lightweight state per guild for utility/status
round_state: dict[int, dict] = {}

# =========================
# Utilities
# =========================

async def get_voice_players(channel: discord.VoiceChannel):
    return [m for m in channel.members if not m.bot]

async def get_react_players(guild: discord.Guild, channel: discord.TextChannel, message_id: int, emoji: str):
    msg = await channel.fetch_message(message_id)
    target_reaction = None
    for r in msg.reactions:
        if str(r.emoji) == emoji:
            target_reaction = r
            break
    if not target_reaction:
        raise ValueError("No matching reaction found on that message.")

    users = []
    async for u in target_reaction.users():
        if not u.bot:
            member = guild.get_member(u.id)
            if member:
                users.append(member)
    # dedupe
    return list({m.id: m for m in users}.values())

# =========================
# Slash command: start_wordgame (blank + random starter)
# =========================

@tree.command(name="start_wordgame", description="DM a word to players (voice or reactors), pick one blank, and choose a random starter.")
@app_commands.describe(
    word="The secret word to DM (everyone except the blank)",
    source="Where to collect players from: voice or react",
    voice_channel="Voice channel (required if source=voice)",
    text_channel="Text channel that has the reaction message (required if source=react)",
    react_message_id="Message ID that players reacted to (required if source=react)",
    react_emoji="The exact emoji to collect (e.g., 😀 or <:name:1234567890>) (required if source=react)",
    exclude_host="Exclude the command invoker from the round"
)
@app_commands.choices(source=[
    app_commands.Choice(name="voice", value="voice"),
    app_commands.Choice(name="react", value="react")
])
async def start_wordgame(
    interaction: discord.Interaction,
    word: str,
    source: app_commands.Choice[str],
    voice_channel: discord.VoiceChannel | None = None,
    text_channel: discord.TextChannel | None = None,
    react_message_id: str | None = None,
    react_emoji: str | None = None,
    exclude_host: bool = False
):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    if not guild:
        return await interaction.followup.send("Use this in a server.", ephemeral=True)

    try:
        if source.value == "voice":
            if not voice_channel:
                return await interaction.followup.send("Provide voice_channel when source=voice.", ephemeral=True)
            players = await get_voice_players(voice_channel)
        else:
            if not (text_channel and react_message_id and react_emoji):
                return await interaction.followup.send("Provide text_channel, react_message_id, and react_emoji when source=react.", ephemeral=True)
            try:
                mid = int(react_message_id)
            except ValueError:
                return await interaction.followup.send("react_message_id must be numeric.", ephemeral=True)
            players = await get_react_players(guild, text_channel, mid, react_emoji)

        if exclude_host:
            players = [p for p in players if p.id != interaction.user.id]

        players = list({p.id: p for p in players if not p.bot}.values())
        if len(players) < 3:
            return await interaction.followup.send(f"Need at least 3 human players; got {len(players)}.", ephemeral=True)

        blank_player = random.choice(players)
        starter = random.choice(players)

        sent_ok, failures = 0, []
        for member in players:
            try:
                if member == blank_player:
                    await member.send("You received NO WORD. Try to blend in. 🙂")
                else:
                    await member.send(f"Your word is: **{word}**\nGive short, non-obvious clues.")
                sent_ok += 1
            except (discord.Forbidden, discord.HTTPException):
                failures.append(member.display_name)

        round_state[guild.id] = {
            "mode": "blank",
            "word": word,
            "players": [p.id for p in players],
            "blank": blank_player.id,
            "starter": starter.id,
            "channel_id": interaction.channel_id,
        }

        # Public announce
        channel = interaction.channel
        if isinstance(channel, (discord.TextChannel, discord.Thread, discord.ForumChannel)):
            await channel.send(
                "🎲 **Word game started!**\n"
                f"- DMs sent to **{sent_ok}** players"
                f"{' (DMs disabled: ' + ', '.join(failures) + ')' if failures else ''}.\n"
                f"- One random player received **no word**.\n"
                f"- **{starter.mention}** goes first — please post a short, subtle clue!"
            )

        await interaction.followup.send("Round set up. Have fun!", ephemeral=True)

    except ValueError as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)
    except Exception:
        await interaction.followup.send("Something went wrong setting up the round.", ephemeral=True)

# =========================
# Slash command: wordgame_status
# =========================

@tree.command(name="wordgame_status", description="Show current round info (ephemeral).")
async def wordgame_status(interaction: discord.Interaction):
    data = round_state.get(interaction.guild_id)
    if not data:
        return await interaction.response.send_message("No active round.", ephemeral=True)

    guild = interaction.guild
    blank = guild.get_member(data.get("blank", 0)) if data.get("mode") == "blank" else None
    starter = guild.get_member(data["starter"]) if data.get("starter") else None
    word = data.get("word", "—")
    mode = data.get("mode", "—")

    msg = f"Mode: {mode}\nWord: {word}\nPlayers: {len(data.get('players', []))}\n"
    if blank:
        msg += f"Blank: {blank.display_name}\n"
    if starter:
        msg += f"Starter: {starter.display_name}"
    await interaction.response.send_message(msg, ephemeral=True)

# =========================
# UI View: Imposter (your flow)
# =========================

class ImposterGameView(View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=120)
        self.players: set[discord.Member] = {author}
        self.language = 'english'
        self.started = False
        self.word = None
        self.category = None
        self.author_id = author.id

    @discord.ui.button(label="Join", style=discord.ButtonStyle.primary, custom_id="join_btn")
    async def join(self, interaction: discord.Interaction, button: Button):
        if self.started:
            return await interaction.response.send_message("Game already started!", ephemeral=True)
        self.players.add(interaction.user)
        await interaction.response.send_message(f"{interaction.user.mention} joined the game!", ephemeral=True)

    @discord.ui.select(
        placeholder="Select language...",
        options=[
            discord.SelectOption(label="English", value="english", default=True),
            discord.SelectOption(label="Arabic", value="arabic")
        ],
        custom_id="lang_select"
    )
    async def select_language(self, interaction: discord.Interaction, select: Select):
        if self.started:
            return await interaction.response.send_message("Game already started!", ephemeral=True)
        self.language = select.values[0]
        await interaction.response.send_message(f"Language set to {self.language}", ephemeral=True)

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.success, custom_id="start_btn")
    async def start(self, interaction: discord.Interaction, button: Button):
        if self.started:
            return await interaction.response.send_message("Game already started!", ephemeral=True)
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("Only the host can start.", ephemeral=True)
        if len(self.players) < 2:
            return await interaction.response.send_message("Need at least 2 players!", ephemeral=True)

        self.started = True
        lang = self.language
        categories = CATEGORIES_AR if lang == 'arabic' else CATEGORIES_EN
        self.category = random.choice(list(categories.keys()))
        self.word = random.choice(categories[self.category])

        # Pick the spy (gets only category) and make the spy start, per your version
        spy = random.choice(list(self.players))

        sent_ok, failures = 0, []
        for player in self.players:
            try:
                if player == spy:
                    content = (f"أنت الجاسوس! التصنيف: {self.category}"
                               if lang == 'arabic'
                               else f"You are the spy! The category is: {self.category}")
                else:
                    content = (f"الكلمة السرية هي: {self.word}\nالتصنيف: {self.category}"
                               if lang == 'arabic'
                               else f"The secret word is: {self.word}\nCategory: {self.category}")
                await player.send(content)
                sent_ok += 1
            except (discord.Forbidden, discord.HTTPException):
                failures.append(player.display_name)

        # Save state for status/debug
        guild = interaction.guild
        if guild:
            round_state[guild.id] = {
                "mode": "imposter",
                "word": self.word,
                "category": self.category,
                "players": [p.id for p in self.players],
                "spy": spy.id,
                "starter": spy.id,
                "channel_id": interaction.channel_id,
            }

        announce = (
            f"{spy.mention} يبدأ! أعطِ دليلاً للكلمة."
            if lang == 'arabic'
            else f"{spy.mention} is chosen to start! Give a clue for the word."
        )
        extra = (f"\n(لم أستطع إرسال رسالة خاصة إلى: {', '.join(failures)})" if failures and lang == 'arabic'
                 else f"\n(I couldn't DM: {', '.join(failures)})" if failures else "")
        try:
            await interaction.response.edit_message(content=announce + extra, view=None)
        except discord.HTTPException:
            # Fallback: send a fresh message in channel
            if interaction.channel:
                await interaction.channel.send(announce + extra)

# =========================
# Slash command: /play (your entry point)
# =========================

@tree.command(name="play", description="Play a party game!")
@app_commands.describe(game="Game to play (currently only 'imposter' supported)")
async def play(interaction: discord.Interaction, game: str):
    if game.lower() != "imposter":
        return await interaction.response.send_message("Only 'imposter' is supported right now.", ephemeral=True)
    embed = discord.Embed(title="Imposter Game", description="Click **Join** to participate.\nSelect language, then the host clicks **Start Game**.")
    view = ImposterGameView(interaction.user)
    await interaction.response.send_message(embed=embed, view=view)

# =========================
# Bot ready & run
# =========================

@bot.event
async def on_ready():
    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print("Failed to sync commands:", e)
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

# ----
# Run with your token:
# os.environ["DISCORD_TOKEN"] = "YOUR_TOKEN_HERE"
# bot.run(os.environ["DISCORD_TOKEN"])
bot.run("")  # <--- put your token here or use env var above
