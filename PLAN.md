# Plan: Add Git Subtree Support to GMD
## ID: 1784084871.227013
## Created: 2026-07-15 03:07:51
## Status: completed

### Goal:
Add git subtree management capabilities to gmd-commit, allowing users to manage subtrees alongside submodules. Subtrees are alternative to submodules where external repos are merged into subdirectories with full history.

### Tasks (19):
1. [completed] Create gmd/gui/__init__.py and gmd/gui/main.py with Tkinter 
   ID: 1784084875.817157
   Progress logs: 2 entries

2. [completed] Create menu bar with File menu (Open Source, Open Destinatio
   ID: 1784084898.4503944
   Progress logs: 1 entries

3. [completed] Create two Treeview panels (left for source, right for desti
   ID: 1784084901.602261
   Progress logs: 1 entries

4. [completed] Add right-click (Button-3) context menu to both Treeview pan
   ID: 1784084904.3799584
   Progress logs: 1 entries

5. [completed] Implement automatic scan when directories are selected. Inte
   ID: 1784084907.153305
   Progress logs: 1 entries

6. [completed] Create bottom panel with action buttons: Preview, Sync, Diff
   ID: 1784084909.6607797
   Progress logs: 1 entries

7. [completed] Add progress bar widget to bottom of window. Create status b
   ID: 1784084912.3406227
   Progress logs: 1 entries

8. [completed] Find and integrate icons for file types (folder, file, modif
   ID: 1784084918.4583485

9. [completed] Create gmd-gui entry point script. Update setup.py with gui 
   ID: 1784084922.1473644

10. [pending] Create Subtree Data Model and Detection
   ID: 1784260209.2207522

11. [pending] Add Subtree Status Checking
   ID: 1784260211.6381989

12. [pending] Add Subtree Pull/Push Operations
   ID: 1784260217.3345308

13. [pending] Add Subtree to CLI Arguments
   ID: 1784260220.1887429

14. [pending] Update Config Schema for Subtrees
   ID: 1784260224.014986

15. [pending] Add Subtree Detection to CLI
   ID: 1784260226.8305998

16. [pending] Update Output Formatters for Subtrees
   ID: 1784260229.4195373

17. [pending] Create Subtree Example Config
   ID: 1784260231.9962807

18. [pending] Update Documentation for Subtrees
   ID: 1784260235.5008194

19. [pending] Add Subtree Tests
   ID: 1784260237.8536434

---

