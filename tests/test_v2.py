import sys
import tempfile
import os
import threading
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import duzen_engine as e
import DosyaDuzeni as m

def write(p, data=b'content'):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)

with tempfile.TemporaryDirectory() as temp:
    p=Path(temp); base=p/'Downloads'; base.mkdir()
    write(base/'archive'/'2024'/'a.pdf')
    write(base/'archive'/'2025'/'a.pdf')
    write(base/'unknown.xyz')
    write(base/'web'/'package.json',b'{}')
    write(base/'web'/'assets'/'image.png')
    write(base/'web'/'bin'/'app.exe')
    write(base/'mystery'/'something.unknown')
    write(base/'mystery'/'image.png')
    write(base/'photos'/'image.png',b'picture')
    stop=threading.Event()
    units,issues=e.inventory(base,stop=stop)
    paths={u['path'] for u in units}
    assert base/'web' in paths and base/'web'/'assets'/'image.png' not in paths
    assert base/'mystery' in paths and base/'mystery'/'image.png' not in paths
    assert base/'archive'/'2024'/'a.pdf' in paths
    protected,notes=e.inventory(base/'web'/'assets')
    assert not protected and notes
    target=p/'sorted'
    write(target/'PDF'/'a.pdf',b'existing')
    plan=e.build_plan(units,target)
    ready=[r for r in plan if r['state']=='Hazır']
    pdf=[r for r in ready if r['unit']['category']=='PDF']
    assert len(pdf)==2 and len({r['dest'] for r in pdf})==2
    assert all(r['dest'].name!='a.pdf' for r in pdf)
    assert next(r for r in plan if r['unit']['path']==base/'unknown.xyz')['dest'] is not None
    assert next(r for r in plan if r['unit']['path']==base/'mystery')['dest'] is not None
    with patch.object(e,'same_volume',return_value=False):
        assert not any(r['state']=='Hazır' for r in e.build_plan(units,target))
    groups,errors=e.find_duplicates(units,stop)
    assert any({base/'archive'/'2024'/'a.pdf',base/'archive'/'2025'/'a.pdf'} <= {x[0] for x in g} for g in groups)
    # Size-only pruning: unique sizes must never reach the hash reader.
    a=p/'unique'; write(a,b'12345678901234567890')
    with patch.object(e,'hash_file',side_effect=AssertionError('unnecessary content read')):
        assert e.find_duplicates([{'path':a,'folder':False,'size':20}])[0]==[]
    stop.set()
    try: e.inventory(base,stop=stop); raise AssertionError('cancel ignored')
    except e.Cancelled: pass
    stop.clear()
    # Same-size different data must not appear as duplicate.
    b=p/'different'; write(b,b'12345678901234567891')
    assert not e.find_duplicates([{'path':a,'folder':False},{'path':b,'folder':False}])[0]
    os.environ['LOCALAPPDATA']=str(p/'local')
    root=m.tk.Tk(); root.withdraw(); app=m.App(root)
    app.inventory=units; app.units=[(u['path'],u['folder']) for u in units]
    app.display_plan(plan)
    assert len(app.ptree.selection())==len(ready)
    src=base/'web'; dst=target/'Projeler'/'web'
    inode=src.stat().st_ino
    journal=app.transact([(src,dst)])
    assert dst.stat().st_ino==inode and (dst/'assets'/'image.png').exists()
    assert m.restore_journal(journal)==1 and (src/'assets'/'image.png').exists()
    # Full preflight prevents partial mutation on target collision.
    a2=p/'one'; b2=p/'two'; write(a2); write(b2)
    try: app.transact([(a2,p/'new'),(b2,p/'new')]); raise AssertionError('collision accepted')
    except ValueError: pass
    assert a2.exists() and b2.exists() and not (p/'new').exists()
    with patch.object(e,'same_volume',return_value=False):
        try: app.transact([(a2,p/'new')]); raise AssertionError('cross volume accepted')
        except ValueError: pass
    assert a2.exists()
    app.refresh_history(); root.update(); root.destroy()
print('PASS: nested archives, project/asset boundaries, unknown files, collisions, duplicate verification, size pruning, cancellation, same-volume rename identity, undo, preflight, UI')
