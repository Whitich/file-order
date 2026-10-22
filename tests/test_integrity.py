import sys,tempfile,gzip,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import duzen_engine as e

def write(p,data=b'data'):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)/'archive';root.mkdir()
    cases={
        'java_world':['level.dat','region/r.0.0.mca','DIM-1/region/r.0.0.mca','playerdata/player.dat'],
        'bedrock':['level.dat','levelname.txt','db/CURRENT','db/00001.ldb'],
        'modded_server':['mods/mod.jar','config/mod.cfg','libraries/game.jar','world/level.dat','server.properties'],
        'game_install':['libraries/game.jar','versions/1.0/game.jar','assets/objects/a'],
        'database':['CURRENT','LOCK','000001.sst'],
        'vm':['machine.vmx','machine.vmdk','snapshots/disk.vmdk'],
        'profile':['prefs.js','places.sqlite','storage/default/db.sqlite'],
        'system_backup':['Program Files/app/app.exe','AppData/app/settings.json'],
        'unrecognized':['weird.custom','readme.txt','asset.jpg'],
        'game_data':['save.sav','notes.txt'],
    }
    for name,paths in cases.items():
        for path in paths: write(root/name/path)
    for name in ['a.pdf','b.docx','c.txt','d.jpg','e.mp4']:write(root/name)
    units,issues=e.inventory(root)
    for name in cases:
        found=[u for u in units if u['path']==root/name]
        assert len(found)==1 and found[0]['folder'],name
        assert not any(root/name in u['path'].parents for u in units),name
    for name in ['a.pdf','b.docx','c.txt','d.jpg','e.mp4']:
        assert any(u['path']==root/name and not u['folder'] for u in units),name
    for name in ['java_world','modded_server','profile']:
        sub=next((p for p in (root/name).iterdir() if p.is_dir()),None)
        if sub: assert not e.inventory(sub)[0],str(sub)
    assert all(info['state']=='Hazır' for info in e.build_plan(units,Path(tmp)/'organized'))
print('PASS: Minecraft Java/Bedrock, modded server, game installation, database, VM, profile, system backup, unknown bundles, game saves, loose documents')

