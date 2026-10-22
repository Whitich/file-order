import sys,os,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import organizer_engine as e
import file_order as m
def write(p,data=b'new'):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
def apply(app,source,target):
    units,issues=e.inventory(source,exclude=[target]);plan=e.build_plan(units,target)
    moves=[move for row in plan if row['state']=='Hazır' for move in row['moves']]
    j=app.transact(moves) if moves else None
    return plan,j
with tempfile.TemporaryDirectory() as temp:
    base=Path(temp);target=base/'organized';os.environ['LOCALAPPDATA']=str(base/'local')
    root=m.tk.Tk();root.withdraw();app=m.App(root)
    one=base/'first';two=base/'second'
    for s in [one,two]:
        write(s/'photo.jpg',s.name.encode());write(s/'document.pdf',s.name.encode())
        write(s/'project'/'a.sln');write(s/'project'/'unrecognized.custom');write(s/'project'/'assets'/'image.png')
        write(s/'world'/'level.dat');write(s/'world'/'region'/'r.0.0.mca')
        write(s/'movie.mp4');write(s/'movie.srt')
    _,j1=apply(app,one,target);_,j2=apply(app,two,target)
    assert (target/'Resimler'/'photo.jpg').read_bytes()==b'first'
    assert (target/'Resimler'/'photo (2).jpg').read_bytes()==b'second'
    assert (target/'PDF'/'document (2).pdf').exists()
    assert (target/'Projeler'/'project'/'assets'/'image.png').exists()
    assert (target/'Projeler'/'project (2)'/'assets'/'image.png').exists()
    assert (target/'Butun_Paketler'/'Oyun_Dunyalari'/'world (2)'/'region'/'r.0.0.mca').exists()
    assert not (target/'Resimler (2)').exists() and not (target/'Projeler (2)').exists()
    assert (target/'Videolar'/'Bagli_Setler'/'movie (2)'/'movie.srt').exists()
    # Existing empty set folder is reused, without creating an unnecessary suffix.
    three=base/'third';write(three/'clip.mp4');write(three/'clip.srt')
    (target/'Videolar'/'Bagli_Setler'/'clip').mkdir(parents=True)
    apply(app,three,target)
    assert (target/'Videolar'/'Bagli_Setler'/'clip'/'clip.mp4').exists()
    assert not (target/'Videolar'/'Bagli_Setler'/'clip (2)').exists()
    # Legacy generic packages can be reclassified into the same target safely.
    legacy=target/'Butun_Paketler'/'Incelenecek_Paketler'
    write(legacy/'unusual_archive'/'opaque.xyz')
    write(legacy/'unusual_archive'/'separate_repo'/'project.sln')
    write(legacy/'unusual_archive'/'album'/'archive_photo.jpg')
    write(legacy/'repo'/'a.csproj');write(legacy/'repo'/'opaque.xyz');write(legacy/'repo'/'assets'/'a.jpg')
    write(legacy/'Masaüstü'/'loose.jpg');write(legacy/'Masaüstü'/'loose.pdf');write(legacy/'Masaüstü'/'opaque.xyz')
    plan,j3=apply(app,target/'Butun_Paketler',target)
    assert (target/'Projeler'/'repo'/'assets'/'a.jpg').exists()
    assert (target/'Resimler'/'loose.jpg').exists()
    assert (target/'PDF'/'loose.pdf').exists()
    assert (target/'Projeler'/'separate_repo'/'project.sln').exists()
    assert (target/'Resimler'/'archive_photo.jpg').exists()
    assert (target/'Butun_Paketler'/'Oyun_Dunyalari'/'world'/'level.dat').exists()
    assert all(row['state']!='Hazır' for row in plan if row['unit']['path'].name in {'world','world (2)'})
    # Each run can be independently undone in reverse order.
    m.restore_journal(j3);m.restore_journal(j2);m.restore_journal(j1)
    assert (one/'project'/'assets'/'image.png').exists() and (two/'photo.jpg').exists()
    app.target.set(str(target));app.save_settings()
    second=m.App(root);assert second.target.get()==str(target)
    root.update();root.destroy()
print('PASS: repeated target reuse, category reuse, conflict numbering, atomic worlds/projects, sidecar set reuse, legacy package reclassification, independent undo, remembered target')
