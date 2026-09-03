# Contributing a format pack

Thanks for growing the Nybble format library! A pack is pure data — a couple of
TOML files — so contributing is quick.

## Fastest path: export from the app

If you built the schema in Nybble, you do not need to write `plugin.toml` by
hand. With the schema loaded, click **Pack...** in the toolbar and fill in the
dialog:

| Dialog field | Becomes |
|---|---|
| Id (folder name) | `id` — must match the folder you create below |
| Display name | `name` |
| Format name | the `[[formats]]` name shown in the app |
| Extension | `extension` |
| Description | `description` |
| Author | `author` |
| Magic (hex) + Magic offset | `detect` — leave the magic blank for manual-only formats |
| Confidence | `confidence` (0..=100) |

The export sets `version = "1.0.0"`, and Nybble validates that the schema parses
before writing the file — so an exported pack is guaranteed installable. Save it
as `formats/<id>/plugin.toml`, then jump to step 3 to add `meta.toml` and
regenerate the index.

Writing the TOML by hand works just as well; the rest of this guide covers that.

## 1. Create the pack folder

Pick a short, lowercase `id` for the format (letters, digits, hyphens). Copy the
example:

```bash
cp -r formats/gif formats/<id>
```

You now have `formats/<id>/plugin.toml` and `formats/<id>/meta.toml`.

## 2. Edit `plugin.toml` (the installable manifest)

```toml
id = "<id>"              # must equal the folder name
name = "Human name"
version = "1.0.0"
description = "One line."
author = "your name / handle"

[[formats]]
name = "MYFMT"          # shown in the app; also a schema entry
extension = "myf"
description = "..."
confidence = 90          # 0..=100; how sure a detect match is
entry = "Root"           # the struct to start parsing from
endian = "le"            # le | be
detect = [{ offset = 0, hex = "DE AD BE EF" }]   # magic number(s); omit for manual-only
schema = """
struct Root {
    magic  bytes[4]  "file magic"
    ...
}
"""
```

- **`detect`** is a list of parts; each part matches `hex` bytes at `offset`. All
  parts must match. Leave `detect` out entirely for a format with no reliable
  magic — it won't auto-detect, but users can still load it manually.
- **`schema`** is Nybble's schema language (structs, primitives, enums,
  bitfields, `if` conditionals, pointers, `cstring`/`[*]`, unions). Inside a TOML
  basic multiline string, escape any `"` in field docs as `\"`.

## 3. Edit `meta.toml` (registry metadata)

```toml
category = "image"                 # image | archive | executable | database | ...
tags = ["image", "raster"]
maintainer = "your name / handle"
homepage = "https://spec-url"       # optional
sample = ""                          # optional: URL to a tiny public sample file
```

## 4. Validate & regenerate the index

```bash
python tools/validate.py     # rewrites index.json; must exit 0
```

Commit the regenerated `index.json` along with your pack — CI runs
`--check` and fails if it's stale.

## 5. Open a PR

Include what the format is and where you sourced the layout (a spec link is
ideal). CI will validate structure automatically.

### Tips for writing the schema

The best way to author and test a schema is in the app itself: open a real file
of the format, use the schema editor with live parsing, iterate until the parse
tree looks right, then paste the schema into your `plugin.toml`.
