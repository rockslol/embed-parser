# embed-parser

A very simple embed parser for Discord bots written in Python.

## What it does

- Parses embed scripts like `{embed}$v{title: Hello}$v{description: World}`
- Replaces basic user, guild, and channel variables
- Supports embed parts: title, description, color, field, footer, author, thumbnail, image, content, button
- Validates script format

## Quick example

```py
from functions.embed_parser import parse_embed_script

script = "{embed}$v{title: Welcome}$v{description: Hello {user.mention}}"
content, embed, views = await parse_embed_script(script, ctx)
```
