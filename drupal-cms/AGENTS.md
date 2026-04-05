# AGENTS.md - Drupal CMS

This file scopes agent rules to the `drupal-cms/` component only.
For the Python application rules see the root `AGENTS.md`.

## Overview

The `drupal-cms/` directory contains a Drupal CMS recipe system. It is a
separate component from the Python application. All work here is PHP-based
and requires DDEV for local development. Python tooling (Pylint, mypy,
Pylance) does not apply here.

---

## Critical Rules (Non-Negotiable)

### 1. NO Emojis - NEVER

Never use emojis in any `.php`, `.twig`, `.yml`, or `.md` files in this
directory. This is a hard requirement shared with the rest of the project.

### 2. DDEV Is Always Required

All commands that interact with the Drupal installation, Composer, Drush,
or any infrastructure (Milvus, Solr, etc.) must be prefixed with `ddev`.
Never run these commands bare on the host machine.

```bash
# Start the environment first
ddev start

# Composer
ddev composer install
ddev composer require drupal/some_module
ddev composer update

# Drush
ddev drush cr
ddev drush updb
ddev drush cex
ddev drush cim

# Infrastructure services (Milvus, Solr, etc.)
ddev exec <command>
```

After making structural changes you may need to rebuild:

```bash
ddev rebuild
```

### 3. PHP Code Quality Standards

All custom PHP code in `web/modules/custom/` and `web/themes/custom/`
must pass both quality tools before committing.

**PHPCS with Drupal coding standard:**

```bash
ddev exec vendor/bin/phpcs --standard=Drupal,DrupalPractice \
  web/modules/custom web/themes/custom
```

**PHPStan at minimum level 6:**

```bash
ddev exec vendor/bin/phpstan analyse \
  --level=6 \
  web/modules/custom web/themes/custom
```

Rules:

- Never use `// phpcs:ignore` or `// phpstan-ignore` unless absolutely
  unavoidable; always fix the underlying issue instead.
- PHPStan level 6 enforces strict null checks and type inference. Add
  proper type hints and null guards rather than suppressing errors.
- Drupal coding standard requires proper docblocks for all hook
  implementations and public methods.

### 4. Drupal Contrib Patch Policy

Never leave direct edits in `web/modules/contrib/` as the only
implementation. If a contrib module requires a fix:

1. Create a patch file in `patches/`.
2. Register the patch in `composer.json` under `extra.patches`.
3. Enable and use Composer patch tooling so the fix reapplies after updates.

This keeps contrib upgrades reproducible and prevents local hotfixes from
being lost on reinstall or update.

### 5. Documentation Must Track Code

| Change Type | Documentation to Update |
|-------------|------------------------|
| New custom module | this AGENTS.md, relevant `docs/` file if integration-facing |
| New DDEV service | this AGENTS.md infrastructure section |
| Changed infrastructure (Milvus, Solr, etc.) | root `docs/` integration docs |

---

## DDEV Infrastructure Services

| Service | Config file | Host port | Purpose |
|---------|-------------|-----------|---------|
| Solr | `docker-compose.solr.yaml` | 8983 | Drupal Search API full-text index |
| Ollama | `docker-compose.ollama.yaml` | 11434 | Local LLM inference for Drupal AI |
| Milvus | `docker-compose.milvus.yaml` | 19530 | Vector DB for Python semantic search |

All services start automatically with `ddev start`.

Milvus takes up to 90 seconds to become healthy on first start. Verify with:

```bash
ddev milvus-status
```

---

## Project Setup

### First-Time Setup

```bash
ddev config --project-type=drupal11 --docroot=web
ddev start
ddev composer install
ddev composer drupal:recipe-unpack
ddev launch
```

### Applying Configuration

```bash
ddev drush cim   # import config
ddev drush cr    # rebuild Drupal cache
```

---

## Custom Modules

| Module | Path | Purpose |
|--------|------|---------|
| `dnd_migrate` | `web/modules/custom/dnd_migrate/` | Migrates D&D game data from JSON source files into Drupal content |
| `entity_lock` | `web/modules/custom/entity_lock/` | Prevents deletion (and unpublishing) of any entity type via a locked-entity config list and admin UI |

### dnd_migrate

Provides Drupal migrate source and process plugins for importing the project's
JSON game data (characters, NPCs, items) into Drupal content nodes.

**Plugins provided:**

| Plugin type | ID | Description |
|-------------|-----|-------------|
| Source | `dnd_json_directory` | Reads all `*.json` files from a directory; one row per file |
| Source | `dnd_items_json` | Reads a keyed-object JSON file (custom_items.json); one row per key |
| Source | `dnd_spell_slots_source` | Flattens spell_slots objects into one row per (character, slot_level) |
| Process | `dnd_join_array` | Joins a PHP array into a single string with a configurable separator |
| Process | `dnd_spell_slot_lookup` | Resolves spell_slots to paragraph entity_reference_revisions values |

**Migration IDs and run order:**

1. `dnd_items` - item nodes from `game_data/items/custom_items.json`
2. `dnd_npc_nodes` - NPC nodes from `game_data/npcs/*.json`
3. `dnd_character_backstory` - paragraph:wysiwyg entities for character backstories
4. `dnd_character_spell_slots` - paragraph:spell_slot entities per slot level
5. `dnd_character_nodes` - character nodes from `game_data/characters/*.json`

**Running migrations:**

Enable the module and run with Drush:

```bash
# Enable the module
ddev drush en dnd_migrate

# Run all D&D migrations in dependency order
ddev drush migrate:import --group=dnd --execute-dependencies

# Run a single migration
ddev drush migrate:import dnd_items

# Check migration status
ddev drush migrate:status --group=dnd

# Roll back (removes Drupal content, does not touch source JSON)
ddev drush migrate:rollback --group=dnd
```

**Source path configuration:**

The `data_dir` and `file_path` values in each migration YAML default to DDEV
container paths (`/var/www/html/game_data/...`). If the project is mounted at a
different path, update those values in each migration's `source:` block.

---

## Quick Reference

| Task | Command |
|------|---------|
| Milvus status (Python) | `ddev milvus-status` |
| Rebuild Milvus index (Python) | `ddev milvus-reindex` |
| Start environment | `ddev start` |
| Stop environment | `ddev stop` |
| Rebuild | `ddev rebuild` |
| Install dependencies | `ddev composer install` |
| Add a module | `ddev composer require drupal/module_name` |
| Clear caches | `ddev drush cr` |
| Run DB updates | `ddev drush updb` |
| Export config | `ddev drush cex` |
| Import config | `ddev drush cim` |
| PHPCS check | `ddev exec vendor/bin/phpcs --standard=Drupal,DrupalPractice web/modules/custom web/themes/custom` |
| PHPStan check | `ddev exec vendor/bin/phpstan analyse --level=6 web/modules/custom web/themes/custom` |
| Run all D&D migrations | `ddev drush migrate:import --group=dnd --execute-dependencies` |
| Check migration status | `ddev drush migrate:status --group=dnd` |
| Roll back D&D migrations | `ddev drush migrate:rollback --group=dnd` |

---

## Directory Layout

```text
drupal-cms/
|-- composer.json        # Dependency manifest + patch registry
|-- patches/             # Patch files for contrib modules
|-- web/
|   |-- modules/
|   |   |-- contrib/     # Downloaded modules - never edit directly
|   |   `-- custom/      # Custom modules - all PHP must pass PHPCS + PHPStan
|   |       `-- dnd_migrate/   # D&D data migration module
|   `-- themes/
|       |-- contrib/     # Downloaded themes - never edit directly
|       `-- custom/      # Custom themes - all PHP must pass PHPCS + PHPStan
`-- private/             # Private files (git-ignored sensitive data)
```
