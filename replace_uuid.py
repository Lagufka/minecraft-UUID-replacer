#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Полная и безопасная миграция UUID в мире Minecraft.
Поддержка:
- IntArray UUID [I; a, b, c, d]
- String UUID
- UUIDMost / UUIDLeast
Совместимо с nbtlib 2.x
"""

import os
import sys
import uuid
import yaml
import shutil
import argparse
from typing import Dict, Any, Tuple

import nbtlib
from nbtlib import File, Compound, List as NBTList, String, IntArray, Long

# ============================================================
# UUID helpers
# ============================================================

def to_signed(x: int) -> int:
    """Преобразует 32-битное число в signed int."""
    return x - 0x100000000 if x & 0x80000000 else x

def uuid_to_ints(uuid_str: str) -> list[int]:
    u = uuid.UUID(uuid_str)
    i = int(u.int)
    return [
        to_signed((i >> 96) & 0xFFFFFFFF),
        to_signed((i >> 64) & 0xFFFFFFFF),
        to_signed((i >> 32) & 0xFFFFFFFF),
        to_signed(i & 0xFFFFFFFF),
    ]

def uuid_to_most_least(uuid_str: str) -> Tuple[int, int]:
    u = uuid.UUID(uuid_str)
    return ((u.int >> 64) & 0xFFFFFFFFFFFFFFFF, u.int & 0xFFFFFFFFFFFFFFFF)

# ============================================================
# Config
# ============================================================

def load_config(path: str = "uuid_config.yml") -> Dict[str, Any]:
    """Загружает конфигурацию и подготавливает все формы UUID."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Файл конфигурации не найден: {path}")

    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if "from" not in cfg or "to" not in cfg:
        raise KeyError("Конфигурация должна содержать ключи 'from' и 'to'")

    old = cfg["from"]
    new = cfg["to"]

    return {
        "old_str": old,
        "new_str": new,
        "old_nodash": old.replace("-", ""),
        "new_nodash": new.replace("-", ""),
        "old_ints": uuid_to_ints(old),
        "new_ints": uuid_to_ints(new),
        "old_most_least": uuid_to_most_least(old),
        "new_most_least": uuid_to_most_least(new),
    }

# ============================================================
# File operations
# ============================================================

def safe_backup(path: str) -> str:
    """Создает резервную копию с уникальным именем."""
    backup_path = path + ".bak"
    counter = 1
    while os.path.exists(backup_path):
        backup_path = f"{path}.bak{counter}"
        counter += 1
    shutil.copy2(path, backup_path)
    return backup_path

def rename_file_if_needed(path: str, cfg: Dict[str, Any]) -> str:
    """Переименовывает файл, если в имени встречается UUID."""
    name = os.path.basename(path)
    new_name = name.replace(cfg["old_str"], cfg["new_str"]).replace(cfg["old_nodash"], cfg["new_nodash"])
    if new_name != name:
        new_path = os.path.join(os.path.dirname(path), new_name)
        if os.path.exists(new_path):
            os.remove(new_path)
        os.rename(path, new_path)
        print(f"  ↪ Переименован файл: {name} → {new_name}")
        return new_path
    return path

# ============================================================
# NBT processing
# ============================================================

def replace_intarray_uuid(obj: IntArray, cfg: Dict[str, Any]) -> bool:
    if len(obj) == 4 and [int(x) for x in obj] == cfg["old_ints"]:
        obj[:] = cfg["new_ints"]
        return True
    return False

def replace_string_uuid(obj: String, cfg: Dict[str, Any]) -> bool:
    text = str(obj)
    new_text = text.replace(cfg["old_str"], cfg["new_str"]).replace(cfg["old_nodash"], cfg["new_nodash"])
    if new_text != text:
        obj.value = new_text
        return True
    return False

def replace_compound_uuid(obj: Compound, cfg: Dict[str, Any]) -> int:
    count = 0
    # UUIDMost / UUIDLeast
    if "UUIDMost" in obj and "UUIDLeast" in obj:
        old_most, old_least = cfg["old_most_least"]
        if obj["UUIDMost"] == Long(old_most) and obj["UUIDLeast"] == Long(old_least):
            new_most, new_least = cfg["new_most_least"]
            obj["UUIDMost"] = Long(new_most)
            obj["UUIDLeast"] = Long(new_least)
            count += 1
    # Рекурсивная обработка
    for k, v in obj.items():
        count += replace_uuid_in_nbt(v, cfg)
    return count

def replace_nbtlist_uuid(obj: NBTList, cfg: Dict[str, Any]) -> int:
    count = 0
    for i, item in enumerate(obj):
        count += replace_uuid_in_nbt(item, cfg)
    return count

def replace_uuid_in_nbt(obj, cfg: Dict[str, Any]) -> int:
    """Рекурсивно заменяет все UUID в объекте NBT."""
    if isinstance(obj, IntArray):
        return int(replace_intarray_uuid(obj, cfg))
    elif isinstance(obj, String):
        return int(replace_string_uuid(obj, cfg))
    elif isinstance(obj, Compound):
        return replace_compound_uuid(obj, cfg)
    elif isinstance(obj, NBTList):
        return replace_nbtlist_uuid(obj, cfg)
    return 0

# ============================================================
# Text/JSON processing
# ============================================================

def process_textual_file(path: str, cfg: Dict[str, Any], stats: Dict[str, int], dry_run: bool, file_type: str):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read()
        new_data = data.replace(cfg["old_str"], cfg["new_str"]).replace(cfg["old_nodash"], cfg["new_nodash"])
        if new_data != data:
            if dry_run:
                print(f"  [dry-run] {file_type} файл с UUID: {path}")
            else:
                backup = safe_backup(path)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_data)
                os.remove(backup)
            stats[file_type] += 1
    except Exception:
        stats["errors"] += 1

def process_nbt_file(path: str, cfg: Dict[str, Any], stats: Dict[str, int], dry_run: bool):
    name = os.path.basename(path)
    if name.startswith("level") and name not in ("level.dat", "level.dat_old"):
        return
    try:
        nbt = nbtlib.load(path)
    except Exception as e:
        print(f"  ✗ Не удалось загрузить NBT: {name} ({e})")
        stats["errors"] += 1
        return
    count = replace_uuid_in_nbt(nbt, cfg)
    if count == 0:
        return
    if dry_run:
        print(f"  [dry-run] NBT UUID замен: {count} в {path}")
        stats["nbt"] += count
        return
    backup = safe_backup(path)
    try:
        nbt.save(path)
        os.remove(backup)
        stats["nbt"] += count
        print(f"    → UUID заменено: {count} в {name}")
    except Exception as e:
        shutil.copy2(backup, path)
        print(f"  ✗ Ошибка сохранения {name}: {e}")
        stats["errors"] += 1

# ============================================================
# World scan
# ============================================================

def scan_world(world: str, cfg: Dict[str, Any], dry_run: bool) -> Dict[str, int]:
    stats = {"nbt": 0, "json": 0, "text": 0, "errors": 0}
    for root, _, files in os.walk(world):
        for file in files:
            path = os.path.join(root, file)
            path = rename_file_if_needed(path, cfg)
            ext = os.path.splitext(path)[1].lower()
            if ext == ".dat":
                process_nbt_file(path, cfg, stats, dry_run)
            elif ext == ".json":
                process_textual_file(path, cfg, stats, dry_run, "json")
            elif ext in (".txt", ".properties", ".yml", ".yaml", ".mcmeta"):
                process_textual_file(path, cfg, stats, dry_run, "text")
    return stats

# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Замена UUID в мире Minecraft.")
    parser.add_argument("world", help="Путь к миру")
    parser.add_argument("--config", default="uuid_config.yml", help="Путь к YAML конфигурации")
    parser.add_argument("--dry-run", action="store_true", help="Проверка замен без изменения файлов")
    args = parser.parse_args()

    if not os.path.exists(args.world):
        print("Мир не найден")
        sys.exit(1)

    try:
        cfg = load_config(args.config)
    except Exception as e:
        print(f"Ошибка загрузки конфигурации: {e}")
        sys.exit(1)

    print(f"UUID: {cfg['old_str']} → {cfg['new_str']}")
    print(f"Начало миграции...{' [dry-run]' if args.dry_run else ''}\n")

    stats = scan_world(args.world, cfg, args.dry_run)

    print("\nГОТОВО")
    print(f"NBT замен: {stats['nbt']}")
    print(f"JSON замен: {stats['json']}")
    print(f"Text замен: {stats['text']}")
    print(f"Ошибок: {stats['errors']}")

if __name__ == "__main__":
    main()
