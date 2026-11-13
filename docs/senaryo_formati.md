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

## Haftalık trend raporu (last30days)
Her pazartesi blackwolf0133/cop-adamla-tarih deposundaki "Trend araştırma" iş akışı son 30 günün trendlerini 6 kanal için tarar
(YouTube, Reddit vb.; SCRAPECREATORS anahtarı varsa Instagram ve TikTok da). Yeni bölüm yazmadan önce en yeni raporu oku:

```bash
TAG=$(gh api "repos/blackwolf0133/cop-adamla-tarih/releases?per_page=20" --jq '[.[]|select(.tag_name|startswith("trend-"))][0].tag_name')
ID=$(gh api "repos/blackwolf0133/cop-adamla-tarih/releases/tags/$TAG" --jq '.assets[]|select(.name=="birsatir.md").id')
gh api -H "Accept: application/octet-stream" "repos/blackwolf0133/cop-adamla-tarih/releases/assets/$ID" > /tmp/trend.md
```
Bu kanalın dosyası: **birsatir.md**. Rapordaki tutan kanca kalıplarını, konu açılarını ve formatları kendi kurallarımıza uyarlayarak kullan;
başka içerik üreticilerinin metnini, videosunu ya da hikâyesini kopyalama. Rapor yoksa ya da eskiyse (14 günden eski) bu adımı atla.

---

## 13 Kasım: İLK 3 SANİYE kuralları (ZORUNLU, diğer kurallarla çelişirse bu geçerli)

Veri: 8 kanalda izleyici ortalama 5-13 sn'de kaydırıyor. Instagram videoyu önce küçük bir test grubuna gösteriyor; izlenme süresi, sona kadar izlenme ve DM ile gönderilme iyi değilse yaymıyor. Reels izleyicisi ~1,4 sn'de karar veriyor ve izlemelerin yarısından fazlası ses kapalı başlıyor.

**Motor ne yapıyor (otomatik):** Bir Satır'da kanca yazısı = 1. sahnenin üstteki metni; artık 0. karede tam görünür + ilk 0,8 sn hızlı zoom. Bu kanalda `kanca_yazi` alanı GEREKMEZ; 1. sahnenin metni kanca kurallarına uysun. (Diğer kanallarda: 0. saniyede ekranda büyük kanca yazısı ~3 sn.) Yazı bölümdeki `"kanca_yazi"` alanından gelir; yoksa açıklamanın (caption / instagram_caption) ilk satırından, o da uzunsa ilk cümlesinden. Bu yüzden:
- Her bölüme `"kanca_yazi"` ekle: en fazla 8 kelime, sessizken tek başına merak uyandıran cümle (cevabı vermeden). Seslendirilen ilk cümleyle aynı olmak zorunda değil ama aynı merakı açsın. (Son Mola'da bu alan sahne içindedir ve 2-3 kelimedir; orada mevcut kural geçerli.)
- Açıklamanın ilk satırı da kısa ve merak uyandıran olsun (yedek kanca yazısı olarak kullanılıyor).

**Kanca puanlama (yazdıktan sonra her bölüm için):** İlk seslendirilen cümleyi ve kanca_yazi'yi şu 5 türe göre 1-5 puanla, kendine sor: "Akışta kaydırırken 1,5 sn'de durur muydum?"
1. Ortak dert: izleyicinin yaşadığı ama dile getirmediği bir sıkıntı (Reels'te en güçlüsü)
2. Merak boşluğu: kapanması için izlemek gereken bir soru/boşluk
3. İddialı/ters köşe cümle: doğru ama şaşırtıcı, karşı çıkılası bir iddia
4. Kalıp kırma: beklenmedik bir giriş
5. Görsel şok: ilk karede açıklama isteyen bir görüntü
En yüksek puan 4'ün altındaysa ilk cümleyi yeniden yaz. Selamlama, giriş, "bugün size … anlatacağım", tarih/yer ile başlamak YASAK; en çarpıcı an ilk cümlede. Doğruluk kuralları aynen geçerli (abartı/uydurma yok).

**Gönderilme (DM) sebebi:** Instagram'da yeni kişilere ulaştıran en güçlü sinyal videonun DM ile birine gönderilmesi. Her bölümün SON seslendirilen cümlesi (ya da kapanış kartı alt yazısı), izleyicinin videoyu belirli birine göndermesi için doğal bir sebep versin; TEK cümle, dilenmeden: "Bunu her ay sonu batan arkadaşına gönder.", "Bunu gece yolculuğu seven birine gönder." Açıklamadaki tek çağrı kuralı aynen kalır (bu cümle videonun içinde).
