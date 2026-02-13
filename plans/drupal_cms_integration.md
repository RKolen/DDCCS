# Drupal CMS Integration Design for D&D Character Consultant

## Overview

This document describes the design for integrating the D&D Character Consultant
System with Drupal CMS for local visualization. The system is currently
file-based (JSON) and will be coupled with Drupal for better visual presentation
locally, with future support for a decoupled React frontend.

---

## 1. Architecture Decision

### 1.1 Is Drupal the Right Choice?

**Recommendation: Yes, with caveats**

Drupal is a reasonable choice for this use case, but it is important to
understand both the benefits and the overhead involved.

#### Pros

| Aspect | Benefit |
|--------|---------|
| **Content Modeling** | Robust entity system with fields, references, and taxonomies |
| **API-First** | JSON:API and RESTful Web Services in core |
| **Taxonomy System** | Native support for traits, classes, species as vocabularies |
| **Search API** | Integration with Solr, Elasticsearch for RAG-like functionality |
| **Local Development** | DDEV provides excellent local Drupal development experience |
| **Decoupled Ready** | Built for headless/decoupled architectures |
| **Community Modules** | Existing modules for relationships, entity references |
| **Permissions** | Fine-grained access control for future multi-user scenarios |

#### Cons

| Aspect | Drawback |
|---------|----------|
| **Heavyweight** | Drupal is overkill for simple local visualization |
| **Learning Curve** | Steep learning curve for Drupal-specific concepts |
| **Maintenance** | Requires ongoing updates and security patches |
| **Resource Usage** | Higher memory/CPU than lightweight alternatives |
| **Development Speed** | Slower initial setup compared to simpler solutions |

### 1.2 Alternative Approaches Considered

#### Alternative A: Static Site Generator (Hugo/Jekyll)

**Pros:** Lightweight, fast, no database, simple deployment
**Cons:** No dynamic search, no API for Python sync, limited interactivity

**Verdict:** Good for read-only, but lacks the API capabilities needed for
Python-to-CMS synchronization.

#### Alternative B: SQLite + Custom Web App (Flask/FastAPI)

**Pros:** Lightweight, Python-native, full control
**Cons:** Need to build everything from scratch (admin UI, API, search)

**Verdict:** More work upfront, but better long-term fit if Drupal feels too
heavy.

#### Alternative C: Notion/Airtable

**Pros:** No setup, visual interface, API available
**Cons:** Cloud-dependent, not local-first, limited customization

**Verdict:** Not suitable for local-only requirement.

### 1.3 Final Recommendation

**Proceed with Drupal** for the following reasons:

1. The user specifically requested Drupal integration
2. DDEV makes local setup straightforward
3. JSON:API provides immediate API capabilities
4. Taxonomy system maps well to D&D traits/classes/species
5. Future React frontend is well-supported by Drupal's API-first architecture

**However**, consider starting with a minimal Drupal setup and evaluating
whether the overhead is justified after initial implementation.

---

## 2. Drupal Content Types

### 2.1 Character Content Type

Machine name: `character`

| Field Name | Machine Name | Type | Description |
|------------|--------------|------|-------------|
| Name | `title` | Core | Character name (Drupal core title field) |
| Nickname | `field_nickname` | Text | Alternative name/alias |
| Species | `field_species` | Entity Reference | Reference to Species taxonomy |
| Lineage | `field_lineage` | Text | Sub-race or lineage |
| Class | `field_class` | Entity Reference | Reference to Class taxonomy |
| Subclass | `field_subclass` | Text | Character subclass/archetype |
| Level | `field_level` | Integer | Character level (1-20) |
| Background | `field_background` | Text (long) | Character background story |
| Backstory | `field_backstory` | Text (long) | Detailed backstory |
| Max HP | `field_max_hp` | Integer | Maximum hit points |
| Armor Class | `field_armor_class` | Integer | AC value |
| Movement Speed | `field_movement_speed` | Integer | Speed in feet |
| Proficiency Bonus | `field_proficiency_bonus` | Integer | Proficiency bonus |
| Portrait | `field_portrait` | Image | Character portrait image |

#### Ability Scores Field Group

Create as a separate paragraph or individual fields:

| Field Name | Machine Name | Type |
|------------|--------------|------|
| Strength | `field_str` | Integer |
| Dexterity | `field_dex` | Integer |
| Constitution | `field_con` | Integer |
| Intelligence | `field_int` | Integer |
| Wisdom | `field_wis` | Integer |
| Charisma | `field_cha` | Integer |

**Alternative:** Use a single `field_ability_scores` paragraph type with all
six scores as sub-fields.

#### Skills Field

Machine name: `field_skills`

Use a key-value field type or create a custom field type. Options:

1. **Paragraphs module:** Create a Skill paragraph with `field_skill_name` and
   `field_skill_modifier`
2. **Table field:** Use the Table Field module for structured data
3. **JSON field:** Store as JSON if searchability is not required

#### Equipment Fields

| Field Name | Machine Name | Type |
|------------|--------------|------|
| Weapons | `field_weapons` | Text (list) |
| Armor | `field_armor` | Text (list) |
| Items | `field_items` | Text (list) |
| Magic Items | `field_magic_items` | Entity Reference | Reference to Item nodes |
| Gold | `field_gold` | Integer |

#### Spell Fields

| Field Name | Machine Name | Type |
|------------|--------------|------|
| Spell Slots | `field_spell_slots` | JSON or key-value |
| Known Spells | `field_known_spells` | Text (list) |

#### Personality Fields (Taxonomy References)

| Field Name | Machine Name | Type |
|------------|--------------|------|
| Personality Traits | `field_personality_traits` | Entity Reference | Traits taxonomy |
| Ideals | `field_ideals` | Entity Reference | Traits taxonomy |
| Bonds | `field_bonds` | Entity Reference | Traits taxonomy |
| Flaws | `field_flaws` | Entity Reference | Traits taxonomy |

#### Relationships Field

Machine name: `field_relationships`

Use the **Entity Reference** field with a custom field to store relationship
description. Options:

1. **Entity Reference with Views:** Create a view showing relationships
2. **Paragraphs:** Create a Relationship paragraph with:
   - `field_related_character` (Entity Reference to Character)
   - `field_relationship_type` (Text: "Friend", "Mentor", etc.)
   - `field_relationship_description` (Text)

#### AI Configuration Fields

| Field Name | Machine Name | Type |
|------------|--------------|------|
| AI Enabled | `field_ai_enabled` | Boolean |
| AI Temperature | `field_ai_temperature` | Decimal |
| AI Max Tokens | `field_ai_max_tokens` | Integer |
| AI System Prompt | `field_ai_system_prompt` | Text (long) |
| AI Model | `field_ai_model` | Text |
| AI Base URL | `field_ai_base_url` | Text |

#### Feats and Abilities

| Field Name | Machine Name | Type |
|------------|--------------|------|
| Feats | `field_feats` | Text (list) |
| Class Abilities | `field_class_abilities` | Text (list) |
| Specialized Abilities | `field_specialized_abilities` | Text (list) |
| Major Plot Actions | `field_major_plot_actions` | Text (list) |

### 2.2 NPC Content Type

Machine name: `npc`

| Field Name | Machine Name | Type | Description |
|------------|--------------|------|-------------|
| Name | `title` | Core | NPC name |
| Nickname | `field_nickname` | Text | Alternative name |
| Profile Type | `field_profile_type` | List (text) | simplified/full |
| Faction | `field_faction` | List (text) | ally/neutral/enemy |
| Role | `field_role` | Text | NPC role (Innkeeper, etc.) |
| Species | `field_species` | Entity Reference | Reference to Species taxonomy |
| Lineage | `field_lineage` | Text | Sub-race or lineage |
| Personality | `field_personality` | Text (long) | Personality description |
| Key Traits | `field_key_traits` | Entity Reference | Traits taxonomy |
| Abilities | `field_abilities` | Text (list) | NPC abilities |
| Recurring | `field_recurring` | Boolean | Is this a recurring NPC? |
| Notes | `field_notes` | Text (long) | DM notes |
| Location | `field_location` | Entity Reference | Location taxonomy |
| Relationships | `field_relationships` | Paragraphs | Same as Character |

#### Full Profile Fields (conditional)

For NPCs with `field_profile_type = full`, include:

| Field Name | Machine Name | Type |
|------------|--------------|------|
| Class | `field_class` | Entity Reference |
| Level | `field_level` | Integer |
| Ability Scores | `field_ability_scores` | Paragraphs |
| Max HP | `field_max_hp` | Integer |
| Armor Class | `field_armor_class` | Integer |

### 2.3 Story Content Type

Machine name: `story`

| Field Name | Machine Name | Type | Description |
|------------|--------------|------|-------------|
| Title | `title` | Core | Story title |
| Campaign | `field_campaign` | Entity Reference | Reference to Campaign taxonomy |
| Story Number | `field_story_number` | Integer | Sequential number (001, 002, etc.) |
| Content | `body` | Text (long, formatted) | Story markdown content |
| Characters | `field_characters` | Entity Reference | Characters appearing in story |
| NPCs | `field_npcs` | Entity Reference | NPCs appearing in story |
| Locations | `field_locations` | Entity Reference | Locations in story |
| Session Date | `field_session_date` | Date | When the session occurred |
| Story Hooks | `field_story_hooks` | Text (long) | Generated story hooks |
| Session Results | `field_session_results` | Text (long) | Session outcome summary |

### 2.4 Item Content Type

Machine name: `item`

| Field Name | Machine Name | Type | Description |
|------------|--------------|------|-------------|
| Name | `title` | Core | Item name |
| Item Type | `field_item_type` | List (text) | weapon/armor/item/magic_item |
| Is Magic | `field_is_magic` | Boolean | Is this a magic item? |
| Description | `body` | Text (long) | Item description |
| Rarity | `field_rarity` | List (text) | common/uncommon/rare/very_rare/legendary/artifact |
| Requires Attunement | `field_attunement` | Boolean | Attunement required? |
| Benefits | `field_benefits` | Text (long) | Item benefits |
| Notes | `field_notes` | Text (long) | Additional notes |
| Owners | `field_owners` | Entity Reference | Characters who own this item |

### 2.5 Session Content Type

Machine name: `session`

| Field Name | Machine Name | Type | Description |
|------------|--------------|------|-------------|
| Title | `title` | Core | Session title |
| Campaign | `field_campaign` | Entity Reference | Campaign reference |
| Session Number | `field_session_number` | Integer | Session sequence |
| Date | `field_session_date` | Date | Session date |
| Summary | `body` | Text (long) | Session summary |
| Characters Present | `field_characters_present` | Entity Reference | Characters in session |
| NPCs Encountered | `field_npcs_encountered` | Entity Reference | NPCs in session |
| Story Files | `field_story_files` | Entity Reference | Related story nodes |
| Character Development | `field_character_development` | Text (long) | Character growth notes |

---

## 3. Taxonomy Vocabulary Design

### 3.1 Traits Vocabulary

Machine name: `traits`

Used for personality_traits, ideals, bonds, and flaws.

**Structure:**

| Field Name | Machine Name | Type |
|------------|--------------|------|
| Name | `name` | Core |
| Trait Type | `field_trait_type` | List (text) | personality/ideal/bond/flaw |
| Description | `description` | Text |

**Example Terms:**

| Name | Trait Type |
|------|------------|
| Stoic | personality |
| Wise | personality |
| Compassionate | personality |
| Protect the Free Peoples | ideal |
| Defend his friends | bond |
| Fear of failing his ancestors | flaw |

### 3.2 Species Vocabulary

Machine name: `species`

**Structure:**

| Field Name | Machine Name | Type |
|------------|--------------|------|
| Name | `name` | Core |
| Description | `description` | Text |
| Parent Species | `parent` | Entity Reference | For sub-species |

**Example Terms:**

- Human
- Elf (parent: null)
  - High Elf (parent: Elf)
  - Wood Elf (parent: Elf)
- Dwarf
- Halfling

### 3.3 Class Vocabulary

Machine name: `dnd_class`

**Structure:**

| Field Name | Machine Name | Type |
|------------|--------------|------|
| Name | `name` | Core |
| Description | `description` | Text |
| Hit Die | `field_hit_die` | Integer |
| Primary Ability | `field_primary_ability` | Text |
| Spellcaster | `field_spellcaster` | Boolean |

**Example Terms:**

| Name | Hit Die | Primary Ability | Spellcaster |
|------|---------|-----------------|-------------|
| Fighter | 10 | Strength | No |
| Ranger | 10 | Dexterity | Yes |
| Wizard | 6 | Intelligence | Yes |
| Cleric | 8 | Wisdom | Yes |

### 3.4 Location Vocabulary

Machine name: `locations`

**Structure:**

| Field Name | Machine Name | Type |
|------------|--------------|------|
| Name | `name` | Core |
| Description | `description` | Text |
| Parent Location | `parent` | Entity Reference |
| Type | `field_location_type` | List (text) | city/region/building/wilderness |

**Example Terms:**

- Middle-earth (region)
  - Eriador (region, parent: Middle-earth)
    - Bree (city, parent: Eriador)
      - The Prancing Pony (building, parent: Bree)
    - Weathertop (wilderness, parent: Eriador)

### 3.5 Campaign Vocabulary

Machine name: `campaign`

**Structure:**

| Field Name | Machine Name | Type |
|------------|--------------|------|
| Name | `name` | Core |
| Description | `description` | Text |
| Start Date | `field_start_date` | Date |
| Status | `field_status` | List (text) | active/completed/on_hold |

### 3.6 Story Tags Vocabulary

Machine name: `story_tags`

**Structure:**

| Field Name | Machine Name | Type |
|------------|--------------|------|
| Name | `name` | Core |
| Description | `description` | Text |

**Example Terms:**

- combat
- social
- exploration
- mystery
- travel
- rest

---

## 4. Database Schema for RAG

### 4.1 RAG Storage Options in Drupal

The current RAG system stores cached wiki content in `.rag_cache/` as JSON
files. For Drupal integration, consider these options:

#### Option A: Custom RAG Entity

Create a custom Drupal entity for RAG entries:

```sql
-- Custom table: rag_cache
CREATE TABLE rag_cache (
  id INT AUTO_INCREMENT PRIMARY KEY,
  uuid VARCHAR(128) NOT NULL,
  source_url VARCHAR(2048) NOT NULL,
  title VARCHAR(512),
  content LONGTEXT,
  embedding BLOB,  -- Vector embedding if using ML
  created INT NOT NULL,
  updated INT NOT NULL,
  expires INT,
  INDEX idx_source_url (source_url(255)),
  INDEX idx_expires (expires)
);
```

**Drupal Entity Definition:**

```php
/**
 * @ContentEntityType(
 *   id = "rag_cache",
 *   label = @Translation("RAG Cache Entry"),
 *   base_table = "rag_cache",
 *   entity_keys = {
 *     "id" = "id",
 *     "uuid" = "uuid",
 *     "label" = "title",
 *   },
 *   handlers = {
 *     "storage" = "Drupal\Core\Entity\Sql\SqlContentEntityStorage",
 *     "access" = "Drupal\Core\Entity\EntityAccessControlHandler",
 *   },
 * )
 */
```

#### Option B: Use Search API with Solr/Elasticsearch

For production-grade RAG functionality:

1. Install **Search API** module
2. Configure Solr or Elasticsearch backend
3. Index Character, NPC, Story, and Item content
4. Use Search API for semantic search

**Pros:**
- Full-text search capabilities
- Faceted search
- Better performance for large datasets

**Cons:**
- Additional infrastructure (Solr/ES server)
- More complex setup

#### Option C: MySQL Full-Text Search

For simpler local-only setup:

1. Enable full-text indexing on relevant fields
2. Use MySQL's MATCH AGAINST for search
3. Store embeddings as JSON in custom table

```sql
-- Add full-text index to story body
ALTER TABLE node__body ADD FULLTEXT INDEX ft_body (body_value);

-- Query example
SELECT * FROM node__body
WHERE MATCH(body_value) AGAINST('Weathertop dark magic' IN NATURAL_LANGUAGE_MODE);
```

### 4.2 Embedding Storage

For vector embeddings (if using ML-based RAG):

#### Option A: Separate Embedding Table

```sql
CREATE TABLE rag_embeddings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  entity_type VARCHAR(64) NOT NULL,
  entity_id INT NOT NULL,
  embedding BLOB NOT NULL,
  model VARCHAR(128),
  created INT NOT NULL,
  INDEX idx_entity (entity_type, entity_id)
);
```

#### Option B: Use MariaDB Vector Type

If using MariaDB 11.7+, native vector support is available:

```sql
CREATE TABLE rag_embeddings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  entity_type VARCHAR(64) NOT NULL,
  entity_id INT NOT NULL,
  embedding VECTOR(1536),  -- OpenAI embedding dimension
  model VARCHAR(128),
  created INT NOT NULL
);
```

### 4.3 Recommended RAG Architecture

For local DDEV setup:

```
+-------------------+     +-------------------+     +-------------------+
| Python App        |     | Drupal CMS        |     | MySQL Database    |
+-------------------+     +-------------------+     +-------------------+
|                   |     |                   |     |                   |
| RAG System        |---->| JSON:API          |---->| rag_cache table   |
| WikiClient        |     | Custom RAG Entity |     | rag_embeddings    |
| WikiCache         |     | Search API        |     | node tables       |
+-------------------+     +-------------------+     +-------------------+
```

**Implementation Steps:**

1. Create custom `rag_cache` entity in Drupal module
2. Expose via JSON:API
3. Modify Python RAG system to sync to Drupal
4. Use MySQL full-text search for basic queries
5. Optionally add Solr for advanced search

---

## 5. DDEV Setup Configuration

### 5.1 DDEV Configuration

Create `.ddev/config.yaml`:

```yaml
name: dnd-consultant
type: drupal
docroot: web
php_version: "8.2"
webserver_type: nginx-fpm
router_http_port: "80"
router_https_port: "443"
xdebug_enabled: false
additional_hostnames: []
additional_fqdns: []
database:
  type: mysql
  version: "8.0"
use_dns_when_possible: true
composer_version: "2"
web_environment: []
corepack_enable: false
```

### 5.2 Required Drupal Modules

Create `web/modules/custom/dnd_content/` module.

**Core Modules (included):**

- node
- taxonomy
- text
- options
- entity_reference
- rest
- serialization
- jsonapi
- basic_auth

**Contrib Modules:**

```bash
# Install via composer
ddev composer require drupal/paragraphs
ddev composer require drupal/entity_reference_revisions
ddev composer require drupal/jsonapi_extras
ddev composer require drupal/restui
ddev composer require drupal/search_api
ddev composer require drupal/facets
ddev composer require drupal/views
ddev composer require drupal/token
ddev composer require drupal/pathauto
```

**Module Purposes:**

| Module | Purpose |
|--------|---------|
| paragraphs | Complex fields (relationships, ability scores) |
| entity_reference_revisions | Required by paragraphs |
| jsonapi_extras | Customize JSON:API endpoints |
| restui | REST API configuration UI |
| search_api | RAG search functionality |
| facets | Filter search results |
| pathauto | Automatic URL aliases |
| token | Token replacement for pathauto |

### 5.3 Drupal Installation Profile

Create a custom installation profile or use Standard profile with
configuration export.

**Recommended: Standard profile + custom module**

```php
// web/modules/custom/dnd_content/dnd_content.info.yml
name: 'D&D Content Types'
type: module
description: 'Content types and taxonomies for D&D Character Consultant'
core_version_requirement: ^10
package: Custom
dependencies:
  - node
  - taxonomy
  - text
  - options
  - entity_reference
  - paragraphs
  - entity_reference_revisions
  - jsonapi
  - rest
  - serialization
```

### 5.4 Local Development Commands

```bash
# Start DDEV
ddev start

# Install Drupal
ddev drush site:install standard --db-url=mysql://db:db@db/db

# Enable custom module
ddev drush en dnd_content

# Import content types and taxonomies
ddev drush config:import

# Create admin user
ddev drush user:create admin --password=admin

# Generate one-time login
ddev drush user:login

# Export configuration
ddev drush config:export

# Clear cache
ddev drush cr
```

---

## 6. Python-to-Drupal API Design

### 6.1 API Architecture

```
+-------------------+                    +-------------------+
| Python App        |                    | Drupal CMS        |
+-------------------+                    +-------------------+
|                   |                    |                   |
| CharacterManager  |--(JSON:API POST)-->| /jsonapi/node/    |
| NPCManager        |                    |   character       |
| StoryManager      |<-(JSON:API GET)----|   npc             |
| ItemRegistry      |                    |   story           |
| RAG System        |                    |   item            |
|                   |                    |                   |
| DrupalSync class  |                    | JSON:API Module   |
+-------------------+                    +-------------------+
```

### 6.2 JSON:API Endpoints

Drupal's JSON:API provides RESTful endpoints automatically:

| Entity | Endpoint | Methods |
|--------|----------|---------|
| Characters | `/jsonapi/node/character` | GET, POST, PATCH, DELETE |
| NPCs | `/jsonapi/node/npc` | GET, POST, PATCH, DELETE |
| Stories | `/jsonapi/node/story` | GET, POST, PATCH, DELETE |
| Items | `/jsonapi/node/item` | GET, POST, PATCH, DELETE |
| Sessions | `/jsonapi/node/session` | GET, POST, PATCH, DELETE |
| Species | `/jsonapi/taxonomy_term/species` | GET, POST, PATCH, DELETE |
| Classes | `/jsonapi/taxonomy_term/dnd_class` | GET, POST, PATCH, DELETE |
| Traits | `/jsonapi/taxonomy_term/traits` | GET, POST, PATCH, DELETE |
| Locations | `/jsonapi/taxonomy_term/locations` | GET, POST, PATCH, DELETE |
| Campaigns | `/jsonapi/taxonomy_term/campaign` | GET, POST, PATCH, DELETE |

### 6.3 Authentication

**Recommended: Basic Auth + HTTPS**

1. Create a dedicated API user in Drupal
2. Assign appropriate permissions
3. Use Basic Authentication for API requests

**Alternative: API Key Module**

For simpler token-based auth:

```bash
ddev composer require drupal/api_key
```

### 6.4 Python DrupalSync Class

Create `src/integration/drupal_sync.py`:

```python
"""
Drupal CMS Synchronization Module

Provides bidirectional sync between JSON files and Drupal CMS.
"""

import os
import json
from typing import Any, Dict, List, Optional
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth

from src.utils.file_io import load_json_file, save_json_file
from src.utils.path_utils import get_characters_dir, get_npcs_dir


class DrupalSync:
    """Synchronize D&D data between local JSON and Drupal CMS."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        verify_ssl: bool = True
    ):
        """
        Initialize Drupal sync client.

        Args:
            base_url: Drupal base URL (e.g., "https://dnd-consultant.ddev.site")
            username: Drupal API user username
            password: Drupal API user password
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/jsonapi"
        self.auth = HTTPBasicAuth(username, password)
        self.verify_ssl = verify_ssl
        self.headers = {
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Make authenticated request to JSON:API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (e.g., "/node/character")
            data: Request body data
            params: Query parameters

        Returns:
            Response JSON data

        Raises:
            requests.HTTPError: On API error
        """
        url = f"{self.api_url}{endpoint}"
        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            auth=self.auth,
            json=data,
            params=params,
            verify=self.verify_ssl
        )
        response.raise_for_status()
        return response.json()

    def push_character(self, character_data: Dict) -> str:
        """
        Push a character to Drupal.

        Args:
            character_data: Character JSON data

        Returns:
            Drupal node UUID
        """
        # Map JSON fields to Drupal fields
        drupal_data = self._map_character_to_drupal(character_data)

        # Check if character exists
        existing = self._find_character_by_name(character_data["name"])

        if existing:
            # Update existing node
            node_id = existing["id"]
            self._request(
                "PATCH",
                f"/node/character/{node_id}",
                data=drupal_data
            )
            return node_id
        else:
            # Create new node
            response = self._request(
                "POST",
                "/node/character",
                data=drupal_data
            )
            return response["data"]["id"]

    def _map_character_to_drupal(self, data: Dict) -> Dict:
        """Map character JSON to Drupal JSON:API format."""
        return {
            "data": {
                "type": "node--character",
                "attributes": {
                    "title": data["name"],
                    "field_nickname": data.get("nickname"),
                    "field_level": data.get("level"),
                    "field_background": data.get("background"),
                    "field_backstory": data.get("backstory"),
                    "field_max_hp": data.get("max_hit_points"),
                    "field_armor_class": data.get("armor_class"),
                    "field_movement_speed": data.get("movement_speed"),
                    "field_proficiency_bonus": data.get("proficiency_bonus"),
                    "field_ai_enabled": data.get("ai_config", {}).get("enabled"),
                    "field_ai_temperature": data.get("ai_config", {}).get("temperature"),
                    "field_ai_max_tokens": data.get("ai_config", {}).get("max_tokens"),
                    "field_ai_system_prompt": data.get("ai_config", {}).get("system_prompt"),
                },
                "relationships": {
                    "field_species": {
                        "data": {"type": "taxonomy_term--species", "id": "UUID_HERE"}
                    },
                    "field_class": {
                        "data": {"type": "taxonomy_term--dnd_class", "id": "UUID_HERE"}
                    },
                }
            }
        }

    def _find_character_by_name(self, name: str) -> Optional[Dict]:
        """Find existing character node by name."""
        try:
            response = self._request(
                "GET",
                "/node/character",
                params={"filter[title]": name}
            )
            if response["data"]:
                return response["data"][0]
        except requests.HTTPError:
            pass
        return None

    def pull_character(self, node_uuid: str) -> Dict:
        """
        Pull a character from Drupal.

        Args:
            node_uuid: Drupal node UUID

        Returns:
            Character data in local JSON format
        """
        response = self._request("GET", f"/node/character/{node_uuid}")
        return self._map_drupal_to_character(response["data"])

    def _map_drupal_to_character(self, drupal_data: Dict) -> Dict:
        """Map Drupal JSON:API format to local JSON format."""
        attrs = drupal_data.get("attributes", {})
        rels = drupal_data.get("relationships", {})

        return {
            "name": attrs.get("title"),
            "nickname": attrs.get("field_nickname"),
            "level": attrs.get("field_level"),
            "background": attrs.get("field_background"),
            "backstory": attrs.get("field_backstory"),
            "max_hit_points": attrs.get("field_max_hp"),
            "armor_class": attrs.get("field_armor_class"),
            "movement_speed": attrs.get("field_movement_speed"),
            "proficiency_bonus": attrs.get("field_proficiency_bonus"),
            "ai_config": {
                "enabled": attrs.get("field_ai_enabled", False),
                "temperature": attrs.get("field_ai_temperature", 0.7),
                "max_tokens": attrs.get("field_ai_max_tokens", 1000),
                "system_prompt": attrs.get("field_ai_system_prompt", ""),
            },
            # Additional fields would be mapped here
        }

    def sync_all_characters(self, direction: str = "push") -> Dict[str, int]:
        """
        Sync all characters.

        Args:
            direction: "push" (JSON to Drupal) or "pull" (Drupal to JSON)

        Returns:
            Stats dictionary with counts
        """
        stats = {"created": 0, "updated": 0, "errors": 0}

        if direction == "push":
            characters_dir = get_characters_dir()
            for char_file in characters_dir.glob("*.json"):
                if ".example" in char_file.name:
                    continue
                try:
                    data = load_json_file(str(char_file))
                    existing = self._find_character_by_name(data["name"])
                    self.push_character(data)
                    if existing:
                        stats["updated"] += 1
                    else:
                        stats["created"] += 1
                except Exception as e:
                    print(f"Error syncing {char_file}: {e}")
                    stats["errors"] += 1

        return stats
```

### 6.5 Sync Strategy

**Recommended: Push from Python**

The Python application should push changes to Drupal because:

1. Python is the primary data entry point
2. JSON files are the source of truth
3. Drupal serves as visualization layer
4. Simpler than setting up Drupal webhooks

**Sync Triggers:**

1. **Manual sync:** CLI command to sync all data
2. **Automatic sync:** After character/story modifications
3. **Scheduled sync:** Cron job for periodic full sync

**CLI Integration:**

```python
# Add to dnd_consultant.py or create new sync command

def sync_to_drupal():
    """Sync all local data to Drupal CMS."""
    from src.integration.drupal_sync import DrupalSync
    from src.utils.file_io import load_json_file

    # Load Drupal config from .env
    config = load_drupal_config()

    sync = DrupalSync(
        base_url=config["DRUPAL_BASE_URL"],
        username=config["DRUPAL_USER"],
        password=config["DRUPAL_PASSWORD"]
    )

    # Sync all content types
    print("Syncing characters...")
    char_stats = sync.sync_all_characters("push")
    print(f"  Created: {char_stats['created']}, Updated: {char_stats['updated']}")

    print("Syncing NPCs...")
    npc_stats = sync.sync_all_npcs("push")
    print(f"  Created: {npc_stats['created']}, Updated: {npc_stats['updated']}")

    print("Syncing items...")
    item_stats = sync.sync_all_items("push")
    print(f"  Created: {item_stats['created']}, Updated: {item_stats['updated']}")

    print("Syncing stories...")
    story_stats = sync.sync_all_stories("push")
    print(f"  Created: {story_stats['created']}, Updated: {story_stats['updated']}")
```

---

## 7. Migration Plan

### 7.1 Migration Strategy Overview

```
Phase 1: Setup           Phase 2: Taxonomy      Phase 3: Content
+------------------+     +------------------+    +------------------+
| Install Drupal   |---->| Create vocabularies|--->| Migrate content  |
| Configure DDEV   |     | Import terms     |    | Verify data      |
| Enable modules   |     | Verify structure |    | Test API         |
+------------------+     +------------------+    +------------------+
                                                        |
                                                        v
                                                 Phase 4: RAG
                                                 +------------------+
                                                 | Create RAG entity|
                                                 | Migrate cache    |
                                                 | Test search      |
                                                 +------------------+
```

### 7.2 Phase 1: Drupal Setup

**Tasks:**

1. Initialize DDEV project
2. Install Drupal 10
3. Enable required modules
4. Create API user
5. Configure JSON:API

**Commands:**

```bash
# Create DDEV project
mkdir drupal && cd drupal
ddev config --project-type drupal --docroot web --create-docroot

# Install Drupal
ddev composer create drupal/recommended-project

# Install contrib modules
ddev composer require drupal/paragraphs drupal/entity_reference_revisions
ddev composer require drupal/jsonapi_extras drupal/restui
ddev composer require drupal/search_api drupal/facets
ddev composer require drupal/pathauto drupal/token

# Start and install
ddev start
ddev drush site:install standard --db-url=mysql://db:db@db/db

# Create API user
ddev drush user:create api_user --password=secure_password
ddev drush user:role:add administrator api_user
```

### 7.3 Phase 2: Taxonomy Migration

**Create vocabulary terms from existing data:**

```python
# scripts/migrate_taxonomies.py

import json
from pathlib import Path
from collections import defaultdict

def extract_unique_values():
    """Extract unique values for taxonomy terms from JSON files."""
    species = set()
    classes = set()
    traits = defaultdict(set)  # personality, ideal, bond, flaw
    locations = set()

    # Extract from characters
    char_dir = Path("game_data/characters")
    for char_file in char_dir.glob("*.json"):
        if ".example" in char_file.name:
            continue
        with open(char_file) as f:
            data = json.load(f)

        species.add(data.get("species"))
        classes.add(data.get("dnd_class"))

        for trait in data.get("personality_traits", []):
            traits["personality"].add(trait)
        for ideal in data.get("ideals", []):
            traits["ideal"].add(ideal)
        for bond in data.get("bonds", []):
            traits["bond"].add(bond)
        for flaw in data.get("flaws", []):
            traits["flaw"].add(flaw)

    # Extract from NPCs
    npc_dir = Path("game_data/npcs")
    for npc_file in npc_dir.glob("*.json"):
        if ".example" in npc_file.name:
            continue
        with open(npc_file) as f:
            data = json.load(f)

        species.add(data.get("species"))

    return {
        "species": sorted(filter(None, species)),
        "classes": sorted(filter(None, classes)),
        "traits": traits,
    }

def generate_drupal_migration():
    """Generate Drupal migration YAML files."""
    values = extract_unique_values()

    # Generate taxonomy term migration
    migration = {
        "id": "dnd_taxonomies",
        "migration_group": "dnd_content",
        "source": {
            "plugin": "embedded_data",
            "data_rows": [],
            "ids": ["id"]
        },
        "process": {
            "vid": "vocabulary",
            "name": "name",
        },
        "destination": {
            "plugin": "entity:taxonomy_term"
        }
    }

    # Add species terms
    for i, species in enumerate(values["species"]):
        migration["source"]["data_rows"].append({
            "id": f"species_{i}",
            "vocabulary": "species",
            "name": species
        })

    return migration
```

### 7.4 Phase 3: Content Migration

**One-time migration script:**

```python
# scripts/migrate_to_drupal.py

"""
One-time migration script to import all JSON data into Drupal.

Usage:
    python scripts/migrate_to_drupal.py --dry-run  # Preview changes
    python scripts/migrate_to_drupal.py            # Execute migration
"""

import argparse
import json
from pathlib import Path
from src.integration.drupal_sync import DrupalSync
from src.utils.file_io import load_json_file
from src.utils.path_utils import (
    get_characters_dir,
    get_npcs_dir,
    get_game_data_path
)


def load_drupal_config():
    """Load Drupal connection config from environment."""
    import os
    return {
        "base_url": os.getenv("DRUPAL_BASE_URL", "https://dnd-consultant.ddev.site"),
        "username": os.getenv("DRUPAL_USER", "api_user"),
        "password": os.getenv("DRUPAL_PASSWORD", ""),
    }


def migrate_characters(sync: DrupalSync, dry_run: bool = False):
    """Migrate all character JSON files to Drupal."""
    characters_dir = get_characters_dir()
    results = {"created": 0, "updated": 0, "skipped": 0, "errors": []}

    for char_file in sorted(characters_dir.glob("*.json")):
        if ".example" in char_file.name:
            continue

        print(f"Processing {char_file.name}...")

        try:
            data = load_json_file(str(char_file))
            if dry_run:
                print(f"  Would sync: {data['name']}")
                results["skipped"] += 1
            else:
                node_id = sync.push_character(data)
                print(f"  Synced: {data['name']} -> {node_id}")
                results["created"] += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            results["errors"].append({"file": str(char_file), "error": str(e)})

    return results


def migrate_npcs(sync: DrupalSync, dry_run: bool = False):
    """Migrate all NPC JSON files to Drupal."""
    npcs_dir = get_npcs_dir()
    results = {"created": 0, "updated": 0, "skipped": 0, "errors": []}

    for npc_file in sorted(npcs_dir.glob("*.json")):
        if ".example" in npc_file.name:
            continue

        print(f"Processing {npc_file.name}...")

        try:
            data = load_json_file(str(npc_file))
            if dry_run:
                print(f"  Would sync: {data['name']}")
                results["skipped"] += 1
            else:
                node_id = sync.push_npc(data)
                print(f"  Synced: {data['name']} -> {node_id}")
                results["created"] += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            results["errors"].append({"file": str(npc_file), "error": str(e)})

    return results


def migrate_items(sync: DrupalSync, dry_run: bool = False):
    """Migrate custom items registry to Drupal."""
    items_file = get_game_data_path() / "items" / "custom_items.json"
    results = {"created": 0, "updated": 0, "skipped": 0, "errors": []}

    if not items_file.exists():
        print("No custom items file found")
        return results

    data = load_json_file(str(items_file))

    for item_name, item_data in data.items():
        print(f"Processing item: {item_name}...")

        try:
            if dry_run:
                print(f"  Would sync: {item_name}")
                results["skipped"] += 1
            else:
                node_id = sync.push_item(item_data)
                print(f"  Synced: {item_name} -> {node_id}")
                results["created"] += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            results["errors"].append({"item": item_name, "error": str(e)})

    return results


def migrate_stories(sync: DrupalSync, dry_run: bool = False):
    """Migrate story markdown files to Drupal."""
    campaigns_dir = get_game_data_path() / "campaigns"
    results = {"created": 0, "updated": 0, "skipped": 0, "errors": []}

    for campaign_dir in sorted(campaigns_dir.iterdir()):
        if not campaign_dir.is_dir():
            continue

        campaign_name = campaign_dir.name
        print(f"\nProcessing campaign: {campaign_name}")

        for story_file in sorted(campaign_dir.glob("*.md")):
            # Skip generated files
            if any(x in story_file.name for x in ["session_results", "story_hooks", "character_development"]):
                continue

            print(f"  Processing {story_file.name}...")

            try:
                with open(story_file, encoding="utf-8") as f:
                    content = f.read()

                story_data = {
                    "title": story_file.stem,
                    "campaign": campaign_name,
                    "content": content,
                    "story_number": extract_story_number(story_file.name),
                }

                if dry_run:
                    print(f"    Would sync: {story_file.name}")
                    results["skipped"] += 1
                else:
                    node_id = sync.push_story(story_data)
                    print(f"    Synced: {story_file.name} -> {node_id}")
                    results["created"] += 1
            except Exception as e:
                print(f"    ERROR: {e}")
                results["errors"].append({"file": str(story_file), "error": str(e)})

    return results


def extract_story_number(filename: str) -> int:
    """Extract story number from filename like '001_start.md'."""
    import re
    match = re.match(r"(\d+)_", filename)
    return int(match.group(1)) if match else 0


def main():
    parser = argparse.ArgumentParser(description="Migrate D&D data to Drupal")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changes")
    args = parser.parse_args()

    print("=" * 60)
    print("D&D Character Consultant -> Drupal Migration")
    print("=" * 60)

    if args.dry_run:
        print("\n[DRY RUN MODE - No changes will be made]\n")

    config = load_drupal_config()

    if not config["password"]:
        print("ERROR: DRUPAL_PASSWORD environment variable not set")
        return

    sync = DrupalSync(
        base_url=config["base_url"],
        username=config["username"],
        password=config["password"]
    )

    # Run migrations
    print("\n--- Migrating Characters ---")
    char_results = migrate_characters(sync, args.dry_run)

    print("\n--- Migrating NPCs ---")
    npc_results = migrate_npcs(sync, args.dry_run)

    print("\n--- Migrating Items ---")
    item_results = migrate_items(sync, args.dry_run)

    print("\n--- Migrating Stories ---")
    story_results = migrate_stories(sync, args.dry_run)

    # Summary
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"Characters: {char_results['created']} created, {len(char_results['errors'])} errors")
    print(f"NPCs: {npc_results['created']} created, {len(npc_results['errors'])} errors")
    print(f"Items: {item_results['created']} created, {len(item_results['errors'])} errors")
    print(f"Stories: {story_results['created']} created, {len(story_results['errors'])} errors")


if __name__ == "__main__":
    main()
```

### 7.5 Phase 4: RAG Migration

**Migrate RAG cache to Drupal:**

```python
# scripts/migrate_rag_cache.py

"""
Migrate RAG cache from JSON files to Drupal database.
"""

import json
from pathlib import Path
from src.integration.drupal_sync import DrupalSync


def migrate_rag_cache(sync: DrupalSync, dry_run: bool = False):
    """Migrate RAG cache entries to Drupal."""
    cache_dir = Path(".rag_cache")
    index_file = cache_dir / "index.json"

    if not index_file.exists():
        print("No RAG cache found")
        return

    with open(index_file) as f:
        index = json.load(f)

    for cache_key, entry in index.items():
        cache_file = cache_dir / f"{cache_key}.json"
        if not cache_file.exists():
            continue

        with open(cache_file) as f:
            content = json.load(f)

        print(f"Migrating: {entry.get('title', cache_key)}")

        if not dry_run:
            sync.push_rag_entry({
                "source_url": entry.get("url", ""),
                "title": entry.get("title", ""),
                "content": content,
            })
```

### 7.6 Ongoing Sync Strategy

After initial migration, implement ongoing sync:

**Option A: Automatic Sync on Change**

```python
# Modify existing managers to trigger sync

class CharacterProfile:
    def save(self):
        # ... existing save logic ...

        # Trigger Drupal sync if configured
        if self.drupal_sync_enabled:
            self.sync_to_drupal()
```

**Option B: Scheduled Full Sync**

```bash
# Add to crontab or scheduled task
0 * * * * cd /path/to/project && python -m src.integration.sync_all
```

**Option C: Manual Sync Command**

```bash
# CLI command for manual sync
python dnd_consultant.py --sync-drupal
```

---

## 8. Future React Frontend

### 8.1 Decoupled Architecture

```
+-------------------+     +-------------------+     +-------------------+
| React Frontend    |     | Drupal CMS        |     | Python App        |
+-------------------+     +-------------------+     +-------------------+
|                   |     |                   |     |                   |
| Next.js/Remix     |<----| JSON:API          |<----| DrupalSync        |
| React Query       |     | REST API          |     | JSON Files        |
| Tailwind CSS      |     | Authentication    |     | RAG System        |
|                   |     |                   |     |                   |
+-------------------+     +-------------------+     +-------------------+
```

### 8.2 API-First Approach

Drupal is already configured for API-first with JSON:API. For React frontend:

1. **Keep JSON:API as primary API**
2. **Add CORS configuration** for local development
3. **Consider GraphQL** for complex queries

**CORS Configuration (settings.php):**

```php
// web/sites/default/settings.php
$settings['cors'] = [
  'enabled' => TRUE,
  'allowedHeaders' => ['*'],
  'allowedMethods' => ['*'],
  'allowedOrigins' => ['http://localhost:3000', 'http://localhost:5173'],
  'exposedHeaders' => FALSE,
  'maxAge' => FALSE,
  'supportsCredentials' => TRUE,
];
```

### 8.3 React Data Fetching

**Example React Query setup:**

```typescript
// src/api/characters.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

const API_BASE = 'https://dnd-consultant.ddev.site/jsonapi';

interface Character {
  id: string;
  type: string;
  attributes: {
    title: string;
    field_level: number;
    field_background: string;
    // ... other fields
  };
  relationships: {
    field_species: {
      data: { id: string; type: string };
    };
    field_class: {
      data: { id: string; type: string };
    };
  };
}

export function useCharacters() {
  return useQuery({
    queryKey: ['characters'],
    queryFn: async () => {
      const response = await fetch(
        `${API_BASE}/node/character?include=field_species,field_class`
      );
      if (!response.ok) throw new Error('Failed to fetch characters');
      return response.json();
    },
  });
}

export function useCharacter(id: string) {
  return useQuery({
    queryKey: ['character', id],
    queryFn: async () => {
      const response = await fetch(
        `${API_BASE}/node/character/${id}?include=field_species,field_class`
      );
      if (!response.ok) throw new Error('Failed to fetch character');
      return response.json();
    },
  });
}
```

### 8.4 Data Model Considerations

For React frontend, consider:

1. **Denormalize frequently accessed fields** (species name, class name) into
   character nodes for faster loading
2. **Use JSON:API includes** for related entities
3. **Implement caching** with React Query
4. **Consider computed fields** for derived data (ability modifiers, etc.)

**Example computed field in Drupal:**

```php
// web/modules/custom/dnd_content/src/Plugin/Field/FieldType/AbilityModifiersField.php

namespace Drupal\dnd_content\Plugin\Field\FieldType;

use Drupal\Core\Field\FieldItemBase;

/**
 * Computed field for ability modifiers.
 *
 * @FieldType(
 *   id = "ability_modifiers",
 *   label = @Translation("Ability Modifiers"),
 *   description = @Translation("Computed ability modifiers from scores"),
 *   no_ui = TRUE,
 *   computed = TRUE,
 * )
 */
class AbilityModifiersField extends FieldItemBase {
  // Implementation...
}
```

### 8.5 React Component Structure

```
src/
|-- components/
|   |-- Character/
|   |   |-- CharacterCard.tsx
|   |   |-- CharacterSheet.tsx
|   |   |-- AbilityScores.tsx
|   |   |-- EquipmentList.tsx
|   |   |-- SpellList.tsx
|   |   |-- RelationshipMap.tsx
|   |-- NPC/
|   |   |-- NPCCard.tsx
|   |   |-- NPCProfile.tsx
|   |-- Story/
|   |   |-- StoryReader.tsx
|   |   |-- StoryList.tsx
|   |-- Campaign/
|       |-- CampaignDashboard.tsx
|       |-- SessionTimeline.tsx
|-- pages/
|   |-- characters/
|   |   |-- index.tsx
|   |   |-- [id].tsx
|   |-- npcs/
|   |-- stories/
|   |-- campaigns/
|-- api/
|   |-- characters.ts
|   |-- npcs.ts
|   |-- stories.ts
|-- hooks/
|   |-- useCharacters.ts
|   |-- useNPCs.ts
|-- types/
    |-- character.ts
    |-- npc.ts
    |-- story.ts
```

---

## 9. Implementation Checklist

### Phase 1: Setup

- [ ] Initialize DDEV project
- [ ] Install Drupal 10
- [ ] Enable required modules (paragraphs, jsonapi, rest, search_api)
- [ ] Create API user with appropriate permissions
- [ ] Configure JSON:API and CORS

### Phase 2: Content Types

- [ ] Create Character content type with all fields
- [ ] Create NPC content type with all fields
- [ ] Create Story content type with all fields
- [ ] Create Item content type with all fields
- [ ] Create Session content type with all fields
- [ ] Create Paragraph types (relationships, ability_scores, skills)

### Phase 3: Taxonomies

- [ ] Create Traits vocabulary
- [ ] Create Species vocabulary
- [ ] Create Class vocabulary
- [ ] Create Location vocabulary
- [ ] Create Campaign vocabulary
- [ ] Create Story Tags vocabulary

### Phase 4: Python Integration

- [ ] Create `src/integration/drupal_sync.py`
- [ ] Implement character sync methods
- [ ] Implement NPC sync methods
- [ ] Implement item sync methods
- [ ] Implement story sync methods
- [ ] Add CLI commands for sync

### Phase 5: Migration

- [ ] Create taxonomy migration script
- [ ] Create content migration script
- [ ] Run dry-run migration
- [ ] Execute full migration
- [ ] Verify data integrity

### Phase 6: RAG Integration

- [ ] Create custom RAG entity in Drupal
- [ ] Implement RAG sync methods
- [ ] Configure Search API (optional)
- [ ] Test search functionality

### Phase 7: React Frontend (Future)

- [ ] Initialize React project
- [ ] Configure API client
- [ ] Build character components
- [ ] Build NPC components
- [ ] Build story reader
- [ ] Build campaign dashboard

---

## 10. Appendix

### A. Environment Variables

Add to `.env`:

```properties
# Drupal CMS Integration
DRUPAL_BASE_URL=https://dnd-consultant.ddev.site
DRUPAL_USER=api_user
DRUPAL_PASSWORD=your_secure_password
DRUPAL_SYNC_ENABLED=true
```

### B. JSON:API Example Requests

**Create Character:**

```bash
curl -X POST \
  https://dnd-consultant.ddev.site/jsonapi/node/character \
  -H "Content-Type: application/vnd.api+json" \
  -H "Accept: application/vnd.api+json" \
  -u api_user:password \
  -d '{
    "data": {
      "type": "node--character",
      "attributes": {
        "title": "Aragorn",
        "field_level": 10,
        "field_background": "Noble"
      }
    }
  }'
```

**Get Characters with Includes:**

```bash
curl -X GET \
  "https://dnd-consultant.ddev.site/jsonapi/node/character?include=field_species,field_class&fields[node--character]=title,field_level,field_background"
```

### C. Drupal Module Structure

```
web/modules/custom/dnd_content/
|-- dnd_content.info.yml
|-- dnd_content.module
|-- src/
|   |-- Entity/
|   |   |-- RagCache.php
|   |-- Plugin/
|   |   |-- Field/
|   |   |-- FieldType/
|   |-- Form/
|-- config/
|   |-- install/
|   |   |-- node.type.character.yml
|   |   |-- taxonomy.vocabulary.species.yml
|   |   |-- field.field.node.character.field_species.yml
|   |-- optional/
|-- tests/
```

### D. Related Files

- Character JSON schema: [`game_data/characters/aragorn.json`](game_data/characters/aragorn.json)
- NPC JSON schema: [`game_data/npcs/butterbur.json`](game_data/npcs/butterbur.json)
- Item JSON schema: [`game_data/items/custom_items.json`](game_data/items/custom_items.json)
- Story format: [`game_data/campaigns/Example_Campaign/001_start.md`](game_data/campaigns/Example_Campaign/001_start.md)
- RAG system: [`src/ai/rag_system.py`](src/ai/rag_system.py)
- Character validator: [`src/validation/character_validator.py`](src/validation/character_validator.py)
- NPC validator: [`src/validation/npc_validator.py`](src/validation/npc_validator.py)
