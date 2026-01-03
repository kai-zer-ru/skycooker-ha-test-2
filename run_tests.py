#!/usr/bin/env python3
"""
Скрипт для запуска тестов интеграции SkyCooker
"""

import sys
import subprocess
import os

def run_tests():
    """Запуск тестов"""
    print("Запуск тестов для интеграции SkyCooker...")
    
    # Проверяем наличие pytest
    try:
        import pytest
    except ImportError:
        print("Ошибка: pytest не установлен. Установите его командой: pip install pytest")
        return False
    
    # Запускаем тесты
    test_dir = "tests"
    if not os.path.exists(test_dir):
        print(f"Ошибка: папка {test_dir} не найдена")
        return False
    
    # Запускаем pytest
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        test_dir, 
        "-v",  # verbose output
        "--tb=short"  # short traceback format
    ])
    
    return result.returncode == 0

if __name__ == "__main__":
    success = run_tests()
    if success:
        print("\n✅ Все тесты прошли успешно!")
        sys.exit(0)
    else:
        print("\n❌ Некоторые тесты не прошли")
        sys.exit(1)