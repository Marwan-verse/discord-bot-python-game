import discord
import random
from discord import app_commands
from discord.ui import View, Button, Select

# Array of 200 words for the game



# English word categories
FOODS_EN = ["bread", "egg", "cheese", "yogurt", "waffle", "pumpkin", "candy", "honey", "soup", "salad"]
ANIMALS_EN = ["dog", "elephant", "kangaroo", "tiger", "wolf", "yak", "zebra", "owl", "panda", "dolphin"]
FRUITS_EN = ["apple", "banana", "lemon", "grape", "orange", "mango", "olive", "peach", "pear", "apricot"]
PLACES_EN = ["beach", "castle", "garden", "opera", "zoo", "school", "museum", "market", "station", "hotel"]
OBJECTS_EN = ["car", "guitar", "house", "notebook", "piano", "camera", "diamond", "mirror", "lamp", "robot"]
CLOTHES_EN = ["jacket", "hat", "jeans", "apron", "uniform", "scarf", "glove", "mask", "skirt", "shirt"]
NATURE_EN = ["mountain", "river", "ocean", "island", "forest", "hill", "valley", "desert", "reef", "grove"]
JOBS_EN = ["engineer", "queen", "viking", "pirate", "artist", "doctor", "pilot", "chef", "teacher", "farmer"]

# Arabic word categories
FOODS_AR = ["خبز", "بيضة", "جبن", "زبادي", "وافل", "يقطين", "حلوى", "عسل", "شوربة", "سلطة"]
ANIMALS_AR = ["كلب", "فيل", "كنغر", "نمر", "ذئب", "ياك", "حمار وحشي", "بومة", "باندا", "دلفين"]
FRUITS_AR = ["تفاحة", "موز", "ليمون", "عنب", "برتقال", "مانجو", "زيتون", "خوخ", "كمثرى", "مشمش"]
PLACES_AR = ["شاطئ", "قلعة", "حديقة", "أوبرا", "حديقة حيوان", "مدرسة", "متحف", "سوق", "محطة", "فندق"]
OBJECTS_AR = ["سيارة", "جيتار", "منزل", "دفتر", "بيانو", "كاميرا", "ألماس", "مرآة", "مصباح", "روبوت"]
CLOTHES_AR = ["سترة", "قبعة", "جينز", "مريول", "زي رسمي", "وشاح", "قفاز", "قناع", "تنورة", "قميص"]
NATURE_AR = ["جبل", "نهر", "محيط", "جزيرة", "غابة", "تل", "وادي", "صحراء", "شعاب مرجانية", "بستان"]
JOBS_AR = ["مهندس", "ملكة", "فايكنج", "قرصان", "فنان", "طبيب", "طيار", "طباخ", "معلم", "مزارع"]

# Category mapping for random selection and display
CATEGORIES_EN = {
    "Foods": FOODS_EN,
    "Animals": ANIMALS_EN,
    "Fruits": FRUITS_EN,
    "Places": PLACES_EN,
    "Objects": OBJECTS_EN,
    "Clothes": CLOTHES_EN,
    "Nature": NATURE_EN,
    "Jobs": JOBS_EN
}
CATEGORIES_AR = {
    "طعام": FOODS_AR,
    "حيوانات": ANIMALS_AR,
    "فاكهة": FRUITS_AR,
    "أماكن": PLACES_AR,
    "أشياء": OBJECTS_AR,
    "ملابس": CLOTHES_AR,
    "طبيعة": NATURE_AR,
    "وظائف": JOBS_AR
}
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree


# Helper to get members in a voice channel
def get_voice_members(interaction):
    if interaction.user.voice and interaction.user.voice.channel:
        return [member for member in interaction.user.voice.channel.members if not member.bot]
    else:
        return []

# UI View for joining and language selection
class ImposterGameView(View):
    def __init__(self, author):
        super().__init__(timeout=120)
        self.players = set([author])
        self.language = 'english'
        self.started = False
        self.word = None
    @discord.ui.button(label="Join", style=discord.ButtonStyle.primary, custom_id="join_btn")
    async def join(self, interaction: discord.Interaction, button: Button):
        if self.started:
            await interaction.response.send_message("Game already started!", ephemeral=True)
            return
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
        self.language = select.values[0]
        await interaction.response.send_message(f"Language set to {self.language}", ephemeral=True)

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.success, custom_id="start_btn")
    async def start(self, interaction: discord.Interaction, button: Button):
        if self.started:
            await interaction.response.send_message("Game already started!", ephemeral=True)
            return
        if len(self.players) < 2:
            await interaction.response.send_message("Need at least 2 players!", ephemeral=True)
            return
        self.started = True
        lang = self.language
        if lang == 'arabic':
            categories = CATEGORIES_AR
        else:
            categories = CATEGORIES_EN
        category = random.choice(list(categories.keys()))
        word = random.choice(categories[category])
        self.word = word
        self.category = category
        spy = random.choice(list(self.players))
        for player in self.players:
            try:
                if player == spy:
                    await player.send((f"أنت الجاسوس! التصنيف: {category}" if lang == 'arabic' else f"You are the spy! The category is: {category}"))
                else:
                    await player.send((f"الكلمة السرية هي: {word}\nالتصنيف: {category}" if lang == 'arabic' else f"The secret word is: {word}\nCategory: {category}"))
            except Exception:
                pass
        await interaction.response.edit_message(content=(f"{spy.mention} يبدأ! أعطِ دليلاً للكلمة." if lang == 'arabic' else f"{spy.mention} is chosen to start! Give a clue for the word."), view=None)



# Slash command: /play imposter
@tree.command(name="play", description="Play a party game!")
@app_commands.describe(game="Game to play (currently only imposter supported)")
async def play(interaction: discord.Interaction, game: str):
    if game.lower() != "imposter":
        await interaction.response.send_message("Only 'imposter' is supported right now.", ephemeral=True)
        return
    embed = discord.Embed(title="Imposter Game", description="Click Join to participate! Select language and Start when ready.")
    view = ImposterGameView(interaction.user)
    await interaction.response.send_message(embed=embed, view=view)

# Command to start the game for users who reacted to a message


# (Optional) You can add more slash commands for other game modes here


# Sync commands and run the bot
@bot.event
async def on_ready():
    try:
        await tree.sync()
        print(f"Synced slash commands for {bot.user}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

bot.run('YOUR_BOT_TOKEN')
