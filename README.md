# Nybble format registry

[![validate](https://github.com/Majd42/nybble-registry/actions/workflows/validate.yml/badge.svg)](https://github.com/Majd42/nybble-registry/actions/workflows/validate.yml)

A community library of **format packs** for
[Nybble](https://github.com/Majd42/binary-explorer), the visual binary structure
explorer. Each pack teaches Nybble a new file format — how to detect it and how
to decode its structure. Packs are **declarative**: a single TOML file, data
only, no code, so they're safe to share and trivial to install.

## About

Nybble parses a binary file into a labeled structure tree using a **schema** — a
compact description of the format's layout. This registry is the shared home for
those schemas, packaged as installable format packs. It plays the same role a
plugin gallery does for an editor: a browsable, reviewable catalog the app pulls
from, and the place community-contributed formats land.

Two ideas keep it simple:

- **Data, not code.** A pack is pure TOML — metadata, magic-number detection
  rules, and a schema written in Nybble's schema language. There is nothing to
  execute, so a pack is safe to download, easy to diff in a PR, and portable
  across every place Nybble runs.
- **One file the app already understands.** A pack's `plugin.toml` is exactly
  what you'd install by hand from the app's **Plugins** panel. The registry adds
  only a thin layer of metadata (`meta.toml`) and a generated catalog
  ([`index.json`](./index.json)) on top of it.

The catalog currently ships **21 packs** spanning images, audio, video,
executables, filesystems, fonts, archives, network captures, and 3D models —
see [`index.json`](./index.json) for the authoritative, always-current list.

## What's a format pack?

A folder under [`formats/`](./formats), named for the format's id:

```
formats/<id>/
├── plugin.toml   # the installable manifest (exactly what the app consumes)
└── meta.toml     # registry metadata: category, tags, maintainer, sample
```

`plugin.toml` is the same file you'd install by hand in the app's **Plugins**
panel. It declares metadata plus one or more `[[formats]]`, each with a
magic-number `detect` rule and an inline `schema` written in Nybble's schema
language. See [`formats/gif`](./formats/gif) for a worked example.

## Using packs

- **In the app:** browse and install packs from the registry directly, or
  download a pack's `plugin.toml` and install it from **Plugins → Install from
  file…**.
- **Programmatically:** [`index.json`](./index.json) is a generated catalog of
  every pack — id, name, category, tags, the formats it provides, and the path
  to its `plugin.toml`. Fetch it to browse or auto-install.

## Contributing a format

See [CONTRIBUTING.md](./CONTRIBUTING.md). In short: copy the `gif` folder, edit
the two files, run `python tools/validate.py`, and open a PR. CI validates every
pack and confirms `index.json` is up to date.

## Validation

```bash
python tools/validate.py          # validate all packs, rewrite index.json
python tools/validate.py --check  # validate + fail if index.json is stale (CI)
```

Needs only Python 3.11+ (standard-library `tomllib`). Today this is
**structural** validation — TOML well-formedness, required fields, valid detect
hex, unique ids. Deep schema-grammar checking runs client-side when a pack is
installed.

## License

Format packs are contributed by their authors; see each pack's `meta.toml` for
attribution. Unless a pack states otherwise, packs in this registry may be freely
used and redistributed.
