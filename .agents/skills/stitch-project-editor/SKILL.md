---
name: stitch-project-editor
description: Automated workflow and best practices for modifying Google Stitch UI projects using the Stitch MCP server, where the primary input provided is a Stitch Project ID. Use this skill whenever the user asks to modify, edit, add screens to, redesign, or update a Stitch project by providing a project ID (e.g. "projects/6027426941495902996" or "6027426941495902996").
---

# Stitch Project Editor

This skill provides standard operating procedures and best practices for inspecting, modifying, and creating screens or design systems within Google Stitch UI projects using the `StitchMCP` tools.

---

## 1. Input Processing & Parameter Normalization

Stitch MCP tools require different formats for project IDs depending on the specific tool schema:

| Tool | Format Expected | Example |
| :--- | :--- | :--- |
| `get_project` | Full resource name (`projects/{id}`) | `projects/6027426941495902996` |
| `list_screens` | Full parent name (`projects/{id}`) | `projects/6027426941495902996` |
| `edit_screens` | Raw ID only (without `projects/`) | `6027426941495902996` |
| `generate_screen_from_text` | Raw ID only (without `projects/`) | `6027426941495902996` |
| `get_screen` | Full screen name (`projects/{pId}/screens/{sId}`) | `projects/6027426941495902996/screens/1881038d...` |

**Rule:** Extract the raw numeric/alphanumeric project ID first, then format as needed for each tool.

---

## 2. Step-by-Step Workflow

### Step 1: Project Discovery & Context Retrieval
ALWAYS call `get_project` first using `projects/{projectId}`.

**Goals of Discovery:**
- Retrieve current project `deviceType` (`DESKTOP`, `MOBILE`, `TABLET`, `AGNOSTIC`).
- Inspect `screenInstances` to identify active screen IDs and layout positions.
- Extract any configured `designTheme` or `designSystem` asset references.

```json
// Tool: StitchMCP -> get_project
{
  "name": "projects/<PROJECT_ID>"
}
```

---

### Step 2: Determine Action & Select Tool

#### Scenario A: Editing Existing Screen(s)
When modifying an existing UI screen (e.g., "change the navbar color", "add a search filter to the main dashboard"):
1. Identify target `screenId`(s) from `get_project` (strip `projects/.../screens/` prefix).
2. Call `edit_screens`.

```json
// Tool: StitchMCP -> edit_screens
{
  "projectId": "<RAW_PROJECT_ID>",
  "selectedScreenIds": ["<SCREEN_ID_1>"],
  "prompt": "<Detailed description of changes>",
  "deviceType": "<DEVICE_TYPE_FROM_PROJECT>"
}
```

#### Scenario B: Generating a New Screen
When creating a new screen from scratch in the project:
1. Pass raw `projectId`.
2. Include project `deviceType`.
3. Include design system reference if available in project metadata.

```json
// Tool: StitchMCP -> generate_screen_from_text
{
  "projectId": "<RAW_PROJECT_ID>",
  "prompt": "<Detailed prompt for the new screen>",
  "deviceType": "<DEVICE_TYPE_FROM_PROJECT>",
  "designSystem": "<ASSET_ID_IF_AVAILABLE>"
}
```

#### Scenario C: Updating Design System / Theme
When updating color palettes, typography, or global design token markdown:
1. Use `upload_design_md` or `apply_design_system`.

---

## 3. Critical Execution & Resilience Rules

1. **Patience with Long Operations:**
   - Generation and edit operations in Stitch (`edit_screens`, `generate_screen_from_text`) can take **1 to 3 minutes**.
   - **DO NOT RETRY** immediately if the call times out or encounters a connection flicker.

2. **Timeout / Disconnection Recovery:**
   - If a tool call times out or throws a connection error, the process may still complete on Google Stitch servers.
   - Run `get_project` or `list_screens` 30 seconds after the error to check if the new screen/edit was committed.

3. **Output Component Suggestions:**
   - If `generate_screen_from_text` returns suggestions (e.g., `"Yes, make them all"`), present them to the user or accept relevant suggestions to continue generation.

---

## 4. Response & Output Delivery

After completing the edit or creation:
1. Summarize the changes applied to the project.
2. Output updated screen IDs, names, or download links provided by Stitch.
3. Offer next steps (e.g., generating additional variants via `generate_variants`, tweaking specific components, or exporting code).
