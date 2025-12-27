#!/usr/bin/env python3
# debug_nbt.py - Диагностический скрипт для проверки работы с NBT файлами

import os
import sys
import nbtlib
from nbtlib import File, IntArray

def inspect_file(file_path):
    """Проверяет структуру NBT файла"""
    try:
        print(f"\n--- Инспекция файла: {os.path.basename(file_path)} ---")
        
        # Пробуем загрузить файл
        nbt_file = nbtlib.load(file_path)
        
        # Функция для рекурсивного обхода структуры
        def walk_nbt(obj, path="", depth=0):
            indent = "  " * depth
            
            if isinstance(obj, nbtlib.Compound):
                print(f"{indent}Compound ({len(obj)} ключей):")
                for key in obj.keys():
                    print(f"{indent}  Ключ: '{key}'")
                    walk_nbt(obj[key], f"{path}.{key}" if path else key, depth+2)
                    
            elif isinstance(obj, nbtlib.List):
                print(f"{indent}List[type={obj.subtype}] длина={len(obj)}:")
                if len(obj) <= 5:  # Показываем только первые 5 элементов
                    for i, item in enumerate(obj[:5]):
                        walk_nbt(item, f"{path}[{i}]", depth+1)
                else:
                    print(f"{indent}  ... и ещё {len(obj)-5} элементов")
                    
            elif isinstance(obj, IntArray):
                print(f"{indent}IntArray (длина={len(obj)}): {list(obj)}")
                # Проверяем, не UUID ли это (IntArray из 4 элементов)
                if len(obj) == 4:
                    print(f"{indent}  ВНИМАНИЕ: Это может быть UUID!")
                    
            elif isinstance(obj, (int, float, str)):
                print(f"{indent}{type(obj).__name__}: {obj}")
                
            else:
                print(f"{indent}{type(obj).__name__}")
        
        walk_nbt(nbt_file)
        return True
        
    except Exception as e:
        print(f"  ОШИБКА при чтении файла: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) < 2:
        print("Использование: python debug_nbt.py <путь_к_папке_world>")
        sys.exit(1)
    
    world_path = sys.argv[1]
    
    # Проверяем ключевые файлы
    test_files = [
        "level.dat",
        "playerdata/3f1aa5b9-3c2b-4e44-99ad-f6284e9f2e91.dat",  # Ваш файл
        "stats/3f1aa5b9-3c2b-4e44-99ad-f6284e9f2e91.dat",
        "advancements/3f1aa5b9-3c2b-4e44-99ad-f6284e9f2e91.dat",
    ]
    
    for file_name in test_files:
        file_path = os.path.join(world_path, file_name)
        if os.path.exists(file_path):
            inspect_file(file_path)
        else:
            print(f"\nФайл не найден: {file_path}")

if __name__ == "__main__":
    main()