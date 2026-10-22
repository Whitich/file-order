# File Order

Windows desktop organizer and exact duplicate finder with English and Turkish localization. Version 4.1. English is the default; the application remembers your language selection.

## Run

Requires Python 3.11+ with Tkinter (included in the standard Windows Python installer).

```powershell
python -m pip install -r requirements.txt
python file_order.py
```

You can also double-click `Start.bat`.

## Features

- Categorize independent documents, pictures, video, audio and other files.
- Keep projects, Minecraft worlds, servers, databases and other dependent packages intact.
- Verify exact duplicates using size filtering, SHA-256 and byte comparisons. Compare projects as complete directory trees, never remove shared CSS/assets individually.
- Reuse an existing destination layout; add numeric suffixes only for conflicting new files or complete packages.
- Dated move history, reversible quarantine and undo; Windows Recycle Bin deletion is restored through Windows.
- Visible operation stages, counts, percentages, file paths and elapsed time.

## Language and generated names

Use **Language** (or **Dil** in Turkish) to select **English** or **Türkçe**. Selection is saved locally. Switching language clears the current preview so destination paths are regenerated safely.

| Generated item | English | Türkçe |
| --- | --- | --- |
| Pictures folder | `Pictures` | `Resimler` |
| Projects folder | `Projects` | `Projeler` |
| Text folder | `Text` | `Metinler` |
| Intact packages | `Intact_Packages` | `Butun_Paketler` |
| Operation journal | `operation_*.json` | `islem_*.json` |
| Quarantine folder | `.FileOrder_Quarantine` | `.DosyaDuzeni_Karantina` |

Original file names and existing folders are never translated or renamed automatically. Both layouts remain recognizable for project/package boundaries and duplicate scanning. History in either language stays readable and undoable after switching.

Settings and history stay under `%LOCALAPPDATA%\DosyaDuzeni`. `settings.json` and the application data directory use stable internal names so changing language never disconnects existing history. The older `ayarlar.json` is migrated when settings are saved.

## Workflow

Choose a source and a destination on the same disk, analyze, review the plan, and apply it. For duplicates, use the dedicated buttons in **Duplicate files and projects**; scanning does not move or delete files. Keep one copy per group, review, then choose quarantine or Recycle Bin.

Detailed Turkish guide: [USER_GUIDE_TR.md](USER_GUIDE_TR.md).

## Limits

This is a development version. Integrity detection uses rules and cannot discover every proprietary application's dependencies. Manually protect special packages and review plans. Applications using absolute external paths may require relinking after a move. Same-volume moves do not duplicate file data; cross-volume moves are disabled. Permanently deleted files cannot be restored by this application.

## Tests

```powershell
python run_tests.py
```

Tests use temporary fixtures. Localization tests cover English defaults, persistent switching, generated names, preserving original names, bilingual boundaries/history/undo. Other regression tests exercise Turkish compatibility. No personal operation history, recovery reports or scanned user files are included.
