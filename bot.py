import discord
import random
from discord import app_commands
from discord.ui import View, Button, Select

# Array of 200 words for the game

# English and Arabic word lists
ENGLISH_WORDS = [
    "apple", "banana", "car", "dog", "elephant", "flower", "guitar", "house", "island", "jungle",
    "kangaroo", "lemon", "mountain", "notebook", "ocean", "piano", "queen", "river", "sun", "tree",
    "umbrella", "violin", "window", "xylophone", "yacht", "zebra", "airplane", "balloon", "camera", "diamond",
    "engine", "forest", "garden", "hat", "ice", "jacket", "kite", "lamp", "mirror", "necklace",
    "orange", "pencil", "quilt", "robot", "star", "train", "unicorn", "vase", "whale", "x-ray",
    "yogurt", "zipper", "anchor", "bridge", "castle", "drum", "eagle", "fan", "glove", "hammer",
    "igloo", "jewel", "key", "ladder", "magnet", "needle", "owl", "pumpkin", "quartz", "rocket",
    "sail", "tiger", "urn", "volcano", "wheel", "xenon", "yarn", "zeppelin", "ant", "bread",
    "cloud", "desk", "egg", "flag", "grape", "hill", "ink", "jeans", "kettle", "leaf",
    "moon", "nest", "octopus", "pearl", "quiver", "rose", "ship", "table", "uniform", "vulture",
    "wolf", "xmas", "yak", "zoo", "arch", "beach", "circle", "dolphin", "earth", "feather",
    "gate", "horn", "iron", "jungle", "knee", "lake", "mask", "net", "opera", "parrot",
    "quokka", "ring", "swan", "tower", "urchin", "valley", "wand", "xenops", "yeti", "zucchini",
    "apron", "bottle", "candle", "daisy", "engineer", "fence", "globe", "harp", "igloo", "jacket",
    "koala", "lizard", "mango", "needle", "olive", "panda", "quokka", "raven", "scooter", "tulip",
    "urn", "viking", "waffle", "xylophonist", "yawn", "zeppelin", "atlas", "bison", "cactus", "dune",
    "ember", "fjord", "grove", "heron", "iris", "jigsaw", "kelp", "lighthouse", "mantis", "nectar",
    "onyx", "plaza", "quartzite", "reef", "sphinx", "trumpet", "utensil", "vine", "wombat", "xerox",
    "yodel", "zenith"
]

ARABIC_WORDS = [
    "تفاحة", "موز", "سيارة", "كلب", "فيل", "زهرة", "جيتار", "منزل", "جزيرة", "غابة",
    "كنغر", "ليمون", "جبل", "دفتر", "محيط", "بيانو", "ملكة", "نهر", "شمس", "شجرة",
    "مظلة", "كمان", "نافذة", "إكسليفون", "يخت", "حمار وحشي", "طائرة", "بالون", "كاميرا", "ألماس",
    "محرك", "غابة", "حديقة", "قبعة", "ثلج", "سترة", "طائرة ورقية", "مصباح", "مرآة", "قلادة",
    "برتقال", "قلم رصاص", "لحاف", "روبوت", "نجمة", "قطار", "يونيكورن", "مزهرية", "حوت", "أشعة سينية",
    "زبادي", "سحاب", "مرساة", "جسر", "قلعة", "طبلة", "نسر", "مروحة", "قفاز", "مطرقة",
    "إيغلو", "جوهرة", "مفتاح", "سلم", "مغناطيس", "إبرة", "بومة", "يقطين", "كوارتز", "صاروخ",
    "شراع", "نمر", "جرة", "بركان", "عجلة", "زينون", "خيط", "منطاد", "نملة", "خبز",
    "سحابة", "مكتب", "بيضة", "علم", "عنب", "تل", "حبر", "جينز", "غلاية", "ورقة",
    "قمر", "عش", "أخطبوط", "لؤلؤة", "جعبة", "وردة", "سفينة", "طاولة", "زي رسمي", "نسر",
    "ذئب", "عيد الميلاد", "ياك", "حديقة حيوان", "قوس", "شاطئ", "دائرة", "دلفين", "أرض", "ريشة",
    "بوابة", "بوق", "حديد", "أدغال", "ركبة", "بحيرة", "قناع", "شبكة", "أوبرا", "ببغاء"
    # ... add more Arabic words as needed ...
]
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
        word_list = ARABIC_WORDS if lang == 'arabic' else ENGLISH_WORDS
        self.word = random.choice(word_list)
        spy = random.choice(list(self.players))
        for player in self.players:
            try:
                if player == spy:
                    await player.send("أنت الجاسوس! حاول تخمين الكلمة من الأدلة." if lang == 'arabic' else "You are the spy! Try to guess the word from clues.")
                else:
                    await player.send(f"الكلمة السرية هي: {self.word}" if lang == 'arabic' else f"The secret word is: {self.word}")
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
