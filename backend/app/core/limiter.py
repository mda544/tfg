"""
Instancia compartida de slowapi.Limiter.
Importada tanto por main.py (para registrarla en app.state)
como por los routers (para decorar endpoints con @limiter.limit).
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)