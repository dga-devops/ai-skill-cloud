# ClickUp Config Reference — asset-cdk-clickup

## Location

Place `clickup.md` at the **project root** (committed to git).

```
project-root/
└── clickup.md
```

---

## Template

```markdown
# ClickUp Configuration

## Cloud Assets (asset-cdk-clickup)
cloud_assets_list_id: ""         # ID of "Cloud Resources" list in Asset Management
cloud_assets_list_name: "Cloud Resources"
asset_management_folder_id: ""   # ID of Asset Management folder
space_name: ""                    # e.g. "ITSM-ITC"
default_environment: "dev"        # sandbox | dev | uat | prod
```

---

## Field Reference

| Field | Required | Description |
|---|---|---|
| `cloud_assets_list_id` | Yes | ClickUp list ID where cloud asset tasks are stored |
| `cloud_assets_list_name` | Yes | Display name (usually "Cloud Resources") |
| `asset_management_folder_id` | Yes | Parent folder ID — used when creating the list for the first time |
| `space_name` | Yes | Space name — for display/confirmation only |
| `default_environment` | No | Fallback environment tag when not detectable from stack name (`sandbox`, `dev`, `uat`, `prod`) |

---

## Setup Flow

When `cloud_assets_list_id` is missing:

```
1. Call clickup_get_workspace_hierarchy (max_depth: 2)
2. Show available Spaces → Folders — ask user which folder to use
   (suggest "Asset Management" in "ITSM-ITC" if visible)
3. Ask: "Should I create a new list called 'Cloud Resources' in {{folder_name}}?"
   - Yes → call clickup_create_list_in_folder (folder_id, name: "Cloud Resources")
   - No  → ask user to select an existing list from the folder
4. Save cloud_assets_list_id and asset_management_folder_id to clickup.md
5. Confirm: "Config saved. Cloud assets will go to: {{list_name}}"
```

Note: Custom fields (ARN, Resource Type, etc.) are created automatically on first task creation
if they don't exist. ClickUp will store the field IDs after creation — save them to `clickup.md`
under `## Custom Field IDs` section for faster subsequent syncs.

---

## Custom Field IDs (auto-populated after first sync)

After the first successful sync, append the discovered custom field IDs to `clickup.md`:

```markdown
## Custom Field IDs
cf_arn_id: ""
cf_resource_type_id: ""
cf_stack_name_id: ""
cf_environment_id: ""
cf_aws_account_id: ""
cf_aws_region_id: ""
cf_version_id: ""
cf_encryption_id: ""
cf_public_access_id: ""
cf_last_deployed_id: ""
cf_security_notes_id: ""
```

These IDs are workspace-scoped — they stay the same for all projects using the same ClickUp workspace.

---

## Example (Filled In)

```markdown
# ClickUp Configuration

## Cloud Assets (asset-cdk-clickup)
cloud_assets_list_id: "901817099999"
cloud_assets_list_name: "Cloud Resources"
asset_management_folder_id: "901813114242"
space_name: "ITSM-ITC"
default_environment: "prod"

## Custom Field IDs
cf_arn_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
cf_resource_type_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
cf_stack_name_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
cf_environment_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
cf_aws_account_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
cf_aws_region_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
cf_version_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
cf_encryption_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
cf_public_access_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
cf_last_deployed_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
cf_security_notes_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```
