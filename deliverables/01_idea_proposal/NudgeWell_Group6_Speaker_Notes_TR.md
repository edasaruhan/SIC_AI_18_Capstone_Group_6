# NudgeWell sunum metni (Türkçe)

**6. Grup · Fikir önerisi sunumu · 24 Eylül 2026**

Slaytlar İngilizce, bu metin sunumu Türkçe anlatmak için. Toplam süre yaklaşık 4 dakika.

---

## Slayt 1: Giriş ve fikir

*Yaklaşık 25 saniye*

Herkese merhaba, biz 6. grubuz. Fikrimizin adı NudgeWell, kendi isteğinizle kurduğunuz bir dijital denge koçu. Hepimiz bazen "artık telefonu bırakmalıyım" deyip yine de kaydırmaya devam ediyoruz. NudgeWell tam bu anlara odaklanıyor. Böyle bir anın geldiğini tahmin ettiğinde, sizin önceden seçtiğiniz küçük bir alternatifi öneriyor, mesela beş dakikalık bir yürüyüş.

---

## Slayt 2: Problem

*Yaklaşık 60 saniye*

Bugün telefonlardaki uyarıların birçoğu sadece süreye bakıyor. Mesela otuz dakika dolunca bir bildirim geliyor. Ama süre tek başına yeterli değil. Üstteki örnekte biri grup projesi için mesajlaşıyor, yani telefonu işi için kullanıyor, ama süre dolduğu için uyarı yine de geliyor. Alttaki örnekte ise kişi "artık bırakmalıyım" diye düşünüyor ama kaydırmaya devam ediyor. Süre sınırına gelmediği için de hiç uyarı almıyor. Yani uyarı, yardıma ihtiyaç olmadığında geliyor, ihtiyaç olduğunda gelmiyor. Bu ikinci duruma niyet-davranış farkı diyoruz, yani kişinin yapmak istediğiyle yaptığı arasındaki fark. AwareMind çalışmasında anlık değerlendirmelerin yüzde 14,9'unda kişi bırakmaya yakın bir puan vermiş ama beş dakikadan uzun süre telefonda kalmış. Yani yaklaşık her yedi andan birinde. Bizim hedefimiz toplam ekran süresi değil, işte bu an.

---

## Slayt 3: Çözümümüz

*Yaklaşık 60 saniye*

Peki NudgeWell bunu nasıl yapıyor? Dört adımda anlatalım. İlk adımda kullanıcı uygulamayı kuruyor ve kendine uygun birkaç alternatif seçiyor, mesela kısa bir yürüyüş, esneme ya da bir arkadaşını aramak. İkinci adımda uygulama, telefon kullanılırken o ana kadar olup bitenlere bakıyor. Saat kaç, hangi tür uygulama açık, bu oturum ne kadardır sürüyor, kişi ne kadar dokunup kaydırıyor ve daha önce telefonu nasıl kullanmış. Üçüncü adımda model bu bilgilere bakarak, kişinin şu an bırakmak isteyip yine de devam etme ihtimalini tahmin ediyor. Dördüncü adımda, uygulama bundan yeterince eminse kullanıcının kendi listesinden kısa bir öneri gösteriyor. Kullanıcı isterse tek dokunuşla kapatabiliyor. Emin değilse hiç araya girmiyor. Yani amaç kullanıcıyı sürekli uyarmak değil, sadece gerçekten gerektiğinde küçük bir hatırlatma yapmak.

---

## Slayt 4: Veri seti ve araştırma yaklaşımı

*Yaklaşık 85 saniye*

Modele bunu öğretmek için AwareMind veri setini kullanacağız. Bu veri Zheng ve Choe'nun 2026 çalışmasında toplandı ve 37 yetişkin Android kullanıcısından gelen 5.772 anlık değerlendirme içeriyor. Bizim için çok değerli, çünkü aynı an için hem kişinin ne dediğini hem de ne yaptığını kaydediyor. Telefon kullanılırken ekrana kısa bir soru geliyor ve kişi o an bırakması mı, devam etmesi mi gerektiğini 1'den 10'a kadar puanlıyor. 1 "bırakmalıyım", 10 "devam etmeliyim" demek. Sonra ekran kilitlenene kadar telefonu ne kadar daha kullandığı kaydediliyor. Bu ikisini yan yana koyunca, "bırakmalıyım demiş ama devam etmiş" anlarını açıkça görebiliyoruz. Model de tam bunu tahmin etmeyi öğrenecek. Tahmin yaparken sadece o ana kadarki bilgileri kullanacak, yani sonucu önceden görmeden tahmin edecek. Önce makaledekine benzer bir random forest ile başlayacağız, sonra kişinin önceki oturumlarını da hesaba katan küçük bir zamansal model deneyeceğiz. En sonunda modeli hiç görmediği yeni kişilerle test edeceğiz, yani uygulamayı ilk kez kullanan birinde de işe yarıyor mu, ona bakacağız. Kısacası NudgeWell süreye değil, kişinin kendi niyetine bakan bir koç. Dinlediğiniz için teşekkür ederiz.
