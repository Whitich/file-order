import sys, os, tempfile, json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import duzen_engine as e
import DosyaDuzeni as m

def write(p,b=b'data'):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b)

with tempfile.TemporaryDirectory() as temp:
    root_path=Path(temp); source=root_path/'Downloads'; source.mkdir()
    loose=['notes.txt','report.docx','paper.pdf','photo.JPG','clip.mp4','image.heic','drawing.psd','installer.exe','data.xyz','plain','readme.md','config.json']
    for name in loose: write(source/name)
    write(source/'mixed'/'notes.txt'); write(source/'mixed'/'photo.png'); write(source/'mixed'/'unknown.zzz')
    write(source/'deeper'/'2024'/'notes.txt'); write(source/'deeper'/'2024'/'report.doc')
    write(source/'code_project'/'package.json',b'{}'); write(source/'code_project'/'assets'/'photo.jpg'); write(source/'code_project'/'guide.pdf')
    write(source/'app'/'run.exe'); write(source/'app'/'engine.dll'); write(source/'app'/'assets'/'pic.png')
    write(source/'creative'/'scene.blend'); write(source/'creative'/'textures'/'map.jpg')
    write(source/'site'/'index.html'); write(source/'site'/'css'/'main.css')
    write(source/'script_project'/'run.py',b"open('input.txt').read()"); write(source/'script_project'/'input.txt')
    write(source/'standalone_script.py',b"print('hello world')")
    write(source/'album'/'DSC001.nef'); write(source/'album'/'DSC001.jpg'); write(source/'album'/'DSC001.xmp')
    write(source/'movies'/'movie.mp4'); write(source/'movies'/'movie.srt')
    write(source/'saved'/'page.html'); write(source/'saved'/'page_files'/'picture.png')
    write(source/'assets'/'loose_resource.png')
    target=source/'Duzenli'
    write(target/'PDF'/'existing.pdf')
    units,issues=e.inventory(source,exclude=[target])
    paths={u['path'] for u in units}
    for name in loose+['standalone_script.py']: assert source/name in paths,name
    for name in ['deeper/2024/notes.txt','deeper/2024/report.doc']:
        assert source/name in paths,name
    for name in ['code_project','app','creative','site','script_project','assets','mixed']:
        assert source/name in paths,name
        assert not any(source/name in p.parents for p in paths),name
    assert not any(target==p or target in p.parents for p in paths)
    assert e.project_reason(source)==''
    assert not e.inventory(source/'code_project'/'assets')[0]
    plan=e.build_plan(units,target)
    assert all(info['state']=='Hazır' for info in plan),[(r['unit']['path'],r['reason']) for r in plan if r['state']!='Hazır']
    # Every file is either moved standalone, inside an atomic folder, or in a paired set.
    moves=[move for info in plan for move in info['moves']]
    all_files=[p for p in source.rglob('*') if p.is_file() and target not in p.parents]
    for f in all_files:
        assert sum(f==src or src in f.parents for src,dst in moves)==1,f
    for name in ['album/DSC001.xmp','movies/movie.srt','saved/page_files']:
        assert any(src==source/name for src,dst in moves),name
    for info in plan:
        if info['unit'].get('companions'):
            assert len({dst.parent for src,dst in info['moves']})==1
    os.environ['LOCALAPPDATA']=str(root_path/'local')
    tk=m.tk.Tk(); tk.withdraw(); app=m.App(tk); app.scanbase=source
    app.inventory=units; app.display_plan(plan)
    assert len(app.plan)==len(units)
    # Selecting one row must not limit the all-ready action.
    app.ptree.selection_set(app.plan[0][0]); called=[]
    with patch.object(m.messagebox,'askyesno',side_effect=lambda title,body:called.append(body) or False): app.organize(all_ready=True)
    assert f'{len(units)} dosya' in called[0]
    fingerprints={str(src):src.stat().st_ino for src,dst in moves}
    journal=app.transact(moves)
    assert all(dst.exists() and dst.stat().st_ino==fingerprints[str(src)] for src,dst in moves)
    assert (target/'Projeler'/'code_project'/'assets'/'photo.jpg').exists()
    assert (target/'Metinler'/'notes.txt').exists()
    assert any((target/'Resimler').rglob('photo.JPG'))
    assert m.restore_journal(journal)==len(moves)
    assert all(f.exists() for f in all_files)
    # Failure after first rename rolls the first rename back.
    x=root_path/'x.txt'; y=root_path/'y.txt'; write(x);write(y)
    rename=os.rename
    def failing(src,dst):
        if Path(src)==y: raise PermissionError('injected locked file')
        return rename(src,dst)
    with patch.object(m.os,'rename',side_effect=failing):
        try: app.transact([(x,root_path/'newx.txt'),(y,root_path/'newy.txt')]); raise AssertionError('failure not raised')
        except ValueError as error: assert 'geri alındı' in str(error)
    assert x.exists() and y.exists() and not (root_path/'newx.txt').exists()
    tk.update(); tk.destroy()
print('PASS: complete recursive coverage, 12 loose types, unknown files, five project/package types, photo sidecars, RAW/JPEG, video subtitles, saved HTML resources, internal target exclusion, all-ready action, rename identity, complete undo, automatic rollback')
