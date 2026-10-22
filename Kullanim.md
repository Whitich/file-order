# File Order / Dosya Düzeni 4.0

## Dil seçimi

Varsayılan dil İngilizcedir. Üstteki **Language / Dil** menüsünden **Türkçe** veya **English** seçin. Seçim sonraki açılışta hatırlanır. Dil değiştirmek mevcut planı temizler; yeni hedef yolları için yeniden analiz edin.

Dil yalnızca arayüzü değil, oluşturulacak sınıf klasörlerini, günlük dosyası önekini ve karantina adını da belirler. İngilizcede Pictures, Projects, Text, Intact_Packages; Türkçede Resimler, Projeler, Metinler, Butun_Paketler oluşturulur. Özgün dosya adları ve önceden var olan klasörler otomatik çevrilmez. Eski günlükler iki dilde de listelenir ve geri alınabilir. Ayar dosyasının settings.json adı ve uygulama veri klasörü sabit kimlik olarak kalır.


İşlem ve ilerleme paneli artık sekmelerin üstündedir; küçük pencerede tablonun altında kaybolmaz. Tarama başlar başlamaz açık durum mesajı görünür ve ikinci tarama düğmeleri işlem bitene kadar pasifleşir. İşlem tamamlanınca düğmeler tekrar açılır. Arayüz hataları sessizce kaybolmak yerine bildirilir ve uygulamanın yerel günlük klasöründeki `hatalar.log` dosyasına kaydedilir.

Mükerrer taramak için uygulamayı yeniden açıp **Düzenlenmiş hedefte mükerrerleri bul** düğmesine bir kez basın. **Hızlı düzenleme** işareti bu düğmeyi etkilemez. Üst panelde tarama aşaması, dosya yolu, sayaç ve süre görünür. Liste sonuçlar doğrulandıktan sonra dolar; boş liste tek başına işlemin başlamadığı anlamına gelmez. Tarama dosyaları taşımaz veya silmez.

## İşlem ve ilerleme paneli

Alt panel her sekmede görünür. Çalışan işlemi, mevcut aşamayı, işlenen dosya/klasör yolunu ve geçen süreyi gösterir. Tarama, boyut inceleme, hızlı eleme, tam içerik okuma, bayt karşılaştırması, plan hazırlama, güvenlik kontrolü, taşıma, karantina, Geri Dönüşüm Kutusu'na gönderme ve geri alma ayrı aşamalar olarak görünür.

Toplam biliniyorsa o aşamanın sayacı ve yüzdesi gösterilir. Büyük dosya okuma ve karşılaştırmada dosyanın MB/GB ilerlemesi görünür. Klasör keşfinde toplam henüz bilinmediği için hareketli çubuk ve bulunan öğe sayısı gösterilir; tahmini yüzde uydurulmaz. Yüzde mevcut aşama veya dosya içindir ve yeni aşamada yeniden başlayabilir. İşlem bitince **TAMAMLANDI**, hata olursa **DURDU / HATA**, tarama durdurulursa **DURDURULDU** yazar. Boşta **HAZIR — İşlem çalışmıyor** görünür.

## Düzenlenmiş klasörde mükerrer arama

**Aynı dosyalar ve projeler** sekmesinde **Düzenlenmiş hedefte mükerrerleri bul** düğmesini kullanın. Bu düğme kayıtlı hedefi tarama kaynağı yapar; hızlı düzenleme ayarına bakmadan tam mükerrer taraması başlatır. Başka bir klasör için kaynak klasörü seçip **SEÇİLİ KLASÖRDE MÜKERRERLERİ BUL** deyin. Aynı kaynak/hedef seçimi artık mükerrer taramasını engellemez. Mükerrer taraması taşıma planı uygulamaz.

Bağımsız resim, TXT ve belgeler birebir içerikleriyle karşılaştırılır. Projeler, dünyalar ve bağlı paketler yalnızca bütün olarak karşılaştırılır. Mevcut şablondaki `Projeler` alt klasörleri, proje işaretleri eksik olsa da bütün kabul edilir. İki ayrı projedeki aynı CSS/resim/asset tek başına kopya listesine girmez. İki projenin tüm göreli dosya yolları ve içerikleri aynıysa bütün klasörler eşleşir. Farklı çıktılar veya ayarlar içeren projeler tam eşleşme sayılmaz.

**Her grupta bir kopya tut, diğerlerini seç** ile fazlalıkları topluca seçin. Kaldırma öncesinde hem içerik hem üst proje/paket sınırları tekrar kontrol edilir. **Karantina** uygulama geçmişinden geri alınabilir; **SİL** Windows Geri Dönüşüm Kutusu'na gönderir ve oradan geri yüklenir. Otomatik silme yapılmaz. Bağlantı içeren paketler ve ayrı dosyalar halinde duran bağlı medya setleri güvenlik için karşılaştırma dışında tutulabilir; açıklamaları uyarılar sekmesinde görünür.

## Paket sınıflandırma ve mevcut hedefe ekleme

Bilinen projeler artık genel belirsiz paket kuralından önce tanınır. Projeler `Projeler`, yaratıcı projeler `Tasarim_ve_3B/Projeler`, uygulama paketleri `Uygulamalar/Paketler` altında bütün tutulur. Masaüstü/indirme arşivleri ve ayrı proje kökleri içeren arşiv klasörleri, belirsiz bir dosya yüzünden tek paket sayılmaz. Bağlı veriler yine korunur. Aynı tür belgeler veya resimler içeren belirsiz koleksiyonlar ilgili türün `Butun_Koleksiyonlar` altına bütün alınabilir.

Aynı hedefi daha sonra yeniden seçebilirsiniz. `Resimler`, `PDF`, `Projeler` ve diğer mevcut sınıf klasörleri tekrar kullanılır. Sınıf klasörü için `(2)` oluşturulmaz. Yalnızca dosya çakışırsa yeni gelene numara eklenir. Proje/dünya/paket klasörü çakışırsa bütün pakete numara eklenir; iki projenin içeriği karıştırılmaz. Bağlı medya setinde gerçek dosya çakışması yoksa hedef set klasörü tekrar kullanılabilir. Her çalışma ayrı geçmiş kaydıdır.

Hedef klasör seçimi sonraki açılışta hatırlanır. Mevcut `Butun_Paketler` içindekileri düzeltmek için hedef olarak aynı ana düzenleme klasörünü seçip **Hedefteki paketleri yeniden incele** deyin. Bu yalnızca analiz ve plan hazırlar. Zaten doğru sınıfta olan paketler yerinde kalır; yanlış sınıflanmış bilinen projeler ve bağımsız dosyalar uygun mevcut sınıflara önerilir. Planı inceleyip uygulayın.

## Bütünlük düzeltmesi

Proje olmaması, bir klasörün bölünebileceği anlamına gelmez. Minecraft Java/Bedrock dünyaları, modlu sunucular, oyun kurulumları, çok dosyalı veritabanları, uygulama profilleri, sanal makineler ve sistem/uygulama yedekleri artık ayrıca tanınır. Bu klasörler bütün olarak `Butun_Paketler` altında sınıflandırılır. Alt dosyaları ayrı düzenlenmez. Üst paket içinden bir alt klasör seçmek de açık paket işaretleri varsa engellenir.

Bağımsız olduğu doğrulanamayan dosyaları içeren alt klasörler artık dağıtılmaz; bütün olarak `Butun_Paketler/Incelenecek_Paketler` altında tutulur. Önceki sürümün aşağıdaki derin sınıflandırma açıklaması, yalnızca bağımsız belgeler ve tanınan arşiv klasörleri için geçerlidir. Her özel uygulamanın tüm bağımlılıklarını otomatik çıkarmak garanti edilemez; özel paketleri elle bütün koruyun.

Masaüstündeki **Dosya Duzeni** kısayolunu kullanın. Açık eski pencereyi kapatıp tekrar açın.

## Tam düzenleme

Klasörü ve aynı diskte bir hedef seçin, **Klasörü analiz et** deyin. Plan artık otomatik hazırlanır. Kategori adetlerini, kaynakları, hedefleri ve koruma nedenlerini inceleyin. **TÜM HAZIR ÖĞELERİ DÜZENLE**, hangi satıra tıklamış olursanız olun tüm hazır öğeleri uygular. Yalnızca belli öğeler için ayrı **Yalnız seçilenleri uygula** düğmesini kullanın. Hedefi değiştirirseniz **Plan oluştur** ile güncelleyin.

Tüm normal alt klasörler, içlerinde tanınmayan dosya olsa da taranır. TXT, Markdown, Word, PDF, tablolar, sunumlar, fotoğraflar, RAW, tasarım, video, ses, kitap, font, kurulum, kod ve veri dosyaları sınıflandırılır. Tanınmayan bağımsız dosyalar atlanmaz; **Diger_Dosyalar / uzantı** altında toplanır. Uzantısızlar ayrı gruptur. Ad çakışmaları numara eklenerek çözülür; üzerine yazılmaz.

## Birlikte kalması gerekenler

- Açık proje işaretleri ve birbirine bağlı kod/kaynak yapıları bulunduğunda bütün klasör **Projeler** altına taşınır. İçindeki EXE, asset, PDF veya resimler ayrı sınıflandırılmaz.
- Uygulama ve DLL paketleri, yaratıcı proje ve medya klasörleri bütün tutulur.
- Aynı adlı fotoğraf/RAW/XMP eşlikçileri, video/altyazı setleri ve kaydedilmiş HTML sayfası/kaynak klasörü aynı hedef alt klasörüne taşınır. Dosya adları korunur. Bağlı setler kopya silme işleminden korunur.
- Bağımsız kaynak ve bağımlılık klasörleri bölünmeden **Paketler** altına alınır.
- **Bölünmeyecek klasör ekle** özel projeleri elle korur. Bu seçim artık uygulama kapatılsa da saklanır.

Tek bir EXE, PSD veya TXT, bütün arşivin proje sayılmasına artık neden olmaz. Proje tanıma yine işaret ve yapıya dayanır; her özel formatın tüm bağımlılıklarını çıkardığı garanti edilemez. Taşıma öncesinde projeleri kapatın ve planı inceleyin. Mutlak yollarla dış dosyalara başvuran uygulamaların bağlantıları yeni konumda güncelleme gerektirebilir.

## Az boş alan

Tarama dosya kopyalamaz. Aynı disk/volume içinde taşıma rename kullanır; dosya verisinin ikinci kopyasını oluşturmaz. 100 GB taşımak için 100 GB ek alan gerekmez. Küçük günlükler/dosya sistemi kayıtları için az miktarda alan gerekir. Farklı diske taşıma otomatik kopyalamaya dönüşmeden engellenir. Hedef, kaynak içinde bir alt klasör olabilir; hedef içerikleri yeniden sınıflandırılmaz.

## Hızlı mod ve kopyalar

**Hızlı düzenleme** büyük dosyaları okumadan envanter çıkarır; proje tanıma gerektiğinde birkaç küçük kod dosyasındaki yerel başvuruları inceleyebilir. Kopya bulmak için bu işareti kaldırıp analiz edin. Boyut ve yapı ile eleme, kısa içerik örneği, SHA-256 ve son olarak bayt karşılaştırması kullanılır. Büyük gerçek kopyaların tam okunması zaman alabilir. Resimler görsel benzerlikle değil, birebir dosya içeriğiyle karşılaştırılır.

**Her grupta bir kopya tut, diğerlerini seç** fazlalıkları topluca seçer. **Bunu tut** ile korunacak kopyayı değiştirebilirsiniz. Karantina aynı diskte ayrı klasöre taşır ve uygulamadan geri alınır; alan boşaltmaz. **SİL**, Windows Geri Dönüşüm Kutusu'na gönderir ve Windows kutusundan geri yüklenir. Windows kalıcı silme uyarısı gösterirse iptal ederek karantinayı kullanın.

## Geçmiş ve hatalar

Tarihli **İşlem geçmişi**, eski/yeni konumları saklar. Düzenleme ve karantina işlemlerini seçip geri alabilirsiniz. Günlükler %LOCALAPPDATA%\DosyaDuzeni içinde kalır. Geri alma var olan dosyanın üzerine yazmaz. Aynı öğeye birden fazla taşıma yaptıysanız son işlemden başlayın.

Taşıma adımlarından biri başarısız olursa tamamlanan adımlar otomatik geri alınmaya çalışılır; kayıt geçmişte tutulur. Geri alma da erişim hatası nedeniyle tamamlanamazsa bunu açıkça bildirir. Plan sonrası değişmiş öğeler yeniden analiz gerektirir. Her taşıma sonrası eski sonuçlar temizlenir.

Boş klasörler, sistem klasörleri ve bağlantılar **Korunanlar ve uyarılar** sekmesinde açıklanır. Boş kaynak klasörleri otomatik silinmez. Karantinayı veya geri dönüşüm kutusunu kalıcı boşaltırsanız dosyalar geri getirilemez. Geri alma konumları geri çevirir; sonradan yaptığınız içerik değişikliklerini geri çevirmez.
