import os,sys,tempfile,time,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import file_order as m

with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp);os.environ['LOCALAPPDATA']=str(p/'local')
    folder=p/'organized';(folder/'Resimler').mkdir(parents=True)
    (folder/'Resimler'/'a.jpg').write_bytes(b'test image')
    (folder/'Resimler'/'b.jpg').write_bytes(b'test image')
    root=m.tk.Tk();root.attributes('-alpha',0.0)
    app=m.App(root);app.tabs.select(0)
    for width,height in [(1240,860),(1100,700)]:
        root.geometry(f'{width}x{height}');root.update()
        assert app.progress_card.winfo_y()<app.tabs.winfo_y()
        assert app.progress_bar.winfo_rooty()+app.progress_bar.winfo_height()<root.winfo_rooty()+root.winfo_height()
        assert app.duplicate_button.winfo_ismapped()
    app.target.set(str(folder));app.scan_target_duplicates()
    assert app.busy and app.duplicate_button.instate(['disabled'])
    assert 'başladı' in app.status.get()
    deadline=time.monotonic()+5
    while app.busy and time.monotonic()<deadline:root.update();time.sleep(.005)
    assert not app.busy and len(app.groups)==1
    assert not app.duplicate_button.instate(['disabled'])
    assert 'TAMAMLANDI' in app.operation_label.get()
    root.destroy()
print('PASS: progress above tabs at 860/700px, visible scan controls, immediate start feedback, disabled concurrent starts, real target scan, completion and restored controls')
