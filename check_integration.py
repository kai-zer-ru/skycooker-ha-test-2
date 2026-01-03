#!/usr/bin/env python3
"""
Скрипт для проверки интеграции SkyCooker
"""

import os
import sys
import json

def check_file_exists(path, description):
    """Проверка существования файла"""
    if os.path.exists(path):
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ {description}: {path} - не найден")
        return False

def check_manifest():
    """Проверка manifest.json"""
    manifest_path = "custom_components/skycooker/manifest.json"
    if not check_file_exists(manifest_path, "Manifest файл"):
        return False
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        required_fields = ['domain', 'name', 'version', 'config_flow', 'requirements']
        for field in required_fields:
            if field not in manifest:
                print(f"❌ Manifest: отсутствует обязательное поле {field}")
                return False
        
        print(f"✅ Manifest: все обязательные поля присутствуют")
        return True
    except Exception as e:
        print(f"❌ Manifest: ошибка чтения файла: {e}")
        return False

def check_translations():
    """Проверка файлов переводов"""
    translations_dir = "custom_components/skycooker/translations"
    if not os.path.exists(translations_dir):
        print(f"❌ Папка переводов: {translations_dir} - не найдена")
        return False
    
    ru_file = os.path.join(translations_dir, "ru.json")
    en_file = os.path.join(translations_dir, "en.json")
    
    ru_exists = check_file_exists(ru_file, "Русский перевод")
    en_exists = check_file_exists(en_file, "Английский перевод")
    
    return ru_exists and en_exists

def check_core_files():
    """Проверка основных файлов интеграции"""
    files_to_check = [
        ("custom_components/skycooker/__init__.py", "Основной модуль"),
        ("custom_components/skycooker/const.py", "Константы"),
        ("custom_components/skycooker/btle.py", "Bluetooth модуль"),
        ("custom_components/skycooker/config_flow.py", "Конфигурационный поток"),
        ("custom_components/skycooker/sensor.py", "Сенсоры"),
        ("custom_components/skycooker/switch.py", "Переключатели"),
        ("custom_components/skycooker/number.py", "Числовые сущности"),
        ("custom_components/skycooker/select.py", "Выбор программ"),
    ]
    
    all_exist = True
    for file_path, description in files_to_check:
        if not check_file_exists(file_path, description):
            all_exist = False
    
    return all_exist

def check_documentation():
    """Проверка документации"""
    docs_to_check = [
        ("README.md", "Русская документация"),
        ("README_EN.md", "Английская документация"),
    ]
    
    all_exist = True
    for file_path, description in docs_to_check:
        if not check_file_exists(file_path, description):
            all_exist = False
    
    return all_exist

def check_tests():
    """Проверка тестов"""
    test_files = [
        ("tests/__init__.py", "Тестовый модуль"),
        ("tests/test_config_flow.py", "Тесты конфигурационного потока"),
    ]
    
    all_exist = True
    for file_path, description in test_files:
        if not check_file_exists(file_path, description):
            all_exist = False
    
    return all_exist

def main():
    """Основная функция проверки"""
    print("Проверка интеграции SkyCooker...")
    print("=" * 50)
    
    checks = [
        ("Основные файлы", check_core_files),
        ("Manifest", check_manifest),
        ("Переводы", check_translations),
        ("Документация", check_documentation),
        ("Тесты", check_tests),
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ Все проверки пройдены! Интеграция готова к использованию.")
        return True
    else:
        print("❌ Некоторые проверки не пройдены. Проверьте отчет выше.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)