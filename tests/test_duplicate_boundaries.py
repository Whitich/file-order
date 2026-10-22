import os,sys,tempfile,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import duzen_engine as e
import DosyaDuzeni as m

def write(p,data):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)/'organized';root.mkdir()
    for name in ['A','B','A_copy']:
        p=root/'Projeler'/name
        # No project manifest: the existing organizer boundary must still hold.
        write(p/'style.css',b'same css used in independent projects')
        write(p/'readme.txt',b'project A' if name!='B' else b'project B')
        write(p/'assets'/'image.png',b'shared asset')
    write(root/'Resimler'/'one.jpg',b'photo');write(root/'Resimler'/'renamed.jpg',b'photo')
    write(root/'Resimler'/'different.jpg',b'other')
    write(root/'Metinler'/'one.txt',b'text');write(root/'Metinler'/'two.txt',b'text')
    for name in ['world','world_copy']:
        write(root/'Butun_Paketler'/'Oyun_Dunyalari'/name/'level.dat',b'level')
        write(root/'Butun_Paketler'/'Oyun_Dunyalari'/name/'region'/'r.0.0.mca',b'region')
    units,issues=e.inventory(root,exclude=[root],purpose='duplicates')
    assert units,'Selected target was wrongly excluded'
    paths={u['path'] for u in units}
    assert all(root/'Projeler'/n in paths for n in ['A','B','A_copy'])
    assert not any(p.name in {'style.css','readme.txt','image.png','level.dat','r.0.0.mca'} for p in paths)
    groups,errors=e.find_duplicates(units)
    sets=[{p for p,f in g} for g in groups]
    expected=[{root/'Projeler'/'A',root/'Projeler'/'A_copy'},
              {root/'Resimler'/'one.jpg',root/'Resimler'/'renamed.jpg'},
              {root/'Metinler'/'one.txt',root/'Metinler'/'two.txt'},
              {root/'Butun_Paketler'/'Oyun_Dunyalari'/'world',root/'Butun_Paketler'/'Oyun_Dunyalari'/'world_copy'}]
    assert len(sets)==4 and all(s in sets for s in expected),(sets,errors)
    for g in groups:
        for p,f in g: e.assert_removable_unit(p,f,root)
    for illegal in [root/'Projeler'/'A'/'style.css',root/'Projeler'/'B'/'assets'/'image.png']:
        try: e.assert_removable_unit(illegal,False,root);raise AssertionError('Project child removal permitted')
        except ValueError:pass
    assert not e.inventory(root/'Projeler'/'A'/'assets',purpose='duplicates')[0]
    # Public UI command must ignore fast organizer mode and scan its own target.
    os.environ['LOCALAPPDATA']=str(Path(tmp)/'local')
    tk=m.tk.Tk();tk.withdraw();app=m.App(tk)
    app.target.set(str(root));app.organizer_only.set(True)
    pending=[];app.launch=lambda fn,**kwargs:pending.append(fn)
    app.scan_target_duplicates();assert len(pending)==1
    pending[0]();app.poll()
    assert len(app.groups)==4 and app.base.get()==str(root)
    app.select_extras();assert len(app.tree.selection())==4
    # Run actual reversible removal, not Windows deletion, only on fixtures.
    app.launch=lambda fn,**kwargs:fn()
    m.messagebox.askyesno=lambda *a,**k:True
    app.quarantine()
    assert (root/'Projeler'/'A'/'style.css').exists()
    assert (root/'Projeler'/'B'/'style.css').exists()
    assert not (root/'Projeler'/'A_copy').exists()
    journal=next((Path(tmp)/'local'/'DosyaDuzeni').glob('islem_*.json'))
    assert m.restore_journal(journal)==4
    assert (root/'Projeler'/'A_copy'/'assets'/'image.png').exists()
    tk.update();tk.destroy()
print('PASS: own-target duplicate scan, standalone photos/text, whole-project duplicates, shared CSS/assets protected, Minecraft worlds atomic, nested scope refused, dedicated UI command, bulk selection, reversible removal')
