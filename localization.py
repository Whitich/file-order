"""English/Turkish presentation and generated-name localization.

Canonical classification keys and source file names never depend on UI language.
"""
import json
import os
import re
from pathlib import Path

LANGUAGE = os.environ.get('FILE_ORDER_LANGUAGE','en')
FOLDERS = {
    'Tablolar':'Spreadsheets','Sunumlar':'Presentations','Resimler':'Pictures',
    'Videolar':'Videos','Sesler':'Audio','Arsivler':'Archives','Metinler':'Text',
    'E_Kitaplar':'Ebooks','Kurulumlar':'Installers','Uygulamalar':'Applications',
    'Disk_Kaliplari':'Disk_Images','Tasarim_ve_3B':'Design_and_3D',
    'Yazilim_Dosyalari':'Source_Files','Veri_ve_Ayarlar':'Data_and_Settings',
    'Yazi_Tipleri':'Fonts','Altyazilar':'Subtitles','Kisayollar':'Shortcuts',
    'Projeler':'Projects','Butun_Paketler':'Intact_Packages','Paketler':'Packages',
    'Kaynak_Klasorleri':'Resource_Folders','Bagimliliklar':'Dependencies',
    'Butun_Koleksiyonlar':'Intact_Collections','Incelenecek_Paketler':'Review_Packages',
    'Oyun_Dunyalari':'Game_Worlds','Oyun_ve_Sunucular':'Games_and_Servers',
    'Uygulama_Yedekleri':'Application_Backups','Veritabanlari':'Databases',
    'Sanal_Makineler':'Virtual_Machines','Uygulama_Profilleri':'Application_Profiles',
    'Calisma_Ortamlari':'Runtime_Environments','Veri_Paketleri':'Data_Packages',
    'Diger_Dosyalar':'Other_Files','Uzantisiz':'No_Extension',
    'Web_Sayfalari':'Web_Pages','Bagli_Setler':'Related_Sets',
}

_PAIRS = r'''Dosya Düzeni • Güvenli tarama ve düzenleme|File Order • Safe scanning and organization
DOSYA DÜZENİ  /  4.0|FILE ORDER  /  4.0
Dil değişti. Yeni dosya yolları için yeniden analiz edin.|Language changed. Analyze again to generate destination paths in this language.
Önce incele. Güvenle düzenle. İstediğinde geri al.|Inspect first. Organize safely. Undo when needed.
Kopyasız taşıma  •  Projeler bütün kalır  •  Tarihli işlem geçmişi|Move without copying  •  Projects stay intact  •  Dated operation history
Bir klasör seçerek başlayın. Hiçbir dosya otomatik silinmez.|Choose a folder to start. Files are never deleted automatically.
Klasör seç|Choose folder
Bölünmeyecek klasör ekle|Protect an intact folder
Klasörü analiz et|Analyze folder
Hızlı düzenleme (içerik karşılaştırması yapma)|Quick organization (skip content comparison)
Taramayı durdur|Stop scanning
Son işlemi geri al|Undo latest operation
Aynı dosyalar ve projeler|Duplicate files and projects
Düzenleme önizlemesi|Organization preview
İşlem geçmişi|Operation history
Korunanlar ve uyarılar|Protected items and notices
SEÇİLİ KLASÖRDE MÜKERRERLERİ BUL|FIND DUPLICATES IN SELECTED FOLDER
Düzenlenmiş hedefte mükerrerleri bul|Find duplicates in organized destination
Dosyalar içerikleriyle; projeler, dünyalar ve paketler bütün olarak kıyaslanır. Ortak CSS / asset tek başına silinmez.|Files are compared by content; projects, worlds and packages as whole units. Shared CSS/assets are never removed individually.
Tarama bitince fazlalıkları tek düğmeyle seçebilirsiniz. Silme otomatik yapılmaz.|After scanning, select excess copies with one click. Nothing is deleted automatically.
Her grupta bir kopya tut, diğerlerini seç|Keep one copy per group, select the rest
Bunu tut, grubun diğerlerini seç|Keep this copy, select its duplicates
Seçimleri temizle|Clear selection
Seçimi temizle|Clear selection
Resmi görmek için bir satıra tıklayın.|Click a row to preview its image.
Seçilenleri karantinaya taşı (geri alınabilir)|Quarantine selected items (undo available)
SİL — Geri Dönüşüm Kutusu’na gönder|DELETE — Send to Recycle Bin
01  Hedefi seç     →     02  Planı incele     →     03  Hazır öğeleri uygula|01  Choose destination     →     02  Review plan     →     03  Apply ready items
Bağımsız belgeler sınıflanır. Oyun dünyaları, uygulama verileri, projeler ve belirsiz paketler bütün kalır.|Independent documents are categorized. Game worlds, app data, projects and uncertain packages stay intact.
Hedef seç|Choose destination
Plan oluştur|Build plan
Hedefteki paketleri yeniden incele|Reinspect destination packages
Önce “Klasörü analiz et” düğmesini kullanın. Hızlı mod dosya içeriğini okumaz.|Start with Analyze folder. Quick mode skips full file-content reading.
TXT, PDF, Word, fotoğraf, video, ses, tasarım, kurulum ve diğer dosyalar dahil.|Includes text, PDF, Word, pictures, video, audio, design, installers and other files.
Neden / koruma|Reason / protection
Hazır öğelerin tümünü seç|Select all ready items
TÜM HAZIR ÖĞELERİ DÜZENLE|ORGANIZE ALL READY ITEMS
Yalnız seçilenleri uygula|Apply selected items only
Tarihli bir işlemi seçin; dosyaların eski ve yeni konumlarını inceleyip geri alın. Geçmiş uygulama kapatılsa da saklanır.|Select a dated operation, review original/new locations and undo it. History survives application restarts.
Geçmişi yenile|Refresh history
Seçilen işlemi geri al|Undo selected operation
Anlaşılamayan veya erişilemeyen öğeler taramayı durdurmaz. Nedenleri burada görünür.|Unrecognized or inaccessible items do not stop scanning. Their reasons appear here.
HAZIR — İşlem çalışmıyor|READY — No operation running
Bir işlem başlattığınızda aşaması ve ilerlemesi burada görünür.|The current stage and progress appear here when an operation starts.
Arayüz hatası|Interface error
Ayrıntı kaydedildi: |Details saved to: 
Bu hedefte Butun_Paketler klasörü bulunamadı.|No intact-package folder was found in this destination.
Bir kopya korunmalı|Keep at least one copy
Her grupta en az bir kopya bırakın.|Leave at least one copy in each group.
Her grupta en az bir öğeyi seçmeden bırakın.|Leave at least one item unselected in each group.
Seçilen kopyaları sil|Delete selected copies
 fazla kopya Windows Geri Dönüşüm Kutusu’na gönderilecek. Her grupta bir kopya kalacak.\n\nBunları geri almak için Windows Geri Dönüşüm Kutusu’nu kullanın. Devam edilsin mi?| excess copies will be sent to the Windows Recycle Bin. One copy per group will remain.\n\nRestore them through the Windows Recycle Bin. Continue?
Silme öncesi içerik doğrulaması|Verifying content before deletion
Dosyalar değişmiş; silme durduruldu: |Files changed; deletion stopped: 
İçerik değişti: |Content changed: 
Geri Dönüşüm Kutusu’na gönderiliyor|Sending to Recycle Bin
Windows Geri Dönüşüm Kutusu|Windows Recycle Bin
Geri Dönüşüm Kutusu’na silme|Delete to Recycle Bin
 kopya Geri Dönüşüm Kutusu’na gönderildi. Yeniden analiz edin.| copies sent to the Recycle Bin. Analyze again.
Mükerrerleri silme|Deleting duplicate copies
Bütün tutulacak klasör|Folder to keep intact
Korunan klasör kaydedildi. Yeniden tarayın: |Protected folder saved. Scan again: 
Önce devam eden işlemin tamamlanmasını bekleyin.|Wait for the running operation to finish first.
 başladı. İlerleme üst panelde gösteriliyor.| started. Progress is shown in the upper panel.
Tarama başladı. Sonuçlar tamamlandığında burada listelenecek; henüz silme yapılmıyor.|Scan started. Results will appear when complete; no deletion is taking place.
Başlatılıyor|Starting
TARAMA / İŞLEM SÜRÜYOR…|SCAN / OPERATION RUNNING…
Önce mevcut düzenleme hedefini seçin.|Choose an existing organization destination first.
Mükerrer tarama|Duplicate scan
Devam eden işlem: |Running operation: 
. İlerleme üst panelde.|. Progress is shown above.
Önce “Klasör seç” ile var olan bir klasör seçin.|Use Choose folder to select an existing folder first.
Klasör gerekli|Folder required
Klasörler inceleniyor; dosya kopyalanmıyor…|Inspecting folders; no files are being copied…
Klasör analizi|Folder analysis
Mükerrer taraması|Duplicate scanning
İşlem sürüyor…|Working…
 öğe • toplam belirleniyor| items • discovering total
 öğe • %| items • %
0 öğe|0 items
TAMAMLANDI  •  |COMPLETED  •  
DURDURULDU  •  |STOPPED  •  
DURDU / HATA  •  |STOPPED / ERROR  •  
İşlem tamamlanmadı|Operation did not complete
İşlem durdu. Tamamlanan taşımalar geçmişte saklanır. Devam etmeden yeniden analiz edin.|Operation stopped. Completed moves are recorded in history. Analyze again before continuing.
İşlem tamamlanamadı|Operation could not complete
Dosya konumları değişti. Yeni bir analiz başlatın.|File locations changed. Run a new analysis.
Bütün klasör|Intact folder
 öğe  •  | items  •  
 bütün korunan klasör  •  | protected intact folders  •  
 kopya grubu  •  | duplicate groups  •  
 saniye| seconds
 mükerrer grup • | duplicate groups • 
 fazla kopya • | excess copies • 
 toplam fazla içerik. Paketlerin içinden tek dosya listelenmez.| total excess content. Individual files inside packages are not listed.
Analiz hazır. Hedefi seçip “Plan oluştur” düğmesine basın.|Analysis ready. Select a destination and build the plan.
Analiz tamamlandı. |Analysis complete. 
 uyarı.| notices.
 Kopya bulmak için hızlı düzenleme işaretini kaldırıp analiz edin.| To find duplicates, disable quick organization or use Find duplicates.
 Aynı içerikler tam doğrulamayla karşılaştırıldı.| Matching content was fully verified.
Taşıma ön kontrolü|Move preflight checks
Kaynak yok veya bağlantı: |Source missing or a link: 
Hedef çakışması: |Destination conflict: 
Klasör kendi içine taşınamaz|A folder cannot be moved into itself
Farklı diske taşıma kapalı. Hedefi kaynakla aynı diskten seçin.|Cross-volume moves are disabled. Choose a destination on the source volume.
Karantinaya taşınıyor|Moving to quarantine
Dosyalar taşınıyor|Moving files
Hedef zaten var: |Destination already exists: 
Bağlantı taşınamaz: |Cannot move a link: 
Düzenleme durduruldu|Organization stopped
Taşıma durdu: |Move stopped: 
. Bazı adımlar geri alınamadı: |. Some steps could not be undone: 
. İşlem geçmişini kullanın.|. Use operation history.
Taşıma tamamlanamadı: |Move could not complete: 
. Önceki |. Previous 
 adım geri alındı. Ayrıntılar işlem geçmişinde.| steps were undone. See operation history for details.
Karantinaya taşı|Move to quarantine
 öğe karantinaya taşınacak. Kalıcı silme yapılmaz. Devam edilsin mi?| items will be quarantined. Nothing is permanently deleted. Continue?
Karantina öncesi içerik doğrulaması|Verifying content before quarantine
İçerik değişmiş veya eşit değil: |Content changed or does not match: 
Karantinaya taşındı. İşlem geçmişinden geri alabilirsiniz. Yeniden analiz edin.|Moved to quarantine. Undo through operation history. Analyze again.
Karantinaya taşıma|Quarantining items
Önce bir klasörü analiz edin ve hedef seçin.|Analyze a source folder and choose a destination first.
Kaynak klasörden farklı bir hedef seçin. Kaynak içinde “Duzenli” gibi bir alt klasör de olabilir.|Choose a destination different from the source. A child folder such as Organized is allowed.
Taşıma planı|Move plan
 bağlı öğe)| related items)
 dosya / bütün paket hazır  •  | files / intact packages ready  •  
 yerinde kalacak  •  Ek veri kopyası: 0 B| will remain in place  •  Additional data copy: 0 B
Plan hazır. Koruma nedenini görmek için bir satıra tıklayın. Uygulayana kadar hiçbir dosya taşınmaz.|Plan ready. Click a row for its protection reason. Nothing moves until you apply the plan.
 • Birlikte: | • Together: 
Planı uygula|Apply plan
 dosya / bütün paket (| files / intact packages (
 taşıma adımı) düzenlenecek. Projeler ve bağlı setler birlikte kalır. İşlem geçmişinden geri alınabilir. Devam edilsin mi?| move steps) will be organized. Projects and related sets stay together. Undo is available in history. Continue?
Plan güvenlik kontrolü|Plan safety checks
Plan hazırlandıktan sonra öğe değişti. Yeniden analiz edin: |Item changed after planning. Analyze again: 
Bu öğenin üst klasörü bütün korunması gereken paket olarak görünüyor. Yeniden analiz edin: |This item now belongs to an intact package. Analyze again: 
 öğe kopyalanmadan taşındı. İşlem geçmişinden geri alabilirsiniz.| items moved without copying. Undo is available in history.
Dosyaları düzenleme / taşıma|Organizing / moving files
Geri al|Undo
Geri alınabilecek işlem bulunamadı.|No operation is available to undo.
Windows Kutusu’ndan geri alınır|Restore through Windows Recycle Bin
Hata / geri alma kaydı|Error / rollback record
Geri alındı|Undone
Kısmen geri alındı|Partially undone
Taşındı / Kontrol edilebilir|Moved / available for review
Bu silmeyi Windows Geri Dönüşüm Kutusu’ndan geri yükleyin.|Restore this deletion through the Windows Recycle Bin.
Bu işlem zaten geri alınmış.|This operation has already been undone.
 öğe eski konumuna taşınacak. Var olan dosyaların üzerine yazılmaz. Devam edilsin mi?| items will return to their original locations. Existing files will not be overwritten. Continue?
 öğe eski konumuna taşındı. Yeniden analiz edin.| items restored to their original locations. Analyze again.
İşlemi geri alma|Undoing operation
Geri alma ön kontrolü|Undo preflight checks
Eski konum bir bağlantı olmuş; kontrol gerekli: |Original location is now a link; review required: 
Eski konumda farklı bir öğe var: |A different item exists at the original location: 
Eski konumda aynı isimli bir öğe var. Üzerine yazılmadı: |An item with the same name exists at the original location. Nothing was overwritten: 
Taşınan öğe bulunamadı. Sonraki işlemleri önce geri alın: |Moved item not found. Undo later operations first: 
Öğe bir bağlantıyla değiştirilmiş: |Item has been replaced by a link: 
Eski konuma yeni bir dosya geldi; üzerine yazılmadı: |A new file appeared at the original location; nothing was overwritten: 
Dosyalar eski konumuna taşınıyor|Restoring original locations
Silme tamamlanmadı veya iptal edildi: |Deletion did not complete or was cancelled: 
Tarama sırasında değişti: |Changed during scanning: 
Bağlantı içeren klasör karşılaştırılmadı: |Folder containing a link was not compared: 
 grupta birer kopya korunacak; | groups will retain one copy each; 
 fazla kopya seçildi. Henüz silinmedi.| excess copies selected. Nothing has been deleted.
Bu grupta korunacak kopya: |Copy to keep in this group: 
Vurgulanan satırlar kaldırılacak kopyalardır.|Highlighted rows are the copies selected for removal.
Resim önizlemesi yok|No image preview
Bu resim biçimi önizlenemedi.|This image format could not be previewed.
Klasör taranıyor|Scanning folders
Klasör taraması tamamlandı|Folder scan complete
Boyut ve klasör yapısı inceleniyor|Inspecting sizes and folder structure
Hızlı içerik elemesi|Quick content filtering
Tam içerik doğrulama|Full content verification
Dosya içeriği okunuyor|Reading file content
Bayt karşılaştırması|Byte-by-byte comparison
Eşleşmeler doğrulanıyor|Verifying matches
Mükerrer taraması tamamlandı|Duplicate scan complete
Taşıma planı hazırlanıyor|Building move plan
Taşıma planı hazır|Move plan ready
Minecraft dünya verisi; bütün klasör korunur|Minecraft world data; entire folder stays intact
Oyun kurulumu / modlu sunucu; dünya ve çalışma dosyaları birlikte korunur|Game installation / modded server; worlds and runtime files stay together
Oyun kaynak/mod paketi|Game resource/mod package
Sistem / uygulama yedeği; içi ayrıştırılmaz|System/application backup; contents are not separated
Çok dosyalı veritabanı|Multi-file database
Sanal makine ve diskleri birlikte korunur|Virtual machine and disks stay together
Tarayıcı / posta / uygulama profili|Browser/mail/application profile
Çalışma ortamı|Runtime environment
Bağlı oyun / uygulama verisi; tek tek ayrılmaz|Related game/application data; not split into individual files
Bağımsızlığı doğrulanamayan dosyalar içeriyor; klasör bütün korunur|Contains files whose independence is uncertain; entire folder stays intact
Veritabanı / ikili veri ve eşlikçileri birlikte korunur|Database/binary data and companions stay together
İşlem durduruldu. Dosyalara dokunulmadı.|Operation stopped. No files were modified.
Proje işareti: |Project marker: 
Unity proje yapısı|Unity project structure
Sürüm kontrolü klasörü|Version-control folder
Çözüm / oyun proje dosyası|Solution / game project file
Birbirine bağlı kod ve proje yapısı|Related source code and project structure
Yaratıcı proje ve bağlı medya klasörleri|Creative project and linked media folders
Uygulama ve çalışma dosyaları birlikte korunur|Application and runtime files stay together
Web sayfası ve yerel kaynakları|Web page and local resources
Kod yerel dosya/klasörlere başvuruyor|Code references local files/folders
Kod yerel modüllere başvuruyor|Code references local modules
HTML ve bağlı kaynak klasörü|HTML and linked resource folder
Medya ve aynı adlı eşlikçi dosyaları birlikte|Media and same-named companion files stay together
Üst proje işareti: |Parent project marker: 
Elle korunan üst klasör|Manually protected parent folder
Düzenleme şablonunda bütün korunan proje/paket|Intact project/package in the organization layout
Üst klasör proje/paket olarak korundu: |Parent folder is a protected project/package: 
Düzenleme hedefi; yeniden taramaya alınmadı|Organization destination; excluded from repeat scanning
Bağlantı/junction atlandı|Link/junction skipped
Sistem / bağımlılık / karantina klasörü korundu|System/dependency/quarantine folder protected
Bağımlılık klasörü bölünmeden taşınır|Dependency folder is moved intact
Bağımsız dosya|Independent file
Diğer dosya; uzantısına göre sınıflandırılacak|Other file; will be categorized by extension
Düzenleme şablonunda bütün proje / paket; yalnızca tümü kıyaslanır|Intact project/package in the layout; only compared as a whole
Elle korunan klasör|Manually protected folder
Kaynak klasörü bütün korunur|Resource folder stays intact
Boş klasör; dosya içermiyor ve yerinde kalacak|Empty folder; contains no files and will remain in place
Bağlantı içeren eşlikçi set yerinde bırakıldı|Related set containing a link was left in place
Erişilemedi; atlandı: |Inaccessible; skipped: 
Öğe tarama kapsamı dışında: |Item is outside the scan scope: 
Proje / paket içinden tek öğe kaldırılamaz; yeniden tarayın: |Cannot remove an individual item from a project/package; scan again: 
Bağlantı kaldırılamaz: |Cannot remove a link: 
Dosya okuma sırasında değişti: |File changed while being read: 
Bağlantı içeren klasör atlandı: |Folder containing a link was skipped: 
Bağlı medya seti kopya silmeden korundu|Related media set protected from duplicate removal
Hedef disk bulunamadı|Destination volume not found
Öğe artık bulunamıyor; yeniden tarayın|Item no longer exists; scan again
Bağlantı taşınmaz|Links are not moved
Hedef klasör kendi içine taşınmaz|Destination cannot be moved into itself
Hedef klasör yolunda aynı adlı bir dosya var; klasör oluşturulamaz|A file blocks the destination folder path
Zaten doğru sınıf klasöründe; yeniden taşınmaz|Already in the correct category; will not move again
Öğe kendi içine taşınamaz|An item cannot be moved into itself
Farklı disk: ek alan kullanmamak için taşınmayacak|Different volume: skipped to avoid using extra space
Eşlikçi dosya bağlantı veya farklı diskte|Companion is a link or on a different volume
Boyut|Size
Tam yol|Full path
Grup|Group
Dosya|File
Tür|Type
Kaynak|Source
Hedef|Destination
Durum|Status
Sınıf|Category
Tarih / saat|Date / time
İşlem|Operation
Öğe sayısı|Item count
Öğe|Item
Açıklama|Description
Bekleyin|Please wait
Hazır|Ready
Atlandı|Skipped
Belirsiz|Uncertain
Yerinde kalacak|Will remain in place
Yerinde kalır|Stays in place
Erişilemedi|Inaccessible
Taşıma|Move
Düzenleme|Organization
Karantina|Quarantine
öğe|items
Mükerrer|Duplicate
çözüm/proje dosyası|solution/project file
'''

TRANSLATIONS = dict(line.split('|', 1) for line in _PAIRS.splitlines() if '|' in line)
TRANSLATIONS = {k.replace('\\n','\n'):v.replace('\\n','\n') for k,v in TRANSLATIONS.items()}
TRANSLATIONS.update(FOLDERS)
_pattern=re.compile('|'.join(re.escape(k) for k in sorted(TRANSLATIONS,key=len,reverse=True)))
_paths=re.compile(r'[A-Za-z]:[\\/][^\n→•]*|\\\\[^\n→•]*')
_reverse={english:turkish for turkish,english in TRANSLATIONS.items() if turkish!=english}

def set_language(language):
    global LANGUAGE
    LANGUAGE=language if language in {'en','tr'} else 'en'

def load_language():
    # Stable storage identity intentionally does not change when the UI language changes.
    path=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'DosyaDuzeni'/'settings.json'
    if not path.exists():path=path.with_name('ayarlar.json')
    try: data=json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError):data={}
    set_language(os.environ.get('FILE_ORDER_LANGUAGE',data.get('language','en')))

def tr(value):
    if not isinstance(value,str): return value
    if LANGUAGE=='tr': return _reverse.get(value,value)
    # Preserve source paths, including Turkish file names, in mixed status messages.
    protected=[]
    def hide(match):
        protected.append(match.group());return f'\x00{len(protected)-1}\x00'
    text=_paths.sub(hide,value)
    text=_pattern.sub(lambda match:TRANSLATIONS[match.group()],text)
    return re.sub(r'\x00(\d+)\x00',lambda match:protected[int(match[1])],text)

def category_path(category,language=None):
    if (language or LANGUAGE)=='tr':return category
    result=[];literal=False
    for part in category.split('/'):
        result.append(part if literal else FOLDERS.get(part,part))
        if part in {'Bagli_Setler','Web_Sayfalari'}:literal=True
    return '/'.join(result)

def canonical_name(name):
    reverse={v.casefold():k.casefold() for k,v in FOLDERS.items()}
    return reverse.get(name.casefold(),name.casefold())

def generated_name(kind):
    names={'journal':('operation_','islem_'),'quarantine':('.FileOrder_Quarantine','.DosyaDuzeni_Karantina'),
           'organized':('_Organized','_Duzenli'),'errors':('errors.log','hatalar.log')}
    return names[kind][0 if LANGUAGE=='en' else 1]
