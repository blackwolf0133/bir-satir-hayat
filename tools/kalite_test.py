"""Görsel kalite kontrolünü tek bir resim üzerinde dener. Kullanım: python tools/kalite_test.py <png> <tarif>"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.scenes import kalite
print("SONUÇ:", kalite(sys.argv[1], sys.argv[2]))
