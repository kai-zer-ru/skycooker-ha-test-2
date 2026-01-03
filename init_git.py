#!/usr/bin/env python3
"""
Скрипт для инициализации git репозитория и создания первого коммита
"""

import subprocess
import sys
import os

def run_git_command(command):
    """Выполнение git команды"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Ошибка выполнения команды: {command}")
            print(f"Ошибка: {result.stderr}")
            return False
        print(f"✅ {command}")
        if result.stdout.strip():
            print(f"   {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

def init_git_repo():
    """Инициализация git репозитория"""
    print("Инициализация git репозитория...")
    
    # Проверяем, существует ли уже репозиторий
    if os.path.exists(".git"):
        print("❌ Git репозиторий уже существует")
        return False
    
    # Инициализируем репозиторий
    if not run_git_command("git init"):
        return False
    
    # Добавляем файлы
    if not run_git_command("git add ."):
        return False
    
    # Создаем первый коммит
    if not run_git_command('git commit -m "Initial commit: SkyCooker integration for HomeAssistant"'):
        return False
    
    print("\n✅ Git репозиторий успешно инициализирован и первый коммит создан!")
    return True

def main():
    """Основная функция"""
    if not init_git_repo():
        print("\n❌ Ошибка при инициализации git репозитория")
        return False
    
    print("\n" + "=" * 60)
    print("Рекомендуемые действия:")
    print("1. Добавьте удаленный репозиторий:")
    print("   git remote add origin https://github.com/kai-zer-ru/skycooker-ha-test-2.git")
    print("2. Загрузите код в удаленный репозиторий:")
    print("   git push -u origin master")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)