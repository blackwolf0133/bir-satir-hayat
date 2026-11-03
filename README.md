# Bir Satır Hayat

Instagram: **@birsatir.hayat** — her gün tek satırlık bir hayat dersi: suluboya masal çizimleri, el yazısı, sakin bir ses.

## Nasıl çalışır
1. **Hazırla** iş akışı sıradaki bölümü önceden üretir: 5 sahne aynı anda 5 makinede çizilir
   (FLUX.2-klein-4B, Apache-2.0, stable-diffusion.cpp ile CPU'da), sonra ses + yazı + imza ile birleştirilir
   ve `hazir-<id>` sürümüne konur. Önde 3 hazır bölüm olana kadar kendini tekrar başlatır.
2. **Günlük paylaşım** iş akışı her akşam ~22:30'da hazır olan sıradaki bölümü Reel olarak paylaşır.

## Yeni bölüm eklemek
`episodes/NNN_konu.json` — 5 sahne; her sahnede ekrana yazılacak `text` ve çizim için İngilizce `prompt`.
Karakterler `characters` içinde bir kez tarif edilir, sahnelerde `{AD}` diye kullanılır (sahneler arası tutarlılık).
Metinler tamamen özgün olmalı; başka sayfalardan söz alınmaz.

## Lisanslar
- Çizim: FLUX.2-klein-4B (Apache-2.0), metin kodlayıcı Qwen3-4B (Apache-2.0)
- Yazı tipi: Patrick Hand (SIL OFL, `assets/fonts/OFL-PatrickHand.txt`)
- Müzik: kod içinde sentetik olarak üretilir (telifsiz)
- Ses: kanal sahibinin kendi sesi; kayıt depoda yalnızca şifreli tutulur.
