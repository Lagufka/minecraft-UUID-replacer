#!/usr/bin/env python3
# verify_migration.py - Проверка результатов миграции

import os
import sys
import json
import nbtlib
from nbtlib import IntArray

def check_uuid_in_file(file_path, target_uuid_str, target_ints):
    """Проверяет, остались ли старые UUID в файле."""
    import uuid
    
    old_uuid_str = target_uuid_str
    old_uuid_no_dash = old_uuid_str.replace('-', '')
    
    problems = []
    
    # Проверка NBT файлов
    if file_path.endswith('.dat'):
        try:
            nbt_file = nbtlib.load(file_path)
            
            def check_nbt(obj, path=""):
                if isinstance(obj, IntArray) and len(obj) == 4:
                    if list(obj) == target_ints:
                        problems.append(f"Найден старый UUID в {path}: {list(obj)}")
                
                if hasattr(obj, 'keys'):
                    for key in obj.keys():
                        check_nbt(obj[key], f"{path}.{key}" if path else key)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        check_nbt(item, f"{path}[{i}]")
            
            check_nbt(nbt_file, os.path.basename(file_path))
            
        except:
            pass
    
    # Проверка JSON и текстовых файлов
    else:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if old_uuid_str in content:
                problems.append(f"Текстовое вхождение старого UUID")
            elif old_uuid_no_dash in content:
                problems.append(f"Текстовое вхождение старого UUID (без дефисов)")
                
        except:
            pass
    
    # Проверка имени файла
    filename = os.path.basename(file_path)
    if old_uuid_str in filename or old_uuid_no_dash in filename:
        problems.append(f"Старый UUID в имени файла")
    
    return problems

def main():
    if len(sys.argv) != 3:
        print("Использование: python verify_migration.py <путь_к_миру> <старый-UUID>")
        print("Пример: python verify_migration.py ./world 3f1aa5b9-3c2b-4e44-99ad-f6284e9f2e91")
        sys.exit(1)
    
    world_path = sys.argv[1]
    old_uuid_str = sys.argv[2]
    
    # Конвертируем в IntArray для проверки
    import uuid
    u = uuid.UUID(old_uuid_str)
    high = (u.int >> 64) & 0xFFFFFFFFFFFFFFFF
    low = u.int & 0xFFFFFFFFFFFFFFFF
    part1 = (high >> 32) & 0xFFFFFFFF
    part2 = high & 0xFFFFFFFF
    part3 = (low >> 32) & 0xFFFFFFFF
    part4 = low & 0xFFFFFFFF
    
    def to_signed(x):
        return x if x < 0x80000000 else x - 0x100000000
    
    target_ints = [to_signed(part1), to_signed(part2), 
                   to_signed(part3), to_signed(part4)]
    
    print(f"Проверка миграции UUID: {old_uuid_str}")
    print(f"Целевой IntArray: {target_ints}")
    print("=" * 60)
    
    problem_files = []
    
    # Сканируем ключевые директории
    key_dirs = ['playerdata', 'stats', 'advancements', 'data']
    
    for root, dirs, files in os.walk(world_path):
        # Пропускаем ненужные папки
        if 'backup' in root.lower():
            continue
            
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, world_path)
            
            problems = check_uuid_in_file(file_path, old_uuid_str, target_ints)
            
            if problems:
                problem_files.append((rel_path, problems))
                print(f"⚠ {rel_path}")
                for problem in problems:
                    print(f"  → {problem}")
    
    print(f"\n{'='*60}")
    print(f"РЕЗУЛЬТАТ ПРОВЕРКИ:")
    print(f"Проверено файлов с проблемами: {len(problem_files)}")
    
    if len(problem_files) == 0:
        print(f"✅ Миграция выполнена успешно!")
    else:
        print(f"⚠ Найдены файлы со старым UUID")
        print(f"\nРекомендуется:")
        print(f"1. Проверить эти файлы вручную")
        print(f"2. При необходимости повторить миграцию")
        print(f"3. Или отредактировать файлы вручную")

if __name__ == "__main__":
    main()