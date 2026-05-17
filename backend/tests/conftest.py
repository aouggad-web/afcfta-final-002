import pytest
import sys

def pytest_runtest_setup(item):
    if 'currencies' in item.nodeid:
        import currencies.service as cs
        print(f'\n[DEBUG] Before {item.nodeid}')
        print(f'[DEBUG] id(currencies.service) = {id(cs)}')
        print(f'[DEBUG] _BY_COUNTRY len = {len(cs._BY_COUNTRY)}')
        print(f'[DEBUG] _DATA_FILE = {cs._DATA_FILE}')
        print(f'[DEBUG] _DATA_FILE.exists() = {cs._DATA_FILE.exists()}')
        
        # Check what list_currencies function sees
        from currencies.service import list_currencies
        print(f'[DEBUG] id(list_currencies) module = {id(sys.modules[list_currencies.__module__])}')
        print(f'[DEBUG] list_currencies() returns {len(list_currencies())} items')
