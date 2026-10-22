import os,sys,tempfile,json,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.pop('FILE_ORDER_LANGUAGE',None)
import localization as loc
import DosyaDuzeni as appmod
import duzen_engine as engine

def write(p,data=b'data'):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)

with tempfile.TemporaryDirectory() as temp:
    p=Path(temp);os.environ['LOCALAPPDATA']=str(p/'local')
    tk=appmod.tk.Tk();tk.withdraw();app=appmod.App(tk)
    assert loc.LANGUAGE=='en' and app.language_value.get()=='English'
    assert app.analysis_button['text']=='Analyze folder'
    assert tk.title().startswith('File Order')
    # Check all initial labels, tabs, headings and variable-bound status messages.
    turkish=re.compile('[çğıöşüÇĞİÖŞÜ]')
    def inspect(widget):
        if widget is app.language_combo:return
        for key in ('text','textvariable'):
            try:
                value=str(widget.cget(key))
                if key=='textvariable' and value:value=str(tk.getvar(value))
                assert not turkish.search(value),(type(widget).__name__,key,value)
            except appmod.tk.TclError:pass
        for child in widget.winfo_children():inspect(child)
    inspect(tk)
    for tab in app.tabs.tabs():assert not turkish.search(app.tabs.tab(tab,'text'))
    source=p/'archive';target=p/'organized'
    write(source/'Türkçe resim.jpg');write(source/'notes.txt')
    write(source/'repo'/'a.sln');write(source/'repo'/'assets'/'photo.jpg')
    write(source/'world'/'level.dat');write(source/'world'/'region'/'r.0.0.mca')
    units,_=engine.inventory(source);plan=engine.build_plan(units,target)
    moves=[m for row in plan if row['state']=='Hazır' for m in row['moves']]
    assert any(dst==target/'Pictures'/'Türkçe resim.jpg' for src,dst in moves)
    assert any(dst==target/'Projects'/'repo' for src,dst in moves)
    assert any(dst==target/'Intact_Packages'/'Game_Worlds'/'world' for src,dst in moves)
    journal=app.transact(moves)
    assert journal.name.startswith('operation_')
    assert json.loads(journal.read_text())[0]['action']=='Organization'
    # An English-generated project is still atomic during duplicate scanning.
    scanned,_=engine.inventory(target,purpose='duplicates')
    assert any(u['path']==target/'Projects'/'repo' and u['folder'] for u in scanned)
    assert not any(u['path'].name=='a.sln' for u in scanned)
    app.base.set(str(source));app.target.set(str(target))
    app.language_value.set('Türkçe');app.change_language()
    app=tk.file_order_app
    assert loc.LANGUAGE=='tr' and app.analysis_button['text']=='Klasörü analiz et'
    assert json.loads(app.settings_path.read_text())['language']=='tr'
    assert journal in [item[0] for item in app.history_rows.values()]
    assert appmod.restore_journal(journal)==len(moves)
    units,_=engine.inventory(source);trplan=engine.build_plan(units,target)
    assert any(row['dest']==target/'Resimler'/'Türkçe resim.jpg' for row in trplan)
    trmoves=[m for row in trplan if row['state']=='Hazır' for m in row['moves']]
    trjournal=app.transact(trmoves);assert trjournal.name.startswith('islem_')
    assert loc.generated_name('quarantine')=='.DosyaDuzeni_Karantina'
    # Fresh App reads persisted Turkish; switch back and verify English undo.
    assert json.loads(app.settings_path.read_text())['language']=='tr'
    app.language_value.set('English');app.change_language();app=tk.file_order_app
    assert loc.LANGUAGE=='en'
    assert trjournal in [item[0] for item in app.history_rows.values()]
    assert appmod.restore_journal(trjournal)==len(trmoves)
    assert (source/'Türkçe resim.jpg').exists()
    assert loc.tr(r'Source G:\Resimler\Türkçe.jpg')==r'Source G:\Resimler\Türkçe.jpg'
    assert loc.generated_name('quarantine')=='.FileOrder_Quarantine'
    tk.after_cancel(app.poll_id)
    for child in tk.winfo_children():child.destroy()
    fresh=appmod.App(tk)
    assert loc.LANGUAGE=='en' and fresh.language_value.get()=='English'
    tk.destroy()
print('PASS: English default, translated UI, persistent switching, localized output folders/journal/quarantine names, source names preserved, bilingual package protection/history/undo')
