import os,sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import duzen_engine as e
import DosyaDuzeni as m

with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp);source=p/'documents';source.mkdir();target=p/'target'
    (source/'one.txt').write_bytes(b'abc'*1000000)
    (source/'two.txt').write_bytes(b'abc'*1000000)
    events=[]
    units,_=e.inventory(source,progress=events.append)
    groups,_=e.find_duplicates(units,progress=events.append)
    plan=e.build_plan(units,target,progress=events.append)
    assert len(groups)==1
    phases={x['phase'] for x in events}
    assert {'Klasör taranıyor','Taşıma planı hazırlanıyor','Tam içerik doğrulama','Dosya içeriği okunuyor','Bayt karşılaştırması'}<=phases
    assert any(x['unit']=='bayt' and x['done']==x['total']==3000000 for x in events)
    os.environ['LOCALAPPDATA']=str(p/'local')
    root=m.tk.Tk();root.withdraw();app=m.App(root)
    app.operation_started=time.monotonic();app.operation_name='Test'
    app.render_progress({'phase':'Tarama','done':12,'total':None,'path':'folder','unit':'öğe'})
    assert str(app.progress_bar.cget('mode'))=='indeterminate'
    assert 'toplam belirleniyor' in app.operation_metrics.get()
    app.render_progress({'phase':'Taşıma','done':2,'total':10,'path':'file.txt','unit':'öğe'})
    assert float(app.progress_bar['value'])==20 and '2 / 10' in app.operation_metrics.get()
    assert 'Taşıma' in app.operation_label.get() and app.operation_path.get()=='file.txt'
    recorded=[];app.report_progress=lambda event:recorded.append(event)
    journal=app.transact([(source/'one.txt',target/'one.txt')])
    assert any(x['phase']=='Dosyalar taşınıyor' and x['done']==x['total']==1 for x in recorded)
    restored=[];m.restore_journal(journal,restored.append)
    assert any(x['phase']=='Dosyalar eski konumuna taşınıyor' and x['done']==1 for x in restored)
    # Exercise actual worker -> UI queue -> terminal state.
    def wait():
        deadline=time.monotonic()+4
        while app.busy and time.monotonic()<deadline:root.update();time.sleep(.005)
        assert not app.busy
    app.launch(lambda:app.events.put(('status','Test tamamlandı')),label='Başarılı test');wait()
    assert 'TAMAMLANDI' in app.operation_label.get() and float(app.progress_bar['value'])==100
    m.messagebox.showerror=lambda *args:None
    def fail():raise ValueError('test failure')
    app.launch(fail,label='Hatalı test');wait()
    assert 'HATA' in app.operation_label.get() and float(app.progress_bar['value'])==0
    def cancel():raise e.Cancelled('Test durduruldu')
    app.launch(cancel,label='İptal testi');wait()
    assert 'DURDURULDU' in app.operation_label.get() and float(app.progress_bar['value'])==0
    root.destroy()
print('PASS: scan/hash/byte/plan progress, unknown totals, counters, percentages, file paths, transfer/undo counts, worker completion, error state, cancellation state')
