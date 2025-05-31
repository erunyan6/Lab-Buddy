import discord
import re

# Replace with your real bot token
TOKEN = "MTM3ODE1NTQ0MTg5NjQyMzQ0NA.GXXKDc.x_kDXQH2vgRUZj-8tI-7IgZhxTvYa_Koa1RxZ8"

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ========== Dilution Calculation ==========

def calculate_dilution(c1, v1, c2, v2):
    try:
        var_group_1 = (c1, v1)
        var_group_2 = (c2, v2)

        unknown_count = sum(1 for val in (c1, v1, c2, v2) if isinstance(val, str))
        if unknown_count == 0:
            raise ValueError("No unknown value provided. One input must be 'unknown'.")
        elif unknown_count > 1:
            raise ValueError("Too many unknowns. Only one input can be unknown.")

        top = None
        bottom = None

        for group in (var_group_1, var_group_2):
            if all(isinstance(x, float) for x in group):
                top = group[0] * group[1]
            elif any(isinstance(x, str) for x in group):
                bottom = next((x for x in group if isinstance(x, float)), None)

        if top is None or bottom is None:
            raise ValueError("Invalid group configuration.")
        if bottom == 0:
            raise ZeroDivisionError("Cannot divide by zero.")

        return {"success": True, "result": round(top / bottom, 3)}

    except (ValueError, ZeroDivisionError) as e:
        return {"success": False, "error": str(e), "result": None}


def postprocess_dilution(inputs, calculated_value):
    var_group = [inputs["c1"], inputs["v1"], inputs["c2"], inputs["v2"]]
    if any(isinstance(val, str) for val in var_group):
        for i, val in enumerate(var_group):
            if isinstance(val, str):
                var_group[i] = calculated_value
                break
    c1, v1, c2, v2 = var_group

    if c1 < c2 - 0.0001:
        raise ValueError("Final concentration must be less than starting concentration.")
    if v1 >= v2:
        raise ValueError("Final volume must be greater than starting volume.")

    return {
        "C1": round(c1, 3),
        "V1": round(v1, 3),
        "C2": round(c2, 3),
        "V2": round(v2, 3)
    }


# ========== Input Parsing ==========

def parse_inputs(text):
    pattern = r"(\w+)=([\w.]+)"
    matches = dict(re.findall(pattern, text.lower()))
    values = {}
    for key in ("c1", "v1", "c2", "v2"):
        val = matches.get(key)
        if val is None or val == "unknown":
            values[key] = "unknown"
        else:
            try:
                values[key] = float(val)
            except ValueError:
                values[key] = "unknown"
    return values

# ========== Bot Logic ==========

@client.event
async def on_ready():
    print(f"✅ Bot connected as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.lower().startswith("!dilute"):
        inputs = parse_inputs(message.content)
        result = calculate_dilution(inputs["c1"], inputs["v1"], inputs["c2"], inputs["v2"])

        if not result["success"]:
            await message.channel.send(f"⚠️ Error: {result['error']}")
            return

        try:
            final_result = postprocess_dilution(inputs, result["result"])
            response = "\n".join(f"**{k}** = {v}" for k, v in final_result.items())
            await message.channel.send(f"🧪 Final result:\n{response}")
        except ValueError as e:
            await message.channel.send(f"⚠️ Error: {str(e)}")

# ========== Run Bot ==========
client.run(TOKEN)
