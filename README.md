
# Minecraft UUID replacer
Tool to fully replace player UUIDs in Minecraft world files.

## Usage
```bash
python uuid_migrator.py <world_path> [--config <path_to_config>] [--dry-run]
```

## Config
Create `uuid_config.yml`:
```yaml
from: 'old-UUID' #example: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
to: 'new-UUID'
```
# Preview
```bash
python uuid_migrator.py ./world --config migration.yml --dry-run
```

# Apply
```bash
python uuid_migrator.py ./world --config migration.yml
```

# What it does
Scans world directory

Replaces UUID in:
 - NBT files (.dat, .dat_old, .mca)
 - JSON files
 - Text files

Shows replacement statistics

# Warning
Backup your world before running. Use ```--dry-run``` first
