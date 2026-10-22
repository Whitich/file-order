import os
import json
import hashlib
import threading
import queue
import uuid
import ctypes
import time
import traceback
import localization as i18n
from localization import tr
import duzen_engine as engine
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
try:
    from PIL import Image, ImageTk, ImageOps
except ImportError:
    Image = None

def recycle_file(path):
    class Operation(ctypes.Structure):
        _fields_ = [('hwnd', ctypes.c_void_p), ('wFunc', ctypes.c_uint),
                    ('pFrom', ctypes.c_wchar_p), ('pTo', ctypes.c_wchar_p),
                    ('fFlags', ctypes.c_ushort), ('fAnyOperationsAborted', ctypes.c_int),
                    ('hNameMappings', ctypes.c_void_p), ('lpszProgressTitle', ctypes.c_wchar_p)]
    operation = Operation()
    operation.wFunc = 3
    operation.pFrom = str(path.resolve()) + '\0\0'
    # WANTNUKEWARNING prevents silent permanent deletion when recycling is unavailable.
    operation.fFlags = 0x40 | 0x4000
    result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(operation))
    if result or operation.fAnyOperationsAborted:
        raise ValueError('Silme tamamlanmadı veya iptal edildi: ' + str(path))

PROJECT_MARKERS = {'package.json', 'pyproject.toml', 'requirements.txt', 'Cargo.toml', 'go.mod', 'pom.xml', 'build.gradle', 'CMakeLists.txt', '.git', 'Assets', 'project.godot', 'composer.json', 'Gemfile', 'pubspec.yaml', 'Makefile'}
PROTECTED = {'node_modules', '.git', '.venv', 'venv', '__pycache__', 'Windows', 'Program Files', 'Program Files (x86)', 'AppData', '$RECYCLE.BIN', 'System Volume Information'}
CATEGORIES = {'PDF': {'.pdf'}, 'Word': {'.doc', '.docx', '.odt', '.rtf'}, 'Tablolar': {'.xls', '.xlsx', '.csv', '.ods'}, 'Sunumlar': {'.ppt', '.pptx', '.odp'}, 'Resimler': {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tif', '.tiff', '.heic', '.svg'}, 'Videolar': {'.mp4', '.mkv', '.avi', '.mov', '.webm'}, 'Sesler': {'.mp3', '.wav', '.flac', '.ogg', '.m4a'}, 'Arsivler': {'.zip', '.rar', '.7z', '.tar', '.gz'}}

def signature(p):
    s = p.stat()
    return (s.st_size, s.st_mtime_ns)

def digest(p, progress=None):
    if progress: return engine.hash_file(p,progress=progress)
    before = signature(p)
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    if signature(p) != before:
        raise ValueError(f'Tarama sırasında değişti: {p}')
    return h.hexdigest()

def identical(a, b):
    if a.is_symlink() or b.is_symlink() or signature(a)[0] != signature(b)[0]:
        return False
    if os.path.samefile(a, b):
        return False
    sa, sb = signature(a), signature(b)
    with a.open('rb') as fa, b.open('rb') as fb:
        while True:
            x, y = fa.read(1024 * 1024), fb.read(1024 * 1024)
            if x != y:
                return False
            if not x:
                return signature(a) == sa and signature(b) == sb

def linked(p):
    return p.is_symlink() or bool(getattr(p.lstat(), 'st_file_attributes', 0) & 0x400)

def project(p):
    return bool(engine.project_reason(p))

def manifest(p, progress=None):
    result = {}
    def fail(error): raise error
    for root, dirs, files in os.walk(p, onerror=fail):
        for n in dirs + files:
            if linked(Path(root) / n):
                raise ValueError(f'Bağlantı içeren klasör karşılaştırılmadı: {p}')
        for n in dirs:
            result[str((Path(root) / n).relative_to(p)) + '/'] = ''
        for n in files:
            f = Path(root) / n
            result[str(f.relative_to(p))] = (f.stat().st_size, digest(f,progress))
    return result

def same_unit(a, b, folder, progress=None):
    if not folder:
        return engine.byte_equal(a,b,progress=progress) if progress else identical(a, b)
    ma, mb = manifest(a,progress), manifest(b,progress)
    return ma == mb and all(engine.byte_equal(a/r,b/r,progress=progress) or os.path.samefile(a / r, b / r) for r in ma if not r.endswith('/'))

def save_records(path, records):
    temp = path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    temp.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    for attempt in range(30):
        try:
            os.replace(temp, path)
            return
        except PermissionError:
            if attempt==29: raise
            time.sleep(.1)

def restore_journal(path, progress=lambda message:None):
    records = json.loads(path.read_text(encoding='utf-8'))
    active = [r for r in records if r['state'] in ('moved', 'pending')]
    moves = []
    already_restored = []
    for index,r in enumerate(reversed(active)):
        src, dst = Path(r['source']), Path(r['dest'])
        engine.notify(progress,'Geri alma ön kontrolü',index,len(active),src)
        if src.exists() and not dst.exists():
            if linked(src):
                raise ValueError('Eski konum bir bağlantı olmuş; kontrol gerekli: '+str(src))
            expected=r.get('identity')
            if expected and list((src.stat().st_dev,src.stat().st_ino))!=expected:
                raise ValueError('Eski konumda farklı bir öğe var: '+str(src))
            already_restored.append(r)
            continue
        if src.exists():
            raise ValueError('Eski konumda aynı isimli bir öğe var. Üzerine yazılmadı: ' + str(src))
        if not dst.exists():
            raise ValueError('Taşınan öğe bulunamadı. Sonraki işlemleri önce geri alın: ' + str(dst))
        if linked(dst):
            raise ValueError('Öğe bir bağlantıyla değiştirilmiş: ' + str(dst))
        moves.append((r, src, dst))
    for r in already_restored:
        r['state']='undone'
        r['undone_at']=datetime.now().astimezone().isoformat(timespec='seconds')
        r['undo_note']='Eski konum mevcut ve taşıma hedefi yok; yeniden taşınmadı.'
    if already_restored: save_records(path,records)
    last_save=time.monotonic()
    try:
        for i,(r, src, dst) in enumerate(moves,1):
            src.parent.mkdir(parents=True, exist_ok=True)
            if src.exists(): raise ValueError('Eski konuma yeni bir dosya geldi; üzerine yazılmadı: '+str(src))
            os.rename(dst, src)
            r['state'] = 'undone'
            r['undone_at'] = datetime.now().astimezone().isoformat(timespec='seconds')
            engine.notify(progress,'Dosyalar eski konumuna taşınıyor',i,len(moves),src)
            if i%100==0 or time.monotonic()-last_save>1:
                save_records(path,records);last_save=time.monotonic()
    finally:
        save_records(path, records)
    return len(moves)

class LocalizedTreeview(ttk.Treeview):
    def insert(self,parent,index,iid=None,**kwargs):
        if 'values' in kwargs:kwargs['values']=tuple(tr(value) for value in kwargs['values'])
        if 'text' in kwargs:kwargs['text']=tr(kwargs['text'])
        return super().insert(parent,index,iid=iid,**kwargs)

class App:
    def __init__(self, root):
        i18n.load_language()
        self.root = root
        root.title('File Order • '+tr('Güvenli tarama ve düzenleme'))
        root.geometry(f'{min(1280,root.winfo_screenwidth()-40)}x{min(860,root.winfo_screenheight()-100)}')
        root.minsize(1050, 700)
        self.apply_theme()
        self.events = queue.Queue()
        self.stop = threading.Event()
        self.units, self.groups, self.rows, self.plan = [], [], {}, []
        self.busy = False
        self.inventory = []
        self.issues = []
        self.plan_info = {}
        self.organizer_only = tk.BooleanVar(value=True)
        self.last_progress = 0
        self.last_progress_phase=''
        self.operation_started=None
        self.operation_failed=False
        self.operation_name=''
        self.progress_state={}
        self.base = tk.StringVar()
        self.target = tk.StringVar()
        self.status = tk.StringVar(value=tr('Bir klasör seçerek başlayın. Hiçbir dosya otomatik silinmez.'))
        self.settings_path=Path(os.environ.get('LOCALAPPDATA',str(Path.home()))) / 'DosyaDuzeni' / 'settings.json'
        try:
            read_path=self.settings_path if self.settings_path.exists() else self.settings_path.with_name('ayarlar.json')
            settings=json.loads(read_path.read_text(encoding='utf-8'))
            self.manual={Path(p) for p in settings.get('protected',[])}
            self.target.set(tr(settings.get('target','')))
        except (OSError,ValueError,TypeError): self.manual=set()
        top = ttk.Frame(root, padding=14)
        top.pack(fill='x')
        language_row=ttk.Frame(top);language_row.pack(fill='x')
        self.language_value=tk.StringVar(value=tr('English' if i18n.LANGUAGE=='en' else 'Türkçe'))
        self.language_combo=ttk.Combobox(language_row,textvariable=self.language_value,values=('English','Türkçe'),state='readonly',style='Language.TCombobox',exportselection=False,width=12)
        self.language_combo.pack(side='right')
        self.language_combo.bind('<<ComboboxSelected>>',self.change_language)
        ttk.Label(language_row,text=tr('Dil')).pack(side='right',padx=8)
        ttk.Label(top, text='FILE ORDER  /  4.1', style='Title.TLabel').pack(anchor='w')
        ttk.Label(top, text=tr('Önce incele. Güvenle düzenle. İstediğinde geri al.'), style='Muted.TLabel').pack(anchor='w', pady=(0,12))
        self.summary = tk.StringVar(value=tr('Kopyasız taşıma  •  Projeler bütün kalır  •  Tarihli işlem geçmişi'))
        ttk.Label(top, textvariable=self.summary, style='Card.TLabel', padding=12).pack(fill='x', pady=(0,10))
        bar = ttk.Frame(top); bar.pack(fill='x')
        ttk.Entry(bar, textvariable=self.base).pack(side='left', fill='x', expand=True)
        ttk.Button(bar, text=tr('Klasör seç'), command=self.choose).pack(side='left', padx=5)
        ttk.Button(bar, text=tr('Bölünmeyecek klasör ekle'), command=self.protect).pack(side='left')
        bar2 = ttk.Frame(top); bar2.pack(fill='x', pady=8)
        self.analysis_button=ttk.Button(bar2, text=tr('Klasörü analiz et'), style='Accent.TButton', command=self.scan)
        self.analysis_button.pack(side='left')
        ttk.Checkbutton(bar2, text=tr('Hızlı düzenleme (içerik karşılaştırması yapma)'), variable=self.organizer_only).pack(side='left', padx=12)
        ttk.Button(bar2, text=tr('Taramayı durdur'), command=self.stop.set).pack(side='left', padx=5)
        ttk.Button(bar2, text=tr('Son işlemi geri al'), command=self.undo).pack(side='right')
        self.tabs = ttk.Notebook(root); self.tabs.pack(fill='both', expand=True, padx=14)
        dup = ttk.Frame(self.tabs, padding=10); org = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(dup, text=tr('Aynı dosyalar ve projeler')); self.tabs.add(org, text=tr('Düzenleme önizlemesi'))
        dup_scan=ttk.Frame(dup);dup_scan.pack(fill='x',pady=6)
        self.duplicate_button=ttk.Button(dup_scan,text=tr('SEÇİLİ KLASÖRDE MÜKERRERLERİ BUL'),style='Accent.TButton',command=self.scan_duplicates)
        self.duplicate_button.pack(side='left')
        self.target_duplicate_button=ttk.Button(dup_scan,text=tr('Düzenlenmiş hedefte mükerrerleri bul'),command=self.scan_target_duplicates)
        self.target_duplicate_button.pack(side='left',padx=6)
        ttk.Label(dup, text=tr('Dosyalar içerikleriyle; projeler, dünyalar ve paketler bütün olarak kıyaslanır. Ortak CSS / asset tek başına silinmez.')).pack(anchor='w')
        self.duplicate_summary=tk.StringVar(value=tr('Tarama bitince fazlalıkları tek düğmeyle seçebilirsiniz. Silme otomatik yapılmaz.'))
        ttk.Label(dup,textvariable=self.duplicate_summary,style='Card.TLabel',padding=8).pack(fill='x')
        selection_bar = ttk.Frame(dup); selection_bar.pack(fill='x', pady=6)
        ttk.Button(selection_bar, text=tr('Her grupta bir kopya tut, diğerlerini seç'), command=self.select_extras).pack(side='left')
        ttk.Button(selection_bar, text=tr('Bunu tut, grubun diğerlerini seç'), command=self.keep_selected).pack(side='left', padx=6)
        ttk.Button(selection_bar, text=tr('Seçimleri temizle'), command=lambda: self.tree.selection_remove(*self.tree.selection())).pack(side='left')
        self.tree = self.table(dup, ('type','size','path'), ('Tür','Boyut','Tam yol'))
        self.tree.bind('<<TreeviewSelect>>', self.show_preview)
        preview_frame = ttk.Frame(dup); preview_frame.pack(fill='x')
        self.image_preview = ttk.Label(preview_frame, text=tr('Resmi görmek için bir satıra tıklayın.'), width=32)
        self.image_preview.pack(side='left')
        self.preview_text = ttk.Label(preview_frame, text=tr(''), wraplength=650)
        self.preview_text.pack(side='left', padx=12)
        actions = ttk.Frame(dup); actions.pack(fill='x', pady=8)
        ttk.Button(actions, text=tr('Seçilenleri karantinaya taşı (geri alınabilir)'), command=self.quarantine).pack(side='left')
        ttk.Button(actions, text=tr('SİL — Geri Dönüşüm Kutusu’na gönder'), command=self.delete_selected).pack(side='right')
        actions.pack_configure(side='bottom',before=self.tree.master)
        preview_frame.pack_configure(side='bottom',before=self.tree.master)
        ttk.Label(org, text=tr('01  Hedefi seç     →     02  Planı incele     →     03  Hazır öğeleri uygula'), style='Section.TLabel').pack(anchor='w', pady=8)
        ttk.Label(org, text=tr('Bağımsız belgeler sınıflanır. Oyun dünyaları, uygulama verileri, projeler ve belirsiz paketler bütün kalır.'), style='Muted.TLabel').pack(anchor='w')
        row = ttk.Frame(org); row.pack(fill='x', pady=8)
        ttk.Entry(row, textvariable=self.target).pack(side='left', fill='x', expand=True)
        ttk.Button(row, text=tr('Hedef seç'), command=lambda: self.target.set(tr(filedialog.askdirectory() or self.target.get()))).pack(side='left')
        ttk.Button(row, text=tr('Plan oluştur'), command=self.preview).pack(side='left', padx=5)
        ttk.Button(row, text=tr('Hedefteki paketleri yeniden incele'),command=self.inspect_packages).pack(side='left')
        self.plan_summary = tk.StringVar(value=tr('Önce “Klasörü analiz et” düğmesini kullanın. Hızlı mod dosya içeriğini okumaz.'))
        ttk.Label(org, textvariable=self.plan_summary, style='Card.TLabel', padding=10).pack(fill='x', pady=4)
        self.category_summary=tk.StringVar(value=tr('TXT, PDF, Word, fotoğraf, video, ses, tasarım, kurulum ve diğer dosyalar dahil.'))
        ttk.Label(org,textvariable=self.category_summary,wraplength=1120,style='Muted.TLabel').pack(fill='x',pady=4)
        self.ptree = self.table(org, ('state','category','source','dest','reason'), ('Durum','Sınıf','Kaynak','Hedef','Neden / koruma'))
        self.ptree.bind('<<TreeviewSelect>>', self.plan_details)
        self.plan_detail = tk.StringVar()
        ttk.Label(org, textvariable=self.plan_detail, wraplength=1050, style='Muted.TLabel').pack(fill='x')
        org_buttons = ttk.Frame(org); org_buttons.pack(fill='x', pady=8)
        ttk.Button(org_buttons, text=tr('Hazır öğelerin tümünü seç'), command=self.select_ready).pack(side='left')
        ttk.Button(org_buttons, text=tr('Seçimi temizle'), command=lambda:self.ptree.selection_remove(*self.ptree.selection())).pack(side='left',padx=6)
        ttk.Button(org_buttons, text=tr('TÜM HAZIR ÖĞELERİ DÜZENLE'), style='Accent.TButton', command=lambda:self.organize(all_ready=True)).pack(side='right')
        ttk.Button(org_buttons, text=tr('Yalnız seçilenleri uygula'), command=self.organize).pack(side='right',padx=6)
        org_buttons.pack_configure(side='bottom',before=self.ptree.master)
        history = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(history, text=tr('İşlem geçmişi'))
        ttk.Label(history, text=tr('Tarihli bir işlemi seçin; dosyaların eski ve yeni konumlarını inceleyip geri alın. Geçmiş uygulama kapatılsa da saklanır.')).pack(anchor='w')
        self.htree = self.table(history, ('date','action','count','state'), ('Tarih / saat','İşlem','Öğe sayısı','Durum'))
        self.htree.configure(selectmode='browse')
        self.htree.bind('<<TreeviewSelect>>', self.history_details)
        self.details = tk.Text(history, height=7, wrap='word', state='disabled')
        self.details.pack(fill='x')
        buttons = ttk.Frame(history); buttons.pack(fill='x', pady=8)
        ttk.Button(buttons, text=tr('Geçmişi yenile'), command=self.refresh_history).pack(side='left')
        ttk.Button(buttons, text=tr('Seçilen işlemi geri al'), command=self.undo_selected).pack(side='right')
        self.refresh_history()
        problems = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(problems, text=tr('Korunanlar ve uyarılar'))
        ttk.Label(problems, text=tr('Anlaşılamayan veya erişilemeyen öğeler taramayı durdurmaz. Nedenleri burada görünür.')).pack(anchor='w')
        self.issue_tree = self.table(problems, ('path','reason'), ('Öğe','Açıklama'))
        progress_card=ttk.Frame(root,padding=(14,8))
        progress_card.pack(fill='x',before=self.tabs)
        self.progress_card=progress_card
        self.operation_label=tk.StringVar(value=tr('HAZIR — İşlem çalışmıyor'))
        self.operation_path=tk.StringVar(value=tr('Bir işlem başlattığınızda aşaması ve ilerlemesi burada görünür.'))
        self.operation_metrics=tk.StringVar(value=tr(''))
        progress_head=ttk.Frame(progress_card);progress_head.pack(fill='x')
        ttk.Label(progress_head,textvariable=self.operation_label,style='Section.TLabel').pack(side='left')
        ttk.Label(progress_head,textvariable=self.operation_metrics,style='Muted.TLabel').pack(side='right')
        self.progress_bar = ttk.Progressbar(progress_card, mode='determinate',maximum=100)
        self.progress_bar.pack(fill='x',pady=6)
        ttk.Label(progress_card,textvariable=self.operation_path,style='Muted.TLabel',wraplength=1120).pack(anchor='w')
        ttk.Label(progress_card, textvariable=self.status, wraplength=1120).pack(fill='x',pady=(4,0))
        root.report_callback_exception=self.callback_error
        self.tabs.select(org)
        self.poll_id=root.after(150, self.poll)
        root.file_order_app=self

    def change_language(self,event=None):
        chosen='tr' if self.language_value.get()=='Türkçe' else 'en'
        if self.busy:
            self.language_value.set(tr('English' if i18n.LANGUAGE=='en' else 'Türkçe'))
            messagebox.showinfo(tr('Bekleyin'),tr('Önce devam eden işlemin tamamlanmasını bekleyin.'));return
        source=self.base.get();target=self.target.get();tab=self.tabs.index(self.tabs.select())
        i18n.set_language(chosen);self.save_settings()
        self.root.after_cancel(self.poll_id)
        for child in self.root.winfo_children():child.destroy()
        app=App(self.root);app.base.set(tr(source));app.target.set(tr(target));app.tabs.select(tab)
        app.status.set(tr('Dil değişti. Yeni dosya yolları için yeniden analiz edin.'))

    def apply_theme(self):
        style = ttk.Style(self.root); style.theme_use('clam')
        bg, card, text, muted, accent = '#111827', '#1f2937', '#e5e7eb', '#a8b4c5', '#2563eb'
        self.root.configure(bg=bg)
        style.configure('.', background=bg, foreground=text, font=('Segoe UI',10))
        style.configure('TFrame',background=bg)
        style.configure('TLabel',background=bg,foreground=text)
        style.configure('Title.TLabel',font=('Segoe UI',23,'bold'))
        style.configure('Section.TLabel',font=('Segoe UI',12,'bold'))
        style.configure('Muted.TLabel',foreground=muted)
        style.configure('Card.TLabel',background=card,foreground='#93c5fd')
        style.configure('TButton',background=card,foreground=text,padding=(12,8),borderwidth=0)
        style.map('TButton',background=[('active','#374151')])
        style.configure('Accent.TButton',background=accent,foreground='white')
        style.map('Accent.TButton',background=[('active','#1d4ed8')])
        style.configure('TEntry',fieldbackground=card,foreground=text,insertcolor=text,padding=7)
        style.configure('Language.TCombobox',fieldbackground=card,background=card,foreground=text,
                        arrowcolor=text,selectbackground=accent,selectforeground='white',padding=6)
        style.map('Language.TCombobox',
                  fieldbackground=[('disabled',card),('readonly',card)],
                  foreground=[('disabled',muted),('readonly',text)],
                  background=[('active','#374151'),('readonly',card)],
                  selectbackground=[('readonly',accent)],
                  selectforeground=[('readonly','white')])
        self.root.option_add('*TCombobox*Listbox.background',card)
        self.root.option_add('*TCombobox*Listbox.foreground',text)
        self.root.option_add('*TCombobox*Listbox.selectBackground',accent)
        self.root.option_add('*TCombobox*Listbox.selectForeground','white')
        style.configure('Treeview',background=card,fieldbackground=card,foreground=text,rowheight=32,borderwidth=0)
        style.configure('Treeview.Heading',background='#273449',foreground=text,padding=8)
        style.map('Treeview',background=[('selected','#1d4ed8')],foreground=[('selected','white')])
        style.configure('TNotebook',background=bg,borderwidth=0)
        style.configure('TNotebook.Tab',background=card,padding=(16,10))
        style.map('TNotebook.Tab',background=[('selected',accent)],foreground=[('selected','white')])
        style.configure('TCheckbutton',background=bg,foreground=text)

    def table(self, parent, cols, headings):
        frame = ttk.Frame(parent); frame.pack(fill='both', expand=True, pady=8)
        t = LocalizedTreeview(frame, columns=cols, show='tree headings', selectmode='extended', height=7)
        t.heading('#0', text=tr('Grup')); t.column('#0', width=115)
        for c,h in zip(cols,headings):
            t.heading(c,text=tr(h)); t.column(c,width=350 if c in ('path','source','dest') else 95)
        scroll = ttk.Scrollbar(frame, command=t.yview); t.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y'); t.pack(fill='both',expand=True)
        if 'state' in cols:
            t.column('#0',width=0,stretch=False)
            for c in cols: t.column(c,width=105 if c in ('state','category') else 260,minwidth=80)
        horizontal = ttk.Scrollbar(frame, orient='horizontal', command=t.xview)
        t.configure(xscrollcommand=horizontal.set); horizontal.pack(side='bottom',fill='x',before=t)
        return t

    def callback_error(self,kind,value,tb):
        log=self.settings_path.parent/i18n.generated_name('errors')
        log.parent.mkdir(parents=True,exist_ok=True)
        with log.open('a',encoding='utf-8') as out:
            out.write(datetime.now().isoformat()+'\n'+''.join(traceback.format_exception(kind,value,tb))+'\n')
        self.status.set(tr('Arayüz hatası: '+str(value)))
        messagebox.showerror(tr('Arayüz hatası'),tr(str(value)+'\nAyrıntı kaydedildi: '+str(log)))

    def set_scan_buttons(self,busy):
        for button in (self.analysis_button,self.duplicate_button,self.target_duplicate_button):
            button.state(['disabled'] if busy else ['!disabled'])
        self.duplicate_button.configure(text=tr('TARAMA / İŞLEM SÜRÜYOR…' if busy else 'SEÇİLİ KLASÖRDE MÜKERRERLERİ BUL'))

    def choose(self):
        p = filedialog.askdirectory()
        if p:
            self.base.set(tr(p))
            if not self.target.get(): self.target.set(tr(str(Path(p).parent / (Path(p).name + i18n.generated_name('organized')))))

    def save_settings(self):
        self.settings_path.parent.mkdir(parents=True,exist_ok=True)
        save_records(self.settings_path,{'protected':[str(p) for p in self.manual],'target':self.target.get(),'language':i18n.LANGUAGE})

    def inspect_packages(self):
        if self.busy: return
        if not self.target.get(): return
        package_root=Path(self.target.get())/i18n.category_path('Butun_Paketler')
        if not package_root.is_dir():
            package_root=Path(self.target.get())/('Butun_Paketler' if i18n.LANGUAGE=='en' else 'Intact_Packages')
        if not package_root.is_dir():
            messagebox.showinfo(tr('Paketler'),tr('Bu hedefte Butun_Paketler klasörü bulunamadı.')); return
        self.base.set(tr(str(package_root)))
        self.scan()

    def select_extras(self):
        if self.busy: return
        keep = set()
        extras = []
        for row, (group, path, folder) in self.rows.items():
            if group in keep: extras.append(row)
            else: keep.add(group)
        self.tree.selection_set(extras)
        self.status.set(tr(f'{len(keep)} grupta birer kopya korunacak; {len(extras)} fazla kopya seçildi. Henüz silinmedi.'))

    def keep_selected(self):
        if self.busy: return
        row = self.tree.focus()
        if row not in self.rows: return
        group, path, folder = self.rows[row]
        selected = [r for r in self.tree.selection() if r in self.rows and self.rows[r][0] != group]
        selected += [r for r, entry in self.rows.items() if entry[0] == group and r != row]
        self.tree.selection_set(selected)
        self.status.set(tr('Bu grupta korunacak kopya: ' + str(path)))

    def show_preview(self, event=None):
        row = self.tree.focus()
        if row not in self.rows:
            chosen = self.tree.selection()
            row = chosen[0] if chosen else None
        if row not in self.rows: return
        group, path, folder = self.rows[row]
        self.preview_text.configure(text=tr(f'Grup {group+1} • {path}\n' + ('Bütün klasör' if folder else 'Dosya') + '\nVurgulanan satırlar kaldırılacak kopyalardır.'))
        self.image_preview.configure(image='', text=tr('Resim önizlemesi yok'))
        self.preview_image = None
        if not folder and Image and path.suffix.lower() in CATEGORIES['Resimler']:
            try:
                with Image.open(path) as img:
                    img.thumbnail((240,140))
                    self.preview_image = ImageTk.PhotoImage(ImageOps.exif_transpose(img).copy())
                self.image_preview.configure(image=self.preview_image, text=tr(''))
            except Exception:
                self.image_preview.configure(text=tr('Bu resim biçimi önizlenemedi.'))

    def delete_selected(self):
        if self.busy: return
        selected = [self.rows[r] for r in self.tree.selection() if r in self.rows]
        if not selected: return
        chosen = {p for _,p,_ in selected}
        checks = []
        for group, path, folder in selected:
            keep = next((p for p,_ in self.groups[group] if p not in chosen), None)
            if keep is None:
                messagebox.showerror(tr('Bir kopya korunmalı'), tr('Her grupta en az bir kopya bırakın.')); return
            checks.append((path, keep, folder))
        if not messagebox.askyesno(tr('Seçilen kopyaları sil'), tr(f'{len(checks)} fazla kopya Windows Geri Dönüşüm Kutusu’na gönderilecek. Her grupta bir kopya kalacak.\n\nBunları geri almak için Windows Geri Dönüşüm Kutusu’nu kullanın. Devam edilsin mi?')): return
        def work():
            for i,(path, keep, folder) in enumerate(checks):
                engine.notify(self.report_progress,'Silme öncesi içerik doğrulaması',i,len(checks),path)
                engine.assert_removable_unit(path,folder,self.scanbase,self.manual)
                if not same_unit(path,keep,folder,self.report_progress): raise ValueError('Dosyalar değişmiş; silme durduruldu: '+str(path))
            directory = Path(os.environ.get('LOCALAPPDATA',str(Path.home()))) / 'DosyaDuzeni'
            directory.mkdir(parents=True,exist_ok=True)
            journal = directory / (i18n.generated_name('journal')+datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8]+'.json')
            records = []
            for i,(path,keep,folder) in enumerate(checks):
                engine.notify(self.report_progress,'Geri Dönüşüm Kutusu’na gönderiliyor',i,len(checks),path)
                engine.assert_removable_unit(path,folder,self.scanbase,self.manual)
                if not same_unit(path,keep,folder,self.report_progress): raise ValueError('İçerik değişti: '+str(path))
                recycle_file(path)
                records.append({'source':str(path), 'dest':tr('Windows Geri Dönüşüm Kutusu'), 'state':'recycled', 'action':tr('Geri Dönüşüm Kutusu’na silme'), 'created_at':datetime.now().astimezone().isoformat(timespec='seconds'),'language':i18n.LANGUAGE})
                save_records(journal,records)
                engine.notify(self.report_progress,'Geri Dönüşüm Kutusu’na gönderiliyor',i+1,len(checks),path)
            self.events.put(('changed', f'{len(records)} kopya Geri Dönüşüm Kutusu’na gönderildi. Yeniden analiz edin.'))
        self.launch(work,label='Mükerrerleri silme')

    def protect(self):
        p = filedialog.askdirectory(title=tr('Bütün tutulacak klasör'))
        if p:
            self.manual.add(Path(p).resolve())
            self.save_settings()
            self.status.set(tr('Korunan klasör kaydedildi. Yeniden tarayın: ' + p))

    def launch(self, fn, label='İşlem'):
        if self.busy:
            messagebox.showinfo(tr('Bekleyin'),tr('Önce devam eden işlemin tamamlanmasını bekleyin.')); return
        self.busy = True; self.stop.clear()
        self.set_scan_buttons(True)
        self.status.set(tr(label+' başladı. İlerleme üst panelde gösteriliyor.'))
        if 'Mükerrer' in label:self.duplicate_summary.set(tr('Tarama başladı. Sonuçlar tamamlandığında burada listelenecek; henüz silme yapılmıyor.'))
        self.operation_started=time.monotonic();self.operation_failed=False
        self.operation_name=tr(label);self.last_progress=0;self.last_progress_phase=''
        self.render_progress({'phase':'Başlatılıyor','done':0,'total':None,'path':'','unit':'öğe'})
        def run():
            try: fn()
            except engine.Cancelled as e: self.events.put(('cancelled',str(e)))
            except Exception as e: self.events.put(('error', str(e)))
            finally: self.events.put(('done', None))
        threading.Thread(target=run, daemon=True).start()

    def scan_duplicates(self):
        self.tabs.select(0)
        self.scan(duplicate=True)

    def scan_target_duplicates(self):
        if self.busy: return
        if not self.target.get() or not Path(self.target.get()).is_dir():
            messagebox.showinfo(tr('Mükerrer tarama'),tr('Önce mevcut düzenleme hedefini seçin.')); return
        self.base.set(tr(self.target.get()))
        self.scan_duplicates()

    def scan(self, duplicate=False):
        if self.busy:
            self.status.set(tr('Devam eden işlem: '+self.operation_name+'. İlerleme üst panelde.'));return
        base = Path(self.base.get())
        if not self.base.get() or not base.is_dir():
            messagebox.showinfo(tr('Klasör gerekli'),tr('Önce “Klasör seç” ile var olan bir klasör seçin.'));return
        self.scanbase = base.resolve()
        self.save_settings()
        fast = False if duplicate else self.organizer_only.get()
        manual = set(tr(self.manual))
        target=Path(self.target.get()).resolve() if self.target.get() else None
        exclude=[target] if target and target!=self.scanbase else []
        def work():
            started = time.monotonic()
            self.events.put(('status','Klasörler inceleniyor; dosya kopyalanmıyor…'))
            units, errors = engine.inventory(self.scanbase,manual,self.stop,self.report_progress,exclude=exclude,purpose='duplicates' if not fast else 'organize')
            groups = []
            if not fast:
                groups, more = engine.find_duplicates(units,self.stop,self.report_progress)
                errors.extend(more)
            self.events.put(('scan',(units,groups,errors,time.monotonic()-started,fast)))
            if fast and target and target!=self.scanbase:
                self.events.put(('plan',engine.build_plan(units,target,self.report_progress)))
        self.launch(work,label='Klasör analizi' if fast else 'Mükerrer taraması')

    def report_progress(self, text):
        data=text if isinstance(text,dict) else {'phase':text,'done':0,'total':None,'path':'','unit':'öğe'}
        now = time.monotonic()
        if data['phase']!=self.last_progress_phase or now-self.last_progress>.12 or data.get('total')==data.get('done'):
            self.last_progress=now;self.last_progress_phase=data['phase'];self.events.put(('progress',data))

    def render_progress(self,data):
        self.progress_state=data
        total=data.get('total');done=data.get('done',0)
        self.operation_label.set(tr(f'{self.operation_name.upper()}  •  {data["phase"]}'))
        self.operation_path.set(tr(data.get('path') or 'İşlem sürüyor…'))
        if total is None:
            if self.progress_bar.cget('mode')!='indeterminate':
                self.progress_bar.stop();self.progress_bar.configure(mode='indeterminate');self.progress_bar.start(12)
        else:
            self.progress_bar.stop();self.progress_bar.configure(mode='determinate',value=min(100,100*done/total) if total else 100)
        self.update_progress_metrics()

    def update_progress_metrics(self):
        data=self.progress_state
        if not data or self.operation_started is None:return
        elapsed=int(time.monotonic()-self.operation_started)
        done=data.get('done',0);total=data.get('total')
        if total is None: text=f'{done:,} öğe • toplam belirleniyor'
        elif data.get('unit')=='bayt': text=f'{engine.readable_size(done)} / {engine.readable_size(total)} • %{100*done/total:.0f}' if total else '0 B'
        else: text=f'{done:,} / {total:,} öğe • %{100*done/total:.0f}' if total else '0 öğe'
        self.operation_metrics.set(tr(f'{text}  •  {elapsed//60:02d}:{elapsed%60:02d}'))

    def clear_results(self):
        self.units=[]; self.inventory=[]; self.groups=[]; self.rows={}; self.plan=[]; self.plan_info={}
        self.tree.delete(*self.tree.get_children()); self.ptree.delete(*self.ptree.get_children())

    def render_issues(self):
        self.issue_tree.delete(*self.issue_tree.get_children())
        for path,reason in self.issues:
            self.issue_tree.insert('','end',values=(path,reason))

    def poll(self):
        try:
            for _ in range(200):
                kind,data = self.events.get_nowait()
                if kind == 'done':
                    self.busy=False;self.progress_bar.stop();self.update_progress_metrics()
                    self.set_scan_buttons(False)
                    self.progress_bar.configure(mode='determinate')
                    if not self.operation_failed:
                        self.progress_bar.configure(value=100)
                        self.operation_label.set(tr(f'TAMAMLANDI  •  {self.operation_name}'))
                    else:
                        self.progress_bar.configure(value=0)
                        self.operation_metrics.set(tr('İşlem tamamlanmadı'))
                    self.operation_path.set(tr(self.status.get()))
                    self.refresh_history()
                elif kind=='progress': self.render_progress(data)
                elif kind=='cancelled':
                    self.operation_failed=True
                    self.operation_label.set(tr(f'DURDURULDU  •  {self.operation_name}'))
                    self.status.set(tr(data))
                elif kind == 'error':
                    self.operation_failed=True
                    self.operation_label.set(tr(f'DURDU / HATA  •  {self.operation_name}'))
                    self.clear_results()
                    self.status.set(tr(data))
                    self.plan_summary.set(tr('İşlem durdu. Tamamlanan taşımalar geçmişte saklanır. Devam etmeden yeniden analiz edin.'))
                    messagebox.showerror(tr('İşlem tamamlanamadı'),tr(data))
                elif kind == 'status': self.status.set(tr(data))
                elif kind == 'plan':
                    self.display_plan(data)
                elif kind == 'changed':
                    self.clear_results()
                    self.status.set(tr(data))
                    self.plan_summary.set(tr('Dosya konumları değişti. Yeni bir analiz başlatın.'))
                elif kind == 'scan':
                    self.clear_results()
                    self.inventory,self.groups,self.issues,elapsed,fast=data
                    self.units=[(u['path'],u['folder']) for u in self.inventory]
                    sizes={u['path']:u.get('size') or 0 for u in self.inventory}
                    for i,g in enumerate(self.groups):
                        for p,f in g:
                            try: size=engine.readable_size(sizes[p]) if f else engine.readable_size(p.stat().st_size)
                            except OSError: size='Erişilemedi'
                            row=self.tree.insert('', 'end', text=tr(f'Grup {i+1}'),values=('Bütün klasör' if f else 'Dosya', size,str(p)))
                            self.rows[row]=(i,p,f)
                    protected=sum(u['folder'] for u in self.inventory)
                    self.summary.set(tr(f'{len(self.units):,} öğe  •  {protected} bütün korunan klasör  •  {len(self.groups)} kopya grubu  •  {elapsed:.1f} saniye'))
                    extras=sum(len(g)-1 for g in self.groups)
                    extra_bytes=sum(sum(sizes[p] for p,f in g[1:]) for g in self.groups)
                    self.duplicate_summary.set(tr(f'{len(self.groups)} mükerrer grup • {extras} fazla kopya • {engine.readable_size(extra_bytes)} toplam fazla içerik. Paketlerin içinden tek dosya listelenmez.'))
                    self.render_issues()
                    self.plan_summary.set(tr('Analiz hazır. Hedefi seçip “Plan oluştur” düğmesine basın.'))
                    self.status.set(tr(f'Analiz tamamlandı. {len(self.issues)} uyarı.' + (' Kopya bulmak için hızlı düzenleme işaretini kaldırıp analiz edin.' if fast else ' Aynı içerikler tam doğrulamayla karşılaştırıldı.')))
        except queue.Empty: pass
        except Exception:
            import sys
            self.callback_error(*sys.exc_info())
        if self.busy:self.update_progress_metrics()
        self.poll_id=self.root.after(150,self.poll)

    def transact(self, moves, action='Düzenleme'):
        # Validate every move before any mutation. Never fall back to copy/delete.
        destinations=set()
        for index,(src,dst) in enumerate(moves):
            engine.notify(self.report_progress,'Taşıma ön kontrolü',index,len(moves),src)
            if not src.exists() or linked(src): raise ValueError('Kaynak yok veya bağlantı: '+str(src))
            if dst.exists() or str(dst).casefold() in destinations: raise ValueError('Hedef çakışması: '+str(dst))
            destinations.add(str(dst).casefold())
            if src.is_dir() and (dst==src or src in dst.parents): raise ValueError('Klasör kendi içine taşınamaz')
            if not engine.same_volume(src,dst): raise ValueError('Farklı diske taşıma kapalı. Hedefi kaynakla aynı diskten seçin.')
        journal_dir = Path(os.environ.get('LOCALAPPDATA',str(Path.home()))) / 'DosyaDuzeni'
        journal_dir.mkdir(parents=True,exist_ok=True)
        journal = journal_dir / (i18n.generated_name('journal')+datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8]+'.json')
        records=[]
        def save():
            save_records(journal, records)
        for index,(src,dst) in enumerate(moves):
            engine.notify(self.report_progress,'Karantinaya taşınıyor' if action=='Karantina' else 'Dosyalar taşınıyor',index,len(moves),src)
            if dst.exists(): raise ValueError('Hedef zaten var: '+str(dst))
            if linked(src): raise ValueError('Bağlantı taşınamaz: '+str(src))
            if src.is_dir() and (dst == src or src in dst.parents): raise ValueError('Klasör kendi içine taşınamaz.')
            dst.parent.mkdir(parents=True,exist_ok=True)
            stat=src.stat()
            records.append({'source':str(src),'dest':str(dst),'state':'pending', 'action':tr(action), 'created_at':datetime.now().astimezone().isoformat(timespec='seconds'),'identity':[stat.st_dev,stat.st_ino],'language':i18n.LANGUAGE}); save()
            # rename is atomic on one volume; cross-volume operations are deliberately refused.
            try:
                if self.stop.is_set(): raise ValueError('Düzenleme durduruldu')
                os.rename(src,dst)
            except Exception as error:
                records[-1]['state']='failed'
                records[-1]['error']=str(error)
                save()
                try:
                    restored=restore_journal(journal,self.report_progress)
                except (OSError,ValueError) as rollback_error:
                    raise ValueError(f'Taşıma durdu: {error}. Bazı adımlar geri alınamadı: {rollback_error}. İşlem geçmişini kullanın.') from error
                raise ValueError(f'Taşıma tamamlanamadı: {error}. Önceki {restored} adım geri alındı. Ayrıntılar işlem geçmişinde.') from error
            records[-1]['state']='moved'; save()
            engine.notify(self.report_progress,'Karantinaya taşınıyor' if action=='Karantina' else 'Dosyalar taşınıyor',index+1,len(moves),dst)
        return journal

    def quarantine(self):
        if self.busy: return
        selected=[self.rows[r] for r in self.tree.selection() if r in self.rows]
        if not selected: return
        chosen={p for _,p,_ in selected}
        checks=[]
        for i,p,f in selected:
            keep=next((x for x,_ in self.groups[i] if x not in chosen),None)
            if keep is None: messagebox.showerror(tr('Bir kopya korunmalı'),tr('Her grupta en az bir öğeyi seçmeden bırakın.')); return
            checks.append((p,keep,f))
        if not messagebox.askyesno(tr('Karantinaya taşı'),tr(f'{len(checks)} öğe karantinaya taşınacak. Kalıcı silme yapılmaz. Devam edilsin mi?')): return
        def work():
            for index,(p,keep,f) in enumerate(checks):
                engine.notify(self.report_progress,'Karantina öncesi içerik doğrulaması',index,len(checks),p)
                engine.assert_removable_unit(p,f,self.scanbase,self.manual)
                if not same_unit(p,keep,f,self.report_progress): raise ValueError('İçerik değişmiş veya eşit değil: '+str(p))
            q=self.scanbase / i18n.generated_name('quarantine') / uuid.uuid4().hex
            j=self.transact([(p,q / str(i) / p.name) for i,(p,_,_) in enumerate(checks)], 'Karantina')
            self.events.put(('changed','Karantinaya taşındı. İşlem geçmişinden geri alabilirsiniz. Yeniden analiz edin.'))
        self.launch(work,label='Karantinaya taşıma')

    def preview(self):
        if self.busy: return
        if not self.inventory or not self.target.get():
            self.status.set(tr('Önce bir klasörü analiz edin ve hedef seçin.')); return
        target=Path(self.target.get()).resolve()
        self.save_settings()
        if target==self.scanbase:
            messagebox.showerror(tr('Hedef'),tr('Kaynak klasörden farklı bir hedef seçin. Kaynak içinde “Duzenli” gibi bir alt klasör de olabilir.')); return
        inventory=list(self.inventory)
        self.launch(lambda:self.events.put(('plan',engine.build_plan(inventory,target,self.report_progress))),label='Taşıma planı')

    def display_plan(self, results):
        self.plan=[]; self.plan_info={}; self.ptree.delete(*self.ptree.get_children())
        for info in results:
            u=info['unit']; p=u['path']; dst=info['dest']
            label=str(p)+(f" • (+{len(u['companions'])} bağlı öğe)" if u.get('companions') else '')
            row=self.ptree.insert('','end',values=(info['state'],u['category'] or 'Belirsiz',label,str(dst) if dst else 'Yerinde kalır',info['reason']))
            self.plan_info[row]=info
            if info['state']=='Hazır': self.plan.append((row,p,dst))
        from collections import Counter
        counts=Counter(info['unit']['category'].split('/')[0] for info in results if info['state']=='Hazır')
        self.category_summary.set(tr('  •  '.join(f'{name}: {n}' for name,n in sorted(counts.items()))))
        self.plan_summary.set(tr(f'{len(self.plan)} dosya / bütün paket hazır  •  {len(results)-len(self.plan)} yerinde kalacak  •  Ek veri kopyası: 0 B'))
        self.select_ready()
        self.status.set(tr('Plan hazır. Koruma nedenini görmek için bir satıra tıklayın. Uygulayana kadar hiçbir dosya taşınmaz.'))

    def select_ready(self):
        self.ptree.selection_set([r for r,_,_ in self.plan])

    def plan_details(self,event=None):
        row=self.ptree.focus()
        if row in self.plan_info:
            info=self.plan_info[row]
            extra=' | '.join(str(p.name) for p in info['unit'].get('companions',[]))
            self.plan_detail.set(tr(f"{info['unit']['path']}  →  {info['dest'] or 'Yerinde kalacak'}\n{info['reason']}"+(f' • Birlikte: {extra}' if extra else '')))

    def organize(self, all_ready=False):
        if self.busy: return
        selected={r for r,_,_ in self.plan} if all_ready else set(tr(self.ptree.selection()))
        infos=[self.plan_info[r] for r,_,_ in self.plan if r in selected]
        moves=[move for info in infos for move in info.get('moves',[(info['unit']['path'],info['dest'])])]
        if not moves: return
        if messagebox.askyesno(tr('Planı uygula'),tr(f'{len(infos)} dosya / bütün paket ({len(moves)} taşıma adımı) düzenlenecek. Projeler ve bağlı setler birlikte kalır. İşlem geçmişinden geri alınabilir. Devam edilsin mi?')):
            def work():
                # Refresh classification: do not execute a stale file plan if its parent became a project.
                checked=set()
                for index,info in enumerate(infos):
                    engine.notify(self.report_progress,'Plan güvenlik kontrolü',index,len(infos),info['unit']['path'])
                    for name,snapshot in info.get('snapshots',{}).items():
                        if engine.stat_key(Path(name)) != snapshot:
                            raise ValueError('Plan hazırlandıktan sonra öğe değişti. Yeniden analiz edin: '+name)
                for src,dst in moves:
                    for parent in (src.parent,*src.parent.parents):
                        if parent==self.scanbase.parent: break
                        if parent in checked: continue
                        checked.add(parent)
                        if engine.integrity_boundary(parent,root=parent==self.scanbase):
                            raise ValueError('Bu öğenin üst klasörü bütün korunması gereken paket olarak görünüyor. Yeniden analiz edin: '+str(src))
                self.transact(moves)
                self.events.put(('changed',f'{len(moves)} öğe kopyalanmadan taşındı. İşlem geçmişinden geri alabilirsiniz.'))
            self.launch(work,label='Dosyaları düzenleme / taşıma')

    def undo(self):
        if self.busy: return
        self.refresh_history()
        for row, (path, records) in self.history_rows.items():
            if any(r['state'] in ('moved','pending') for r in records):
                self.htree.selection_set(row)
                self.tabs.select(2)
                self.undo_selected()
                return
        messagebox.showinfo(tr('Geri al'),tr('Geri alınabilecek işlem bulunamadı.'))

    def refresh_history(self):
        selected = self.htree.selection()
        previous = self.history_rows[selected[0]][0] if selected and hasattr(self, 'history_rows') and selected[0] in self.history_rows else None
        self.htree.delete(*self.htree.get_children())
        self.history_rows = {}
        folder = Path(os.environ.get('LOCALAPPDATA',str(Path.home()))) / 'DosyaDuzeni'
        journals=list(folder.glob('islem_*.json'))+list(folder.glob('operation_*.json'))
        for path in sorted(journals,key=lambda p:p.name.split('_',1)[1],reverse=True):
            try:
                records = json.loads(path.read_text(encoding='utf-8'))
                if not records: continue
                stamp = records[0].get('created_at')
                date_format='%Y-%m-%d %H:%M:%S' if i18n.LANGUAGE=='en' else '%d.%m.%Y %H:%M:%S'
                date = datetime.fromisoformat(stamp).strftime(date_format) if stamp else datetime.fromtimestamp(path.stat().st_mtime).strftime(date_format)
                undone = sum(r['state']=='undone' for r in records)
                state = 'Windows Kutusu’ndan geri alınır' if any(r['state']=='recycled' for r in records) else 'Hata / geri alma kaydı' if any(r['state']=='failed' for r in records) else 'Geri alındı' if undone==len(records) else 'Kısmen geri alındı' if undone else 'Taşındı / Kontrol edilebilir'
                row = self.htree.insert('', 'end', text=tr(path.stem[-8:]), values=(date, records[0].get('action','Taşıma'),len(records),state))
                self.history_rows[row] = (path, records)
                if path == previous: self.htree.selection_set(row)
            except (OSError, ValueError, KeyError, TypeError):
                continue

    def history_details(self, event=None):
        selected = self.htree.selection()
        self.details.configure(state='normal'); self.details.delete('1.0','end')
        if selected and selected[0] in self.history_rows:
            path, records = self.history_rows[selected[0]]
            labels={'moved':'Taşıma','pending':'İşlem sürüyor…','undone':'Geri alındı','failed':'Hata / geri alma kaydı','recycled':'Windows Kutusu’ndan geri alınır'}
            self.details.insert('end', tr('\n\n'.join(f"{r['source']}\n→ {r['dest']}\nDurum: {labels.get(r['state'],r['state'])}" for r in records)))
        self.details.configure(state='disabled')

    def undo_selected(self):
        if self.busy: return
        selected = self.htree.selection()
        if not selected or selected[0] not in self.history_rows: return
        path, records = self.history_rows[selected[0]]
        active = sum(r['state'] in ('moved','pending') for r in records)
        if not active:
            messagebox.showinfo(tr('Geri al'),tr('Bu silmeyi Windows Geri Dönüşüm Kutusu’ndan geri yükleyin.' if any(r['state']=='recycled' for r in records) else 'Bu işlem zaten geri alınmış.')); return
        if not messagebox.askyesno(tr('Seçilen işlemi geri al'), tr(f'{active} öğe eski konumuna taşınacak. Var olan dosyaların üzerine yazılmaz. Devam edilsin mi?')): return
        def work():
            count = restore_journal(path,self.report_progress)
            self.events.put(('changed', f'{count} öğe eski konumuna taşındı. Yeniden analiz edin.'))
        self.launch(work,label='İşlemi geri alma')

if __name__ == '__main__':
    root=tk.Tk()
    ttk.Style().theme_use('clam')
    App(root)
    root.mainloop()
