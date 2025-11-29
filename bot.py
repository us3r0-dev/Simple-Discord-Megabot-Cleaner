import json
import re
import discord
from discord.ext import commands
from fastapi import FastAPI
import uvicorn
import threading

# Load config
def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def save_config(cfg):
    with open("config.json", "w") as f:
        json.dump(cfg, f, indent=2)

config = load_config()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def user_is_protected(member):
    return any(role.id in config["protected_role_ids"] for role in member.roles)

def matches_pattern(text):
    for p in config["banned_patterns"]:
        if re.search(p, text, re.IGNORECASE):
            return True
    return False

@bot.event
async def on_message(msg):
    if msg.author.bot:
        return

    member = msg.author

    if user_is_protected(member):
        return

    trap_id = config["trap_channel_id"]

    if msg.channel.id == trap_id:
        await member.ban(reason="Posted in trap channel")
        return

    if matches_pattern(msg.content):
        await member.ban(reason="Matched banned pattern")
        await msg.delete()
        return

    await bot.process_commands(msg)

# Web interface
app = FastAPI()

@app.get("/config")
def get_cfg():
    return config

@app.post("/add_pattern")
def add_pattern(p: str):
    config["banned_patterns"].append(p)
    save_config(config)
    return {"ok": True}

@app.post("/remove_pattern")
def remove_pattern(p: str):
    config["banned_patterns"] = [x for x in config["banned_patterns"] if x != p]
    save_config(config)
    return {"ok": True}

@app.post("/add_protected_role")
def add_role(role_id: int):
    config["protected_role_ids"].append(role_id)
    save_config(config)
    return {"ok": True}

@app.post("/set_trap_channel")
def set_trap(cid: int):
    config["trap_channel_id"] = cid
    save_config(config)
    return {"ok": True}

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8080)

threading.Thread(target=run_api).start()

bot.run("YOUR_DISCORD_BOT_TOKEN")
