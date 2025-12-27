#!/usr/bin/env python3
# find_uuid_fixed.py - Поиск UUID в NBT файлах

import os
import sys
import uuid
import nbtlib
from nbtlib import IntArray

def uuid_to_ints(uuid_str):
    """Конвертирует UUID-строку в IntArray."""
    u = uuid.UUID(uuid_str)
    high = (u.int >> 64) & 0xFFFFFFFFFFFFFFFF
    low = u.int & 0xFFFFFFFFFFFFFFFF
    
    part1 = (high >> 32) & 0xFFFFFFFF
    part2 = high & 0xFFFFFFFF
    part3 = (low >> 32) & 0xFFFFFFFF
    part4 = low & 0xFFFFFFFF
    
    def to_signed(x):
        return x if x < 0x80000000 else x - 0x100000000
    
    return [to_signed(part1), to_signed(part2), 
            to_signed(part3), to_signed(part4)]

def search_in_nbt(file_path, target_ints):
    """Ищет UUID в NBT файле."""
    try:
        nbt_file = nbtlib.load(file_path)
        found_locations = []
        
        def search_obj(obj, path=""):
            if isinstance(obj, IntArray) and len(obj) == 4:
                if list(obj) == target_ints:
                    found_locations.append((path, list(obj)))
            
            if isinstance(obj, nbtlib.Compound):
                for key in obj.keys():
                    search_obj(obj[key], f"{path}.{key}" if path else key)
            
            elif isinstance(obj, nbtlib.List):
                for i, item in enumerate(obj):
                    search_obj(item, f"{path}[{i}]")
        
        search_obj(nbt_file, os.path.basename(file_path))
        return found_locations
        
    except Exception as e:
        # print(f"  Ошибка чтения {file_path}: {e}")
        return []

def main():
    if len(sys.argv) != 3:
        print("Использование: python find_uuid_fixed.py <путь_к_миру> <UUID>")
        print("Пример: python find_uuid_fixed.py ./world 3f1aa5b9-3c2b-4e44-99ad-f6284e9f2e91")
        sys.exit(1)
    
    world_path = sys.argv[1]
    uuid_str = sys.argv[2]
    target_ints = uuid_to_ints(uuid_str)
    
    print(f"Поиск UUID: {uuid_str}")
    print(f"Целевой IntArray: {target_ints}")
    print("=" * 60)
    
    found_count = 0
    
    # Проверяем ключевые файлы
    key_files = ["level.dat", f"playerdata/{uuid_str}.dat"]
    for file_name in key_files:
        file_path = os.path.join(world_path, file_name)
        if os.path.exists(file_path):
            locations = search_in_nbt(file_path, target_ints)
            for path, value in locations:
                print(f"✓ Найден в {file_name} по пути: {path}")
                print(f"  Значение: {value}")
                found_count += 1
    
    # Поиск во всех .dat файлах
    print(f"\nПоиск во всех .dat файлах...")
    for root, dirs, files in os.walk(world_path):
        for file in files:
            if file.endswith('.dat'):
                file_path = os.path.join(root, file)
                if file_path.endswith(uuid_str + '.dat'):
                    continue  # Уже проверили
                    
                locations = search_in_nbt(file_path, target_ints)
                for path, value in locations:
                    rel_path = os.path.relpath(file_path, world_path)
                    print(f"✓ Найден в {rel_path} по пути: {path}")
                    print(f"  Значение: {value}")
                    found_count += 1
    
    print(f"\n{'='*60}")
    print(f"Всего найдено: {found_count} вхождений")

if __name__ == "__main__":
    main()