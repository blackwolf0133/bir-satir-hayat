# Senaryo formatı — Bir Satır Hayat

Her bölüm `episodes/NNN_kisa_ad.json`. Video ~18-25 sn: 5 sahne, her sahnede tek kısa cümle (ekrana el yazısıyla yazılır,
kanal sahibinin sesiyle sakin tonda okunur). Son sahnenin altında kanal imzası (çizgi + kalp + @birsatir.hayat) otomatik çıkar.

```json
{
  "id": "008",
  "slug": "kisa_ad",
  "title": "Başlık",
  "characters": {"MAN": "a young man with ..., wearing ...", "WOMAN": "a young woman with ..., wearing ..."},
  "scenes": [
    {"text": "Ekranda ve seste geçen Türkçe cümle.", "prompt": "English scene description using {MAN} ..."},
    ... (TAM 5 sahne)
  ],
  "caption": "Paylaşım metni: 1-2 duygusal cümle + soru 🤍\n\nBirine göndermeye davet eden kısa çağrı.",
  "hashtags": ["#birsatırhayat", "#hayatdersleri", "#anlamlısözler", "#duygusal", "#reels"]
}
```

## Metin kuralları
- **Tamamen özgün.** Başka sayfalardan, kitaplardan, ünlülerden söz alma veya çevirme. Bilinen viral sözlerin kalıbını kopyalama.
- Konu: genel hayat — aile (anne, baba, dede/nine, kardeş), dostluk, sevgi, kendine nazik olmak, sabır, umut, zaman,
  küçük mutluluklar, kayıp ve özlem (yumuşak), yeniden başlamak. Siyaset, din tartışması, ırk, kavga, şiddet yok.
- 5 cümle bir hikâye kurmalı: 1) dokunan bir giriş, 2-4) gelişme, 5) akılda kalan tek satırlık ders.
- Her cümle kısa: en fazla ~12 kelime. Ekranda iki satıra bölmek için `\n` kullanılabilir.
- "Sen" diye hitap et; izleyen kendini ya da birini görsün ve videoyu ona göndermek istesin.
- Sayıları yazıyla yaz. Tırnak (") kullanılabilir, okunmaz.

## Çizim (prompt) kuralları — model: FLUX.2-klein-4B
- Prompt İngilizce, 1-3 cümle, somut: kim, nerede, ne yapıyor, ışık/hava. Stil otomatik eklenir (suluboya masal kitabı).
- Karakterler `characters` içinde bir kez, belirgin şekilde tarif edilir (yaş, saç, renkli bir giysi) ve sahnelerde `{AD}` ile kullanılır.
  Aynı kişi her sahnede aynı tarifle çizilir — tutarlılık buradan gelir. Yaşlanan kişi için ayrı anahtar aç (ör. OLDMOM).
- Sahnede en fazla 2 ana kişi. İki kişiliyse kimin solda/sağda olduğunu ve ne yaptıklarını açık yaz.
- Yazı, tabela, telefon ekranı içeriği isteme (model yazı yazmamalı).
- Hüzünlü sahneler bile yumuşak ve sıcak olsun; korkutucu, kanlı, hastane yatağı, mezar gibi sert görüntüler yok.
- Mevsim/hava sahneler arasında tutarlı olsun (aynı hikâye aynı mevsim).

## Paylaşım metni
`caption` 1-3 kısa satır + 1 soru + birine göndermeye davet. Etiketler TAM 5 tane, ilki `#birsatırhayat`.
Motor açıklamanın sonuna "Görseller yapay zekâ ile çizildi" notunu kendisi ekler.
