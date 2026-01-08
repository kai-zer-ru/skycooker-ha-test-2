#!/usr/bin/env python3
# coding: utf-8

"""
Тесты для проверки работы с битовыми флагами в библиотеке SkyCooker.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from scripts.skycooker.lib.skycooker import SkyCooker
from scripts.skycooker.lib.const import MODE_DATA, MODEL_3, MODEL_1


class MockSkyCooker(SkyCooker):
    """Мок-класс для тестирования SkyCooker."""
    
    def __init__(self, model):
        super().__init__(model)
        self.command = AsyncMock(return_value=[1])
    
    async def command(self, command, params=None):
        """Мок-реализация метода command."""
        return await self._command(command, params)
    
    async def _command(self, command, params=None):
        """Внутренняя реализация метода command."""
        return [1]


@pytest.mark.asyncio
async def test_select_mode_with_bit_flags():
    """Тест проверки, что select_mode использует битовые флаги из MODE_DATA для моделей, отличных от MODEL_3."""
    model = "RMC-CBD100S"  # Модель, отличная от MODEL_3
    skycooker = MockSkyCooker(model)
    
    # Выбираем режим 1 (Multi-chef)
    mode = 1
    await skycooker.select_mode(mode)
    
    # Проверяем, что команда была вызвана с правильными параметрами
    assert skycooker.command.called
    call_args = skycooker.command.call_args
    
    # Проверяем, что битовые флаги были взяты из MODE_DATA
    mode_data = MODE_DATA.get(MODEL_1, [])
    expected_bit_flags = mode_data[mode][3]
    
    # Проверяем, что битовые флаги были переданы в команду
    assert call_args[0][1][8] == expected_bit_flags


@pytest.mark.asyncio
async def test_set_main_mode_with_bit_flags():
    """Тест проверки, что set_main_mode использует битовые флаги из MODE_DATA для моделей, отличных от MODEL_3."""
    model = "RMC-CBD100S"  # Модель, отличная от MODEL_3
    skycooker = MockSkyCooker(model)
    
    # Устанавливаем режим 2 (Multi-chef)
    mode = 2
    await skycooker.set_main_mode(mode)
    
    # Проверяем, что команда была вызвана с правильными параметрами
    assert skycooker.command.called
    call_args = skycooker.command.call_args
    
    # Проверяем, что битовые флаги были взяты из MODE_DATA
    mode_data = MODE_DATA.get(MODEL_1, [])
    expected_bit_flags = mode_data[mode][3]
    
    # Проверяем, что битовые флаги были переданы в команду
    assert call_args[0][1][8] == expected_bit_flags


@pytest.mark.asyncio
async def test_select_mode_with_custom_bit_flags():
    """Тест проверки, что select_mode может использовать пользовательские битовые флаги."""
    model = "RMC-CBD100S"  # Модель, отличная от MODEL_3
    skycooker = MockSkyCooker(model)
    
    # Выбираем режим 1 (Multi-chef) с пользовательскими битовыми флагами
    mode = 1
    custom_bit_flags = 0xFF  # Все флаги включены
    await skycooker.select_mode(mode, bit_flags=custom_bit_flags)
    
    # Проверяем, что команда была вызвана с правильными параметрами
    assert skycooker.command.called
    call_args = skycooker.command.call_args
    
    # Проверяем, что пользовательские битовые флаги были переданы в команду
    assert call_args[0][1][8] == custom_bit_flags


@pytest.mark.asyncio
async def test_set_main_mode_with_custom_bit_flags():
    """Тест проверки, что set_main_mode может использовать пользовательские битовые флаги."""
    model = "RMC-CBD100S"  # Модель, отличная от MODEL_3
    skycooker = MockSkyCooker(model)
    
    # Устанавливаем режим 2 (Multi-chef) с пользовательскими битовыми флагами
    mode = 2
    custom_bit_flags = 0xFF  # Все флаги включены
    await skycooker.set_main_mode(mode, bit_flags=custom_bit_flags)
    
    # Проверяем, что команда была вызвана с правильными параметрами
    assert skycooker.command.called
    call_args = skycooker.command.call_args
    
    # Проверяем, что пользовательские битовые флаги были переданы в команду
    assert call_args[0][1][8] == custom_bit_flags


@pytest.mark.asyncio
async def test_select_mode_with_model_3_no_bit_flags():
    """Тест проверки, что для MODEL_3 битовые флаги не добавляются."""
    model = "RMC-M40S"  # Модель MODEL_3
    skycooker = MockSkyCooker(model)
    
    # Выбираем режим 1 (Multi-chef)
    mode = 1
    await skycooker.select_mode(mode)
    
    # Проверяем, что команда была вызвана с правильными параметрами
    assert skycooker.command.called
    call_args = skycooker.command.call_args
    
    # Проверяем, что пакет данных не содержит bit_flags (длина 8 байт вместо 9)
    assert len(call_args[0][1]) == 8


@pytest.mark.asyncio
async def test_set_main_mode_with_model_3_no_bit_flags():
    """Тест проверки, что для MODEL_3 битовые флаги не добавляются."""
    model = "RMC-M40S"  # Модель MODEL_3
    skycooker = MockSkyCooker(model)
    
    # Устанавливаем режим 2 (Milk porridge)
    mode = 2
    await skycooker.set_main_mode(mode)
    
    # Проверяем, что команда была вызвана с правильными параметрами
    assert skycooker.command.called
    call_args = skycooker.command.call_args
    
    # Проверяем, что пакет данных не содержит bit_flags (длина 8 байт вместо 9)
    assert len(call_args[0][1]) == 8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])