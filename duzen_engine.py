"""Read-only inventory and planning. No filesystem changes in this module."""
import hashlib
import os
import time
from localization import category_path,canonical_name
from pathlib import Path
from collections import defaultdict

MARKERS = {
    '.git', '.hg', '.svn', 'package.json', 'pyproject.toml', 'requirements.txt',
    'setup.py', 'setup.cfg', 'Cargo.toml', 'go.mod', 'go.work', 'pom.xml',
    'build.gradle', 'build.gradle.kts', 'settings.gradle', 'CMakeLists.txt',
    'project.godot', 'composer.json', 'Gemfile', 'pubspec.yaml', 'Makefile',
    'mix.exs', 'deno.json', 'bun.lockb', 'angular.json', 'vite.config.ts',
    'next.config.js', 'next.config.ts', 'next.config.mjs', 'Dockerfile',
    'UnityProjectSettings.asset', 'manifest.json', 'index.html',
}
DEPENDENCIES = {'node_modules', '.git', '.hg', '.svn', '.venv', 'venv', '__pycache__'}
SYSTEM = {'windows', 'program files', 'program files (x86)', 'appdata',
          '$recycle.bin', 'system volume information', 'programdata'}
SOURCE = {'.py', '.js', '.ts', '.tsx', '.jsx', '.cs', '.cpp', '.c', '.h',
          '.rs', '.go', '.java', '.php', '.gd', '.lua', '.sln', '.csproj',
          '.uproject', '.blend', '.aep', '.prproj', '.psd', '.indd', '.fig'}
ASSETS = {'assets', 'asset', 'textures', 'materials', 'meshes', 'shaders',
          'plugins', 'packages', 'projectsettings', 'src', 'source', 'bin',
          'obj', 'dist', 'build', 'resources', 'scripts', 'data', 'lib'}
CATEGORIES = {'PDF': {'.pdf'}, 'Word': {'.doc', '.docx', '.odt', '.rtf'},
    'Tablolar': {'.xls', '.xlsx', '.csv', '.ods'}, 'Sunumlar': {'.ppt', '.pptx', '.odp'},
    'Resimler': {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tif', '.tiff', '.heic', '.svg'},
    'Videolar': {'.mp4', '.mkv', '.avi', '.mov', '.webm'},
    'Sesler': {'.mp3', '.wav', '.flac', '.ogg', '.m4a'},
    'Arsivler': {'.zip', '.rar', '.7z', '.tar', '.gz'}}

CATEGORIES.update({
    'Metinler': {'.txt', '.text', '.md', '.markdown', '.log', '.rst', '.tex'},
    'Resimler': CATEGORIES['Resimler'] | {'.avif', '.jfif', '.jpe', '.ico', '.raw', '.cr2', '.cr3', '.nef', '.arw', '.dng', '.orf', '.rw2', '.psd', '.ai', '.eps', '.xcf', '.afphoto', '.afdesign'},
    'Videolar': CATEGORIES['Videolar'] | {'.m4v', '.wmv', '.flv', '.mts', '.m2ts', '.3gp', '.mpeg', '.mpg', '.ts'},
    'Sesler': CATEGORIES['Sesler'] | {'.aac', '.aiff', '.wma', '.opus', '.amr'},
    'E_Kitaplar': {'.epub', '.mobi', '.azw', '.azw3', '.djvu'},
    'Kurulumlar': {'.msi', '.msix', '.appx', '.apk', '.dmg', '.pkg', '.deb', '.rpm'},
    'Uygulamalar': {'.exe', '.com', '.app'},
    'Disk_Kaliplari': {'.iso', '.img', '.vhd', '.vhdx', '.vmdk'},
    'Tasarim_ve_3B': {'.blend', '.fbx', '.obj', '.stl', '.3ds', '.max', '.c4d', '.skp', '.dwg', '.dxf', '.fig', '.indd', '.aep', '.prproj'},
    'Yazilim_Dosyalari': {'.py', '.js', '.ts', '.tsx', '.jsx', '.cs', '.cpp', '.c', '.h', '.rs', '.go', '.java', '.php', '.gd', '.lua', '.ipynb', '.sh', '.bat', '.ps1', '.html', '.htm', '.css'},
    'Veri_ve_Ayarlar': {'.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.sql', '.db', '.sqlite', '.sqlite3'},
    'Yazi_Tipleri': {'.ttf', '.otf', '.woff', '.woff2'},
    'Altyazilar': {'.srt', '.ass', '.ssa', '.vtt', '.sub'},
    'Kisayollar': {'.lnk', '.url'},
})

CODE = {'.py','.js','.ts','.tsx','.jsx','.cs','.cpp','.c','.h','.rs','.go','.java','.php','.gd','.lua'}
PROJECT_EXT = {'.sln','.slnx','.csproj','.fsproj','.vbproj','.uproject','.xcodeproj'}
CREATIVE = {'.blend','.aep','.prproj','.max','.c4d','.indd'}
SIDECARS = {'.xmp','.aae','.thm','.lrv','.srt','.ass','.ssa','.vtt','.sub','.idx','.cue','.nfo'}
ARCHIVE_NAMES={'desktop','masaüstü','masaustu','downloads','download','dowloads','indirilenler','ind','documents','belgeler','old-backup','old_backup','backup','yedek','toplama','arşiv','arsiv','repos','repositories'}

def container_evidence(p):
    """A desktop/download archive is not an application just because it has a DLL."""
    if p.name.casefold() in ARCHIVE_NAMES: return True
    with os.scandir(p) as it: entries=list(it)
    files=[q for q in entries if q.is_file(follow_symlinks=False)]
    kinds={category(Path(q.name)) for q in files}-{None}
    if len(kinds)>=4: return True
    # A loose metadata file beside separate repositories must not hide them.
    # Only explicit child project markers qualify; generic asset names do not.
    for entry in entries:
        if not entry.is_dir(follow_symlinks=False) or entry.name.lower() in ASSETS or is_link(Path(entry.path)): continue
        try:
            with os.scandir(entry.path) as it: child_names={q.name for q in it}
            if child_names & (MARKERS-{'index.html','manifest.json','Dockerfile','Makefile','requirements.txt'}) or any(Path(n).suffix.lower() in PROJECT_EXT for n in child_names):
                return True
        except OSError: pass
    return False

def whole_category(p,reason):
    if 'Uygulama ve çalışma' in reason: return 'Uygulamalar/Paketler'
    if 'Yaratıcı proje' in reason: return 'Tasarim_ve_3B/Projeler'
    return 'Projeler'

def uncertain_category(p):
    with os.scandir(p) as it:
        files=[Path(q.path) for q in it if q.is_file(follow_symlinks=False)]
    metadata={'thumbs.db','desktop.ini','.ds_store','.nomedia','picasa.ini'}
    kinds=[category(q) for q in files if q.name.lower() not in metadata and category(q)]
    media={'Resimler','Videolar','Sesler','PDF','Word','Metinler','Tasarim_ve_3B'}
    if kinds and len(set(kinds))==1 and kinds[0] in media:
        return kinds[0]+'/Butun_Koleksiyonlar'
    return 'Butun_Paketler/Incelenecek_Paketler'

def integrity_boundary(p,root=False):
    specific=package_boundary(p,generic=False)
    if specific: return 'Butun_Paketler/'+specific[0],specific[1]
    reason=project_reason(p)
    if reason: return whole_category(p,reason),reason
    generic=package_boundary(p,generic=not root and not container_evidence(p))
    if generic:
        kind,reason=generic
        return uncertain_category(p) if kind=='Incelenecek_Paketler' else 'Butun_Paketler/'+kind,reason
    return None

def package_boundary(p, generic=True):
    """Recognize dependent data sets independently of software project markers."""
    with os.scandir(p) as it: entries=list(it)
    names={entry.name.lower() for entry in entries}
    files=[entry for entry in entries if entry.is_file(follow_symlinks=False)]
    exts={Path(entry.name).suffix.lower() for entry in files}
    dirs={entry.name.lower() for entry in entries if entry.is_dir(follow_symlinks=False)}
    if 'level.dat' in names or 'level.dat_old' in names or ('db' in dirs and 'levelname.txt' in names):
        return 'Oyun_Dunyalari','Minecraft dünya verisi; bütün klasör korunur'
    if {'libraries','versions'}<=dirs or {'mods','config'}<=dirs or ('server.properties' in names and ('.jar' in exts or 'world' in dirs)):
        return 'Oyun_ve_Sunucular','Oyun kurulumu / modlu sunucu; dünya ve çalışma dosyaları birlikte korunur'
    if names & {'pack.mcmeta','fabric.mod.json','manifest.mf'}:
        return 'Oyun_ve_Sunucular','Oyun kaynak/mod paketi'
    if len(dirs & {'program files','program files (x86)','appdata','windows','programdata'})>=2:
        return 'Uygulama_Yedekleri','Sistem / uygulama yedeği; içi ayrıştırılmaz'
    if names & {'current','lock'} and ('.sst' in exts or '.ldb' in exts) or '.gdb' in p.suffix.lower():
        return 'Veritabanlari','Çok dosyalı veritabanı'
    if exts & {'.vmx','.vbox','.vmcx'}:
        return 'Sanal_Makineler','Sanal makine ve diskleri birlikte korunur'
    if names & {'prefs.js','places.sqlite','local state','thunderbird.ini'} or {'mail','imapmail'} & dirs and 'prefs.js' in names:
        return 'Uygulama_Profilleri','Tarayıcı / posta / uygulama profili'
    if 'pyvenv.cfg' in names or {'bin','conda-meta'}<=dirs:
        return 'Calisma_Ortamlari','Çalışma ortamı'
    if generic:
        if exts & {'.mca','.mcr','.sav','.rpgsave','.rpa','.pak','.pck','.vpk','.wad','.db-wal','.db-shm','.sqlite-wal','.sqlite-shm'}:
            return 'Veri_Paketleri','Bağlı oyun / uygulama verisi; tek tek ayrılmaz'
        opaque=[entry for entry in files if category(Path(entry.name)) is None and Path(entry.name).suffix.lower() not in SIDECARS]
        if opaque:
            return 'Incelenecek_Paketler','Bağımsızlığı doğrulanamayan dosyalar içeriyor; klasör bütün korunur'
        if exts & {'.dat','.bin','.db','.sqlite','.sqlite3'} and (dirs or len(files)>1):
            return 'Veri_Paketleri','Veritabanı / ikili veri ve eşlikçileri birlikte korunur'
    return None

class Cancelled(Exception): pass

def notify(callback,phase,done=0,total=None,path='',unit='öğe'):
    callback({'phase':phase,'done':done,'total':total,'path':str(path),'unit':unit})

def check(stop):
    if stop is not None and stop.is_set(): raise Cancelled('İşlem durduruldu. Dosyalara dokunulmadı.')

def is_link(p):
    s = p.lstat()
    return p.is_symlink() or bool(getattr(s, 'st_file_attributes', 0) & 0x400)

def project_reason(p):
    """Explicit markers or combined evidence, never one generic file/dir name."""
    with os.scandir(p) as entries:
        entries = list(entries)
    names = {e.name for e in entries}
    lower = {n.lower() for n in names}
    markers = sorted(names & (MARKERS - {'manifest.json','index.html','Dockerfile','Makefile','requirements.txt'}))
    if markers: return 'Proje işareti: ' + ', '.join(markers[:3])
    if {'assets', 'projectsettings'} <= lower: return 'Unity proje yapısı'
    if lower & {'.git', '.hg', '.svn'}: return 'Sürüm kontrolü klasörü'
    files = [e for e in entries if e.is_file(follow_symlinks=False)]
    dirs = {e.name.lower() for e in entries if e.is_dir(follow_symlinks=False)}
    exts = {Path(e.name).suffix.lower() for e in files}
    if exts & PROJECT_EXT: return 'Çözüm / oyun proje dosyası'
    code = [e for e in files if Path(e.name).suffix.lower() in CODE]
    varied=len({category(Path(e.name)) for e in files if category(Path(e.name))})>3
    if code and (names & {'requirements.txt','Dockerfile','Makefile'} or dirs & ASSETS and not varied):
        return 'Birbirine bağlı kod ve proje yapısı'
    if exts & CREATIVE and dirs & (ASSETS | {'footage','media','cache','links','audio','images'}) and not varied:
        return 'Yaratıcı proje ve bağlı medya klasörleri'
    if not varied and (('.exe' in exts and ('.dll' in exts or any(n.endswith('_data') for n in dirs))) or ('.dll' in exts and dirs & ASSETS)):
        return 'Uygulama ve çalışma dosyaları birlikte korunur'
    if names & {'index.html','index.htm'} and (dirs & {'css','js','images','assets'} or exts & {'.css','.js'}):
        return 'Web sayfası ve yerel kaynakları'
    # Code with local file references is a bundle even without a manifest.
    for entry in code[:12]:
        try:
            if entry.stat().st_size > 131072: continue
            body = Path(entry.path).read_text(encoding='utf-8',errors='ignore')
            import re
            quoted = re.findall(r'''["']([^"'\r\n]{1,180})["']''', body)
            if any((Path(p)/value).exists() for value in quoted if not Path(value).is_absolute() and '..' not in Path(value).parts):
                return 'Kod yerel dosya/klasörlere başvuruyor'
            imports=re.findall(r'(?:from|import)\s+([A-Za-z_][\w.]*)',body)
            if any((Path(p)/(name.split('.')[0]+'.py')).exists() or (Path(p)/name.split('.')[0]).is_dir() for name in imports):
                return 'Kod yerel modüllere başvuruyor'
        except (OSError,ValueError): pass
    return ''

def category(p):
    return next((name for name, exts in CATEGORIES.items() if p.suffix.lower() in exts), None)

def organization_category(p):
    known=category(p)
    if known: return known
    ext=p.suffix.lower().lstrip('.')
    # Unknown independent files are accounted for instead of silently excluded.
    return 'Diger_Dosyalar/' + (ext.upper()[:30] if ext else 'Uzantisiz')

def related_sets(entries):
    """Keep sidecars, RAW/JPEG pairs, and saved HTML resources together."""
    by_name={entry.name.casefold():Path(entry.path) for entry in entries}
    sets=[]; consumed=set()
    for entry in entries:
        p=Path(entry.path)
        if p in consumed or not entry.is_file(follow_symlinks=False): continue
        if p.suffix.lower() in {'.html','.htm'}:
            resources=[by_name.get((p.stem+suffix).casefold()) for suffix in ('_files','_dosyalar','.files','_Dateien')]
            resources=[q for q in resources if q and q.is_dir() and not is_link(q)]
            if resources:
                sets.append((p,resources,'Web_Sayfalari/'+p.stem,'HTML ve bağlı kaynak klasörü'))
                consumed.update([p,*resources])
    grouped=defaultdict(list)
    for entry in entries:
        p=Path(entry.path)
        if p not in consumed and entry.is_file(follow_symlinks=False): grouped[p.stem.casefold()].append(p)
    for group in grouped.values():
        media=[p for p in group if category(p) in {'Resimler','Videolar','Sesler'}]
        sidecars=[p for p in group if p.suffix.lower() in SIDECARS]
        if not media or not sidecars and len(media)<2: continue
        anchor=media[0]
        related=[p for p in group if p in media or p in sidecars]
        if len(related)>1:
            sets.append((anchor,[p for p in related if p!=anchor],organization_category(anchor)+'/Bagli_Setler/'+anchor.stem,'Medya ve aynı adlı eşlikçi dosyaları birlikte'))
            consumed.update(related)
    return sets,consumed

def readable_size(n):
    for unit in ('B','KB','MB','GB','TB'):
        if n < 1024 or unit == 'TB': return f'{n:.1f} {unit}'
        n /= 1024

def layout_atomic(p):
    """Existing organizer labels carry an integrity boundary even without markers."""
    if canonical_name(p.parent.name)=='projeler': return True
    pair=(canonical_name(p.parent.parent.name),canonical_name(p.parent.name))
    if pair[0] in {'butun_paketler','paketler'}: return True
    if canonical_name(p.parent.name) in {'bagli_setler','butun_koleksiyonlar'}: return True
    if pair==('uygulamalar','paketler'): return True
    return False

def inventory(base, manual=(), stop=None, progress=lambda s: None, exclude=(), purpose='organize'):
    base = Path(base).resolve()
    units, issues = [], []
    manual = {Path(p).resolve() for p in manual}
    exclude = {Path(p).resolve() for p in exclude if Path(p).resolve()!=base}
    if purpose=='duplicates': exclude=set()
    # Selecting Assets/src directly must not bypass the parent project's boundary.
    for parent in base.parents:
        check(stop)
        if parent == Path(parent.anchor): break
        try:
            # Broad heuristics (e.g. a .js in Temp) are only used for the folder
            # being inventoried. An ancestor needs an explicit project marker.
            with os.scandir(parent) as it: names={entry.name for entry in it}
            strong=(names & (MARKERS-{'index.html','manifest.json','Dockerfile','Makefile','requirements.txt'}))
            if any(Path(name).suffix.lower() in PROJECT_EXT for name in names): strong.add('çözüm/proje dosyası')
            reason = 'Üst proje işareti: '+', '.join(sorted(strong)) if strong else ''
            boundary=package_boundary(parent,generic=False)
            if boundary: reason=boundary[1]
            if parent in manual: reason='Elle korunan üst klasör'
            if purpose=='duplicates' and layout_atomic(parent): reason='Düzenleme şablonunda bütün korunan proje/paket'
            if reason:
                issues.append((str(base), 'Üst klasör proje/paket olarak korundu: ' + str(parent)))
                return [], issues
        except OSError: pass
    count = 0
    visited=0
    notify(progress,'Klasör taranıyor',path=base)
    def visit(p, root=False):
        nonlocal count,visited
        visited+=1
        if visited%100==0: notify(progress,'Klasör taranıyor',len(units),path=p)
        check(stop)
        try:
            if p in exclude:
                issues.append((str(p),'Düzenleme hedefi; yeniden taramaya alınmadı')); return
            if is_link(p):
                issues.append((str(p),'Bağlantı/junction atlandı')); return
            if p.name.lower() in SYSTEM or p.name.startswith(('.DosyaDuzeni','.FileOrder_Quarantine')):
                issues.append((str(p),'Sistem / bağımlılık / karantina klasörü korundu')); return
            if p.name in DEPENDENCIES and p.is_dir():
                units.append({'path':p,'folder':True,'size':None,'category':'Paketler/Bagimliliklar','reason':'Bağımlılık klasörü bölünmeden taşınır'})
                return
            if p.is_file():
                s = p.stat()
                units.append({'path':p, 'folder':False, 'size':s.st_size,
                              'category':organization_category(p), 'reason':'Bağımsız dosya' if category(p) else 'Diğer dosya; uzantısına göre sınıflandırılacak'})
                return
            if purpose=='duplicates' and layout_atomic(p):
                units.append({'path':p,'folder':True,'size':None,'category':'Butun_Paketler','reason':'Düzenleme şablonunda bütün proje / paket; yalnızca tümü kıyaslanır'})
                return
            # Specific integrity boundaries precede archives; generic uncertainty
            # never hides a known project or an ordinary download container.
            boundary=('Projeler','Elle korunan klasör') if p in manual else integrity_boundary(p,root)
            if boundary:
                cat,reason=boundary
                units.append({'path':p,'folder':True,'size':None,'category':cat,'reason':reason})
                return
            with os.scandir(p) as it: entries = sorted(it, key=lambda e:e.name.casefold())
            if p.name.lower() in ASSETS:
                units.append({'path':p,'folder':True,'size':None,'category':'Paketler/Kaynak_Klasorleri','reason':'Kaynak klasörü bütün korunur'})
                return
            if not entries:
                issues.append((str(p),'Boş klasör; dosya içermiyor ve yerinde kalacak'))
            bundles,consumed=related_sets(entries)
            for anchor,companions,cat,reason in bundles:
                if any(is_link(q) for q in (anchor,*companions)):
                    issues.append((str(anchor),'Bağlantı içeren eşlikçi set yerinde bırakıldı'))
                    continue
                units.append({'path':anchor,'folder':False,'size':anchor.stat().st_size,'category':cat,'reason':reason,'companions':companions})
            # Every unprotected archive is traversed, including mixed unknown files.
            for entry in entries:
                if Path(entry.path) not in consumed: visit(Path(entry.path))
            count += 1
            if count % 25 == 0: notify(progress,'Klasör taranıyor',len(units),path=p)
        except OSError as e:
            issues.append((str(p), 'Erişilemedi; atlandı: '+str(e)))
    visit(base, True)
    notify(progress,'Klasör taraması tamamlandı',len(units),len(units),base)
    return units, issues

def assert_removable_unit(p,folder,base,manual=()):
    """Revalidate ancestors immediately before duplicate removal."""
    p=Path(p).resolve();base=Path(base).resolve();manual={Path(q).resolve() for q in manual}
    if p!=base and base not in p.parents: raise ValueError('Öğe tarama kapsamı dışında: '+str(p))
    for ancestor in p.parents:
        if ancestor==base.parent: break
        if ancestor in manual or layout_atomic(ancestor) or integrity_boundary(ancestor,root=ancestor==base):
            raise ValueError('Proje / paket içinden tek öğe kaldırılamaz; yeniden tarayın: '+str(p))
    if is_link(p): raise ValueError('Bağlantı kaldırılamaz: '+str(p))

def stat_key(p):
    s=p.stat()
    return s.st_size, s.st_mtime_ns, s.st_ino, s.st_dev

def hash_file(p, stop=None, sample=False, progress=None):
    before=stat_key(p); h=hashlib.sha256()
    read=0;last=0
    with p.open('rb') as f:
        if sample:
            for pos in sorted({0,max(0,before[0]//2-32768),max(0,before[0]-65536)}):
                check(stop); f.seek(pos); h.update(f.read(65536))
        else:
            while True:
                check(stop); block=f.read(1024*1024)
                if not block: break
                h.update(block)
                read+=len(block)
                now=time.monotonic()
                if progress and (now-last>.12 or read==before[0]):
                    last=now;notify(progress,'Dosya içeriği okunuyor',read,before[0],p,'bayt')
    if before != stat_key(p): raise ValueError('Dosya okuma sırasında değişti: '+str(p))
    return h.hexdigest()

def folder_shape(p, stop=None):
    shape=[]
    def fail(e): raise e
    for root,dirs,files in os.walk(p, onerror=fail, followlinks=False):
        check(stop)
        for name in dirs+files:
            q=Path(root)/name
            if is_link(q): raise ValueError('Bağlantı içeren klasör atlandı: '+str(q))
        for name in dirs: shape.append((str((Path(root)/name).relative_to(p))+'/',-1))
        for name in files:
            q=Path(root)/name
            shape.append((str(q.relative_to(p)),q.stat().st_size))
    return tuple(sorted(shape))

def byte_equal(a,b,stop=None,progress=None):
    if os.path.samefile(a,b): return False
    sa,sb=stat_key(a),stat_key(b)
    if sa[0]!=sb[0]: return False
    done=0;last=0
    with a.open('rb') as fa,b.open('rb') as fb:
        while True:
            check(stop); x,y=fa.read(1024*1024),fb.read(1024*1024)
            if x!=y: return False
            if not x: return sa==stat_key(a) and sb==stat_key(b)
            done+=len(x);now=time.monotonic()
            if progress and (now-last>.12 or done==sa[0]):
                last=now;notify(progress,'Bayt karşılaştırması',done,sa[0],b,'bayt')

def find_duplicates(units,stop=None,progress=lambda s:None):
    issues=[]; shapes={}; sizes=defaultdict(list)
    for index,u in enumerate(units):
        check(stop); p=u['path']
        notify(progress,'Boyut ve klasör yapısı inceleniyor',index,len(units),p)
        if u.get('companions'):
            issues.append((str(p),'Bağlı medya seti kopya silmeden korundu')); continue
        try:
            if u['folder']:
                shape=folder_shape(p,stop); shapes[p]=shape
                u['size']=sum(size for _,size in shape if size>=0)
                key=('folder',shape)
            else: key=('file',p.stat().st_size)
            sizes[key].append(u)
        except (OSError,ValueError) as e: issues.append((str(p),str(e)))
    samples=defaultdict(list)
    candidates=[u for group in sizes.values() if len(group)>1 for u in group]
    for i,u in enumerate(candidates):
        check(stop); p=u['path']
        notify(progress,'Hızlı içerik elemesi',i,len(candidates),p)
        try:
            if u['folder']:
                value=tuple((rel,hash_file(p/rel,stop,True)) for rel,size in shapes[p] if size>=0)
                key=('folder',shapes[p],value)
            else: key=('file',p.stat().st_size,hash_file(p,stop,True))
            samples[key].append(u)
        except (OSError,ValueError) as e: issues.append((str(p),str(e)))
    full=defaultdict(list)
    candidates=[u for group in samples.values() if len(group)>1 for u in group]
    for i,u in enumerate(candidates):
        p=u['path']; notify(progress,'Tam içerik doğrulama',i,len(candidates),p)
        try:
            if u['folder']:
                key=('folder',shapes[p],tuple((rel,hash_file(p/rel,stop,progress=progress)) for rel,size in shapes[p] if size>=0))
            else: key=('file',p.stat().st_size,hash_file(p,stop,progress=progress))
            full[key].append(u)
        except (OSError,ValueError) as e: issues.append((str(p),str(e)))
    groups=[]
    buckets=[bucket for bucket in full.values() if len(bucket)>1]
    for group_index,bucket in enumerate(buckets):
        notify(progress,'Eşleşmeler doğrulanıyor',group_index,len(buckets))
        if len(bucket)<2: continue
        verified=[]
        for u in bucket:
            check(stop)
            try:
                if not verified: verified.append(u); continue
                a,b=verified[0]['path'],u['path']
                equal=all(os.path.samefile(a/rel,b/rel) or byte_equal(a/rel,b/rel,stop,progress) for rel,size in shapes[a] if size>=0) if u['folder'] else byte_equal(a,b,stop,progress)
                if equal and u['folder']:
                    equal=folder_shape(a,stop)==shapes[a] and folder_shape(b,stop)==shapes[b]
                if equal: verified.append(u)
            except (OSError,ValueError) as e: issues.append((str(u['path']),str(e)))
        if len(verified)>1: groups.append([(u['path'],u['folder']) for u in verified])
    notify(progress,'Mükerrer taraması tamamlandı',len(buckets),len(buckets))
    return groups,issues

def existing_parent(p):
    while not p.exists():
        if p==p.parent: raise ValueError('Hedef disk bulunamadı')
        p=p.parent
    return p

def same_volume(src,dst):
    return src.stat().st_dev == existing_parent(dst).stat().st_dev

def build_plan(units,target,progress=lambda s:None):
    target=Path(target).resolve(); plan=[]; reserved=set(); next_suffix={}
    for index,u in enumerate(units):
        notify(progress,'Taşıma planı hazırlanıyor',index,len(units),u['path'])
        p=u['path']; cat=category_path(u['category']) if u['category'] else None; dst=None; state='Yerinde kalacak'; reason=u['reason']
        try:
            if not p.exists(): raise ValueError('Öğe artık bulunamıyor; yeniden tarayın')
            if is_link(p): raise ValueError('Bağlantı taşınmaz')
            if p==target:
                raise ValueError('Hedef klasör kendi içine taşınmaz')
            if cat:
                dst=target/cat/p.name
                if not existing_parent(dst.parent).is_dir():
                    raise ValueError('Hedef klasör yolunda aynı adlı bir dosya var; klasör oluşturulamaz')
                if p.parent.resolve()==(target/cat).resolve():
                    raise ValueError('Zaten doğru sınıf klasöründe; yeniden taşınmaz')
                if dst==p or p in dst.parents: raise ValueError('Öğe kendi içine taşınamaz')
                if not same_volume(p,dst): raise ValueError('Farklı disk: ek alan kullanmamak için taşınmayacak')
                companions=u.get('companions',[])
                if companions:
                    parent=target/cat; original=parent; n=2
                    while parent.is_file() or any((parent/q.name).exists() or str(parent/q.name).casefold() in reserved for q in (p,*companions)):
                        parent=original.with_name(original.name+f' ({n})'); n+=1
                    dst=parent/p.name
                    unit_moves=[(p,dst)]+[(q,parent/q.name) for q in companions]
                else:
                    stem,suffix=p.stem,p.suffix
                    base_key=str(dst).casefold()
                    n=next_suffix.get(base_key,2)
                    while dst.exists() or str(dst).casefold() in reserved:
                        name=f'{p.name} ({n})' if u['folder'] else f'{stem} ({n}){suffix}'
                        dst=target/cat/name; n+=1
                    next_suffix[base_key]=n
                    unit_moves=[(p,dst)]
                for src,dest in unit_moves:
                    if is_link(src) or not same_volume(src,dest): raise ValueError('Eşlikçi dosya bağlantı veya farklı diskte')
                reserved.update(str(dest).casefold() for _,dest in unit_moves)
                state='Hazır'
        except (OSError,ValueError) as e:
            state='Atlandı'; reason=str(e); dst=None
        info={'unit':u,'dest':dst,'state':state,'reason':reason}
        if state=='Hazır':
            info['moves']=unit_moves
            info['snapshots']={str(src):stat_key(src) for src,_ in unit_moves}
        plan.append(info)
    notify(progress,'Taşıma planı hazır',len(units),len(units))
    return plan
