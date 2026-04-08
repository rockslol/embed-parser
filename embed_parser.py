import random
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import discord


async def replace_variables(
    text: str,
    ctx=None,
    user: discord.User = None,
    guild: discord.Guild = None,
    channel: discord.abc.Messageable = None,
) -> str:
    """Replace basic user, guild, and channel placeholders in text."""
    if not text or "{" not in text:
        return text or ""

    bot = None
    if ctx:
        if hasattr(ctx, "bot"):
            bot = ctx.bot
        elif hasattr(ctx, "client"):
            bot = ctx.client
        else:
            bot = ctx

    user = user or ((getattr(ctx, "author", None) or getattr(ctx, "user", None)) if ctx else None)
    guild = guild or (getattr(ctx, "guild", None) if ctx else None)
    channel = channel or (getattr(ctx, "channel", None) if ctx else None)

    replacements: Dict[str, str] = {}

    if user:
        user_color = getattr(user, "color", None)
        user_color_value = getattr(user_color, "value", 0) if user_color is not None else 0

        replacements.update(
            {
                "{user}": str(user),
                "{user.name}": user.name,
                "{user.display_name}": user.display_name,
                "{user.mention}": user.mention,
                "{user.id}": str(user.id),
                "{user.tag}": user.discriminator if hasattr(user, "discriminator") else "N/A",
                "{user.bot}": "Yes" if user.bot else "No",
                "{user.avatar}": str(user.display_avatar.url),
                "{user.display_avatar}": str(user.display_avatar.url),
                "{user.created_at}": user.created_at.strftime("%B %d, %Y"),
                "{user.created_at_timestamp}": f"<t:{int(user.created_at.timestamp())}>",
                "{user.color}": str(user_color) if user_color is not None else "N/A",
                "{user.color.value}": str(user_color_value),
            }
        )

        if hasattr(user, "joined_at") and user.joined_at:
            replacements.update(
                {
                    "{user.joined_at}": user.joined_at.strftime("%B %d, %Y"),
                    "{user.joined_at_timestamp}": f"<t:{int(user.joined_at.timestamp())}>",
                }
            )

        if hasattr(user, "top_role") and user.top_role:
            replacements.update(
                {
                    "{user.top_role}": str(user.top_role),
                    "{user.top_role.name}": user.top_role.name,
                    "{user.top_role.id}": str(user.top_role.id),
                    "{user.top_role.mention}": user.top_role.mention,
                }
            )

        if hasattr(user, "premium_since") and user.premium_since:
            replacements.update(
                {
                    "{user.premium_since}": user.premium_since.strftime("%B %d, %Y"),
                    "{user.premium_since_timestamp}": f"<t:{int(user.premium_since.timestamp())}>",
                    "{user.boosted}": "Yes",
                }
            )
        else:
            replacements["{user.boosted}"] = "No"

    if guild:
        replacements.update(
            {
                "{guild}": str(guild),
                "{guild.name}": guild.name,
                "{guild.id}": str(guild.id),
                "{guild.icon}": str(guild.icon.url) if guild.icon else "N/A",
                "{guild.count}": str(guild.member_count),
                "{guild.member_count}": str(guild.member_count),
                "{guild.boost_count}": str(guild.premium_subscription_count or 0),
                "{guild.boost_tier}": str(guild.premium_tier),
                "{guild.owner}": str(guild.owner),
                "{guild.owner_id}": str(guild.owner_id),
                "{guild.owner_mention}": guild.owner.mention if guild.owner else "N/A",
                "{guild.created_at}": guild.created_at.strftime("%B %d, %Y"),
                "{guild.created_at_timestamp}": f"<t:{int(guild.created_at.timestamp())}>",
                "{guild.vanity}": guild.vanity_url_code or "N/A",
                "{guild.banner}": str(guild.banner.url) if guild.banner else "N/A",
                "{guild.splash}": str(guild.splash.url) if guild.splash else "N/A",
                "{guild.discovery_splash}": str(guild.discovery_splash.url) if guild.discovery_splash else "N/A",
                "{guild.shard_id}": str(guild.shard_id) if hasattr(guild, "shard_id") else "0",
                "{guild.shard_count}": str(bot.shard_count if bot and hasattr(bot, "shard_count") else 1),
                "{guild.description}": guild.description or "N/A",
                "{guild.preferred_locale}": str(guild.preferred_locale),
                "{guild.role_count}": str(len(guild.roles)),
                "{guild.channel_count}": str(len(guild.channels)),
                "{guild.emoji_count}": str(len(guild.emojis)),
                "{guild.sticker_count}": str(len(getattr(guild, "stickers", []))),
            }
        )

        if channel:
            replacements.update(
                {
                    "{channel}": str(channel),
                    "{channel.name}": getattr(channel, "name", "N/A"),
                    "{channel.mention}": getattr(channel, "mention", "N/A"),
                    "{channel.id}": str(getattr(channel, "id", "N/A")),
                    "{channel.topic}": getattr(channel, "topic", "N/A") or "N/A",
                    "{channel.type}": str(getattr(channel, "type", "N/A")),
                    "{channel.position}": str(getattr(channel, "position", "N/A")),
                }
            )

        if user and ("{user.join_position}" in text or "{user.join_position_suffix}" in text):
            try:
                now = datetime.now()
                members = sorted(guild.members, key=lambda m: m.joined_at or now)
                join_pos = next((i for i, m in enumerate(members, 1) if m.id == user.id), 0)
                if join_pos > 0:
                    replacements["{user.join_position}"] = str(join_pos)
                    suffix = "th" if 11 <= join_pos <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(join_pos % 10, "th")
                    replacements["{user.join_position_suffix}"] = f"{join_pos}{suffix}"
            except Exception:
                replacements["{user.join_position}"] = "N/A"
                replacements["{user.join_position_suffix}"] = "N/A"

    for placeholder, value in replacements.items():
        if placeholder in text:
            text = text.replace(placeholder, str(value))

    return text


def _parse_button_params(params_str: str) -> dict:
    """Parse button parameters from key:value or positional format."""
    parts = [p.strip() for p in params_str.split("&")]

    btn = {
        "label": None,
        "style": discord.ButtonStyle.secondary,
        "url": None,
        "disabled": False,
        "emoji": None,
        "custom_id": None,
    }

    style_map = {
        "primary": discord.ButtonStyle.primary,
        "blurple": discord.ButtonStyle.primary,
        "secondary": discord.ButtonStyle.secondary,
        "grey": discord.ButtonStyle.secondary,
        "gray": discord.ButtonStyle.secondary,
        "success": discord.ButtonStyle.success,
        "green": discord.ButtonStyle.success,
        "danger": discord.ButtonStyle.danger,
        "red": discord.ButtonStyle.danger,
        "link": discord.ButtonStyle.link,
        "url": discord.ButtonStyle.link,
    }

    is_kv = any(
        ":" in part and part.split(":", 1)[0].strip().lower() in ["label", "url", "style", "emoji", "disabled", "id", "custom_id"]
        for part in parts
    )

    if is_kv:
        for part in parts:
            if ":" not in part:
                continue
            k, v = part.split(":", 1)
            k, v = k.strip().lower(), v.strip()
            if k == "label":
                btn["label"] = v
            elif k == "url":
                btn["url"] = v
                btn["style"] = discord.ButtonStyle.link
            elif k == "style":
                btn["style"] = style_map.get(v.lower(), btn["style"])
            elif k == "emoji":
                btn["emoji"] = v
            elif k == "disabled":
                btn["disabled"] = v.lower() in ("true", "yes", "on")
            elif k in ("id", "custom_id"):
                btn["custom_id"] = v
    else:
        if len(parts) >= 1:
            btn["label"] = parts[0]
        if len(parts) >= 2:
            btn["style"] = style_map.get(parts[1].lower(), btn["style"])
        if len(parts) >= 3:
            btn["url"] = parts[2] if parts[2].lower() != "none" else None
            if btn["url"]:
                btn["style"] = discord.ButtonStyle.link
        if len(parts) >= 4:
            btn["disabled"] = parts[3].lower() in ("true", "yes", "on", "disabled")
        if len(parts) >= 5:
            btn["emoji"] = parts[4] if parts[4].lower() != "none" else None
        if len(parts) >= 6:
            btn["custom_id"] = parts[5] if parts[5].lower() != "none" else None

    if btn["url"]:
        btn["style"] = discord.ButtonStyle.link
        btn["custom_id"] = None

    return btn


async def process_text_variables(
    text: str,
    ctx=None,
    user: discord.User = None,
    guild: discord.Guild = None,
    channel: discord.abc.Messageable = None,
) -> tuple[str, List[discord.ui.View]]:
    """Process variables and inline button components in plain text."""
    if not text:
        return "", []

    try:
        processed_text = await replace_variables(text, ctx, user=user, guild=guild, channel=channel)
    except Exception as e:
        print(f"Error in replace_variables: {e}")
        processed_text = text

    button_pattern = r"\{button:([^}]+)\}"
    button_matches = re.findall(button_pattern, processed_text)

    buttons = []
    for button_match in button_matches:
        btn_info = _parse_button_params(button_match)
        if btn_info["label"] or btn_info["emoji"]:
            buttons.append(btn_info)

    processed_text = re.sub(button_pattern, "", processed_text)

    views = []
    if buttons:
        view = discord.ui.View(timeout=None)
        for b in buttons[:25]:
            try:
                kwargs = {
                    "label": b["label"] if b["label"] and b["label"].lower() != "none" else None,
                    "style": b["style"],
                    "disabled": b["disabled"],
                    "emoji": b["emoji"] if b["emoji"] and b["emoji"].lower() != "none" else None,
                }

                if b["style"] == discord.ButtonStyle.link:
                    kwargs["url"] = b["url"]
                else:
                    kwargs["custom_id"] = b["custom_id"] or f"btn_{random.randint(1000, 9999)}"

                btn_kwargs = {k: v for k, v in kwargs.items() if v is not None}
                button = discord.ui.Button(**btn_kwargs)
                view.add_item(button)
            except Exception as e:
                print(f"Error creating button: {e}")

        views.append(view)

    return processed_text, views


async def parse_embed_script(
    script: str,
    ctx=None,
    user: discord.User = None,
    guild: discord.Guild = None,
    channel: discord.abc.Messageable = None,
) -> Tuple[Optional[str], Optional[discord.Embed], List[discord.ui.View]]:
    """Parse lightweight embed script syntax: {embed}$v{description: text}."""
    if not script:
        return None, None, []

    async def cached_replace(text: str):
        if not text or "{" not in text:
            return text
        return await replace_variables(text, ctx, user=user, guild=guild, channel=channel)

    if not script.startswith("{embed}"):
        content, views = await process_text_variables(script, ctx, user=user, guild=guild, channel=channel)
        return content, None, views

    script = script[7:]

    components = []
    start_pos = 0
    while True:
        start_marker = script.find("$v{", start_pos)
        if start_marker == -1:
            break

        brace_count = 1
        pos = start_marker + 3
        while pos < len(script) and brace_count > 0:
            if script[pos] == "{":
                brace_count += 1
            elif script[pos] == "}":
                brace_count -= 1
            pos += 1

        if brace_count == 0:
            components.append(script[start_marker + 3 : pos - 1])
            start_pos = pos
        else:
            break

    embed = discord.Embed()
    content = None
    buttons = []

    for component in components:
        try:
            if ":" not in component:
                continue

            key, val = component.split(":", 1)
            key = key.strip().lower()
            val = val.strip()

            if not val:
                continue

            val = await cached_replace(val)

            if key == "content":
                content = val
            elif key == "description":
                embed.description = val
            elif key == "title":
                if "&" in val:
                    parts = [p.strip() for p in val.split("&", 1)]
                    embed.title = parts[0]
                    if len(parts) > 1 and parts[1].lower() != "none":
                        embed.url = parts[1]
                else:
                    embed.title = val
            elif key == "color":
                try:
                    c = val.lstrip("#")
                    if c.lower() == "random":
                        embed.color = discord.Color.random()
                    else:
                        embed.color = discord.Color(int(c if c.startswith("0x") else f"0x{c}", 16) if not c.isdigit() else int(c))
                except Exception:
                    pass
            elif key == "field":
                parts = [p.strip() for p in val.split("&")]
                if len(parts) >= 2:
                    embed.add_field(
                        name=parts[0],
                        value=parts[1],
                        inline=len(parts) > 2 and parts[2].lower() in ("true", "inline", "yes"),
                    )
            elif key == "footer":
                parts = [p.strip() for p in val.split("&")]
                embed.set_footer(
                    text=parts[0],
                    icon_url=parts[1] if len(parts) > 1 and parts[1].lower() != "none" else None,
                )
            elif key == "author":
                parts = [p.strip() for p in val.split("&")]
                if parts:
                    embed.set_author(
                        name=parts[0],
                        icon_url=parts[1] if len(parts) > 1 and parts[1].lower() != "none" else None,
                        url=parts[2] if len(parts) > 2 and parts[2].lower() != "none" else None,
                    )
            elif key == "thumbnail":
                embed.set_thumbnail(url=val)
            elif key == "image":
                embed.set_image(url=val)
            elif key == "button":
                btn = _parse_button_params(val)
                if btn["label"] or btn["emoji"]:
                    buttons.append(btn)
        except Exception as e:
            print(f"Error parsing component '{component}': {e}")
            continue

    if not any(
        [
            embed.title,
            embed.description,
            embed.fields,
            embed.author.name,
            embed.footer.text,
            embed.image.url,
            embed.thumbnail.url,
        ]
    ):
        if not content:
            embed.description = "\u200b"
        else:
            embed = None

    views = []
    if buttons:
        view = discord.ui.View(timeout=None)
        for b in buttons[:25]:
            try:
                kwargs = {
                    "label": b["label"] if b["label"] and b["label"].lower() != "none" else None,
                    "style": b["style"],
                    "disabled": b["disabled"],
                    "emoji": b["emoji"] if b["emoji"] and b["emoji"].lower() != "none" else None,
                }

                if b["style"] == discord.ButtonStyle.link:
                    kwargs["url"] = b["url"]
                else:
                    kwargs["custom_id"] = b["custom_id"] or f"btn_{random.randint(1000, 9999)}"

                btn_kwargs = {k: v for k, v in kwargs.items() if v is not None}
                button = discord.ui.Button(**btn_kwargs)
                view.add_item(button)
            except Exception as e:
                print(f"Error creating button: {e}")
                continue
        views.append(view)

    return content, embed, views


def validate_embed_script(script: str) -> tuple[bool, str]:
    """Validate embed script syntax."""
    if not script:
        return False, "Script cannot be empty"

    brace_stack = []
    i = 0
    while i < len(script):
        if script[i] == "{":
            brace_stack.append(i)
        elif script[i] == "}":
            if brace_stack:
                brace_stack.pop()
            else:
                return False, f"Unexpected closing brace '}}' at position {i}"
        i += 1

    if brace_stack:
        unclosed_pos = brace_stack[0]
        var_start = unclosed_pos + 1
        var_end = var_start
        while var_end < len(script) and script[var_end] not in [" ", "$", "}", "\n"]:
            var_end += 1
        var_name = script[var_start:var_end]
        return False, f"Missing closing brace '}}' for variable '{{{var_name}' at position {unclosed_pos}"

    if not script.startswith("{embed}"):
        return True, "Valid text with variables"

    if not re.search(r"\$v\{[^}]+\}", script):
        return False, "No valid components found. Use $v{component} syntax"

    return True, "Valid embed script"


def get_available_variables() -> Dict[str, List[str]]:
    """Return a categorized list of available variables for this simple parser."""
    return {
        "Script Components": ["{embed}", "$v{...}", "{button:...}", "{content: ...}"],
        "User Variables": [
            "{user}",
            "{user.name}",
            "{user.display_name}",
            "{user.mention}",
            "{user.id}",
            "{user.tag}",
            "{user.bot}",
            "{user.avatar}",
            "{user.display_avatar}",
            "{user.created_at}",
            "{user.created_at_timestamp}",
            "{user.color}",
            "{user.color.value}",
            "{user.joined_at}",
            "{user.joined_at_timestamp}",
            "{user.join_position}",
            "{user.join_position_suffix}",
            "{user.top_role}",
            "{user.top_role.name}",
            "{user.top_role.id}",
            "{user.top_role.mention}",
            "{user.premium_since}",
            "{user.premium_since_timestamp}",
            "{user.boosted}",
        ],
        "Guild Variables": [
            "{guild}",
            "{guild.name}",
            "{guild.id}",
            "{guild.icon}",
            "{guild.count}",
            "{guild.member_count}",
            "{guild.boost_count}",
            "{guild.boost_tier}",
            "{guild.owner}",
            "{guild.owner_id}",
            "{guild.owner_mention}",
            "{guild.created_at}",
            "{guild.created_at_timestamp}",
            "{guild.vanity}",
            "{guild.banner}",
            "{guild.splash}",
            "{guild.discovery_splash}",
            "{guild.shard_id}",
            "{guild.shard_count}",
            "{guild.description}",
            "{guild.preferred_locale}",
            "{guild.role_count}",
            "{guild.channel_count}",
            "{guild.emoji_count}",
            "{guild.sticker_count}",
        ],
        "Channel Variables": [
            "{channel}",
            "{channel.name}",
            "{channel.mention}",
            "{channel.id}",
            "{channel.topic}",
            "{channel.type}",
            "{channel.position}",
        ],
    }
