import interactions
from interactions import Intents, StringSelectMenu, slash_command, slash_option, SlashContext, listen, Modal, ShortText
from interactions.models import Activity, ActivityType
from interactions.api.events import Component
import requests
from datetime import datetime, timezone

#? maybe one generic command in the future for stats. user selects what they want via a dropdown and then a from appears asking them who they want to look up.

bot = interactions.Client(intents=Intents.DEFAULT)

SCOPES = [559722123644633089, 803639880391065623, 1126063813192597545]
# SCOPES = [803639880391065623]

class EMBED_COLORS:
    PRIMARY = 0x7289da
    ERROR = 0xff0000
#* Andrew, use this! Instead of defining colors per embed, it's centralised so it's easier changed. Example:
# embed = interactions.Embed(color=EMBED_COLORS.PRIMARY, title="foo", description="bar") 

TIMEOUT_EMBED = interactions.Embed(color=EMBED_COLORS.ERROR, title="Timeout", description="This action timed out. Please run the command again.")

#* generic functions
def unix_time():
    """Returns a unix timestamp in UTC."""
    return datetime.now(timezone.utc)

#* whatever the bot does 

USERNAME_MODAL = Modal(
    ShortText(label="Username:", custom_id="username", placeholder="LuckUnstoppable7", required=True),
    title="Enter a username",
    custom_id=f"username_input_{unix_time()}"
)

@listen()
async def on_ready():
    print("Ready")
    print(f"This bot is owned by {bot.owner}")
    await bot.change_presence(activity=Activity(type=ActivityType.WATCHING, name="your statistics"))

# command for server stats
@slash_command(
    name="stats",
    description="Get stats about something",
    scopes=SCOPES,
    sub_cmd_name="fancy_generic",
    sub_cmd_description="Lookup a player in the API and view their data",
    #? If this will be the primary command, there won't be any need for subcommands? 

)
async def stats_function(ctx: SlashContext):
    await ctx.send_modal(modal=USERNAME_MODAL)
    modal_ctx: interactions.ModalContext = await ctx.client.wait_for_modal(USERNAME_MODAL)

    USERNAME = modal_ctx.responses["username"]
    api_url = f"https://mcapi.lu7.io/player/{USERNAME}"

    select = StringSelectMenu(
		interactions.StringSelectOption(label="Generic info", value="stat_player_generic", description="Info about online status, UUID, etc."),
		interactions.StringSelectOption(label="Info about plots", value="stat_player_plots", description="Get some info on the plot(s) this player owns"),
        # add myserty dust
		custom_id=f"stat_menu_{unix_time()}",
		placeholder="What stat would you like to lookup?",
		min_values=1,
		max_values=1,
	)
    msg = await modal_ctx.send(components=select)

    try:
        select_ctx: interactions.ComponentContext = await modal_ctx.client.wait_for_component(components=select, timeout=30)
    except TimeoutError:
        select.disabled = True
        await ctx.edit(msg, embed=TIMEOUT_EMBED, components=select)
        return
    
    select_ctx = select_ctx.ctx
    
    chosen_option = select_ctx.values[0]
    print(chosen_option)

    await select_ctx.defer(edit_origin=True)

    try:
        response = requests.get(api_url)
    except requests.RequestException as e:
        embed = interactions.Embed(
            color=EMBED_COLORS.ERROR,
            description="An error occurred while connecting to the API.",
            timestamp=unix_time()
        )
        await select_ctx.edit_origin(embeds=[embed], components=[])
        return
    
    if response.status_code == 404:
        embed = interactions.Embed(
            color=EMBED_COLORS.ERROR,
            description="Player not found or not online.",
            timestamp=unix_time()
        )
        await select_ctx.edit_origin(embeds=[embed])
    elif response.status_code != 200:
        await select_ctx.edit_origin(content=f"Error: {response.status_code}", embeds=[], components=[])

    data = response.json()
    embed_title = f":bust_in_silhouette: Player Info: {data['name']}"
    embed_description = ""
    embed = interactions.Embed(
        color=EMBED_COLORS.PRIMARY,
        title=embed_title,
        timestamp=unix_time()
    )

    if chosen_option == "stat_player_generic":     
        if 'online' in data:
            embed.add_field(name="Online:", value=f"💻 {data['online']}", inline=True)
        if 'uuid' in data:
            embed.add_field(name="UUID:", value=f"🔑 {data['uuid']}", inline=True)
        if 'health' in data and 'maxHealth' in data:
            embed.add_field(name="Health:", value=f"❤️ {data['health']}/{data['maxHealth']}", inline=True)
        if 'foodLevel' in data:
            embed.add_field(name="Food Level:", value=f"🍔 {data['foodLevel']}", inline=True)
        if 'xp' in data:
            embed.add_field(name="Experience:", value=f"⚔️ {data['xp']}", inline=True)
        if 'totalExperience' in data:
            embed.add_field(name="Total Experience:", value=f"🏅 {data['totalExperience']}", inline=True)
        if 'expToLevel' in data:
            embed.add_field(name="Experience to Level:", value=f"📈 {data['expToLevel']}", inline=True)
        if 'gamemode' in data:
            embed.add_field(name="Game Mode:", value=f"🎮 {data['gamemode']}", inline=True)
        if 'location' in data:
            embed.add_field(name="Location:", value=f"🗺️ {data['location']}", inline=True)
        if 'statistics' in data:
            statistics_str = "\n".join([f"{key.replace('_', ' ').title()}: {value}" for key, value in data['statistics'].items()])
            embed_description += f"\n**Statistics:**\n{statistics_str}"
        
        if 'uuid' in data:
            embed.set_thumbnail(url=f"http://cravatar.eu/helmavatar/{data['uuid']}/128.png")

        embed.description = embed_description.strip()
        await select_ctx.edit_origin(embeds=[embed], content=None, components=[])
    elif chosen_option == "stat_player_plots":
        if 'plotCount' in data:
            embed.add_field(name="Plots Owned:", value=f"🔢 {data['plotCount']}", inline=True)
        if 'plots' in data:
            embed.add_field(name="Owned Plot IDs:", value=f"🗺️ {data['plots']}", inline=True)
        
        if 'uuid' in data:
            embed.set_thumbnail(url=f"http://cravatar.eu/helmavatar/{data['uuid']}/128.png")

        embed.description = embed_description.strip()
        await select_ctx.edit_origin(embeds=[embed], content=None, components=[])

@stats_function.subcommand(
    sub_cmd_name="player",
    sub_cmd_description="Lookup a player in the API and view their data",
)
@slash_option(
    name="playername", 
    description="Name of the player to look up", 
    opt_type=interactions.OptionType.STRING, 
    required=True)
async def player_info(ctx: SlashContext, playername: str):
    api_url = f"https://mcapi.lu7.io/player/{playername}"
    await ctx.defer()
    
    try:
        response = requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()
            
            embed_title = f":bust_in_silhouette: Player Info: {data['name']}"
            embed_description = ""
            
            embed = interactions.Embed(
                color=EMBED_COLORS.PRIMARY,
                title=embed_title,
                timestamp=datetime.now(timezone.utc)
            )
            
            if 'online' in data:
                embed.add_field(name="Online:", value=f"💻 {data['online']}", inline=True)
            if 'uuid' in data:
                embed.add_field(name="UUID:", value=f"🔑 {data['uuid']}", inline=True)
            if 'plotCount' in data:
                embed.add_field(name="Plots Owned:", value=f"🔢 {data['plotCount']}", inline=True)
            if 'plots' in data:
                embed.add_field(name="Owned Plot IDs:", value=f"🗺️ {data['plots']}", inline=True)
            if 'health' in data and 'maxHealth' in data:
                embed.add_field(name="Health:", value=f"❤️ {data['health']}/{data['maxHealth']}", inline=True)
            if 'foodLevel' in data:
                embed.add_field(name="Food Level:", value=f"🍔 {data['foodLevel']}", inline=True)
            if 'xp' in data:
                embed.add_field(name="Experience:", value=f"⚔️ {data['xp']}", inline=True)
            if 'totalExperience' in data:
                embed.add_field(name="Total Experience:", value=f"🏅 {data['totalExperience']}", inline=True)
            if 'expToLevel' in data:
                embed.add_field(name="Experience to Level:", value=f"📈 {data['expToLevel']}", inline=True)
            if 'gamemode' in data:
                embed.add_field(name="Game Mode:", value=f"🎮 {data['gamemode']}", inline=True)
            if 'location' in data:
                embed.add_field(name="Location:", value=f"🗺️ {data['location']}", inline=True)
            if 'statistics' in data:
                statistics_str = "\n".join([f"{key.replace('_', ' ').title()}: {value}" for key, value in data['statistics'].items()])
                embed_description += f"\n**Statistics:**\n{statistics_str}"
            
            if 'uuid' in data:
                embed.set_thumbnail(url=f"http://cravatar.eu/helmavatar/{data['uuid']}/128.png")

            embed.description = embed_description.strip()
            await ctx.send(embeds=[embed], content=None)
        elif response.status_code == 404:
            # error happened, return error message
            embed = interactions.Embed(
                color=EMBED_COLORS.ERROR,
                description="Player not found or not online.",
                timestamp=unix_time()
            )
            await ctx.send(embeds=[embed])
        else:
            await ctx.send(f"Error: {response.status_code}")
    
    except requests.RequestException as e:
        embed = interactions.Embed(
            color=EMBED_COLORS.ERROR,
            description="An error occurred while connecting to the API.",
            timestamp=unix_time()
        )
        await ctx.send(embeds=[embed])



bot.start("YOUR-TOKEN-HERE")
#* ^ bot token 
