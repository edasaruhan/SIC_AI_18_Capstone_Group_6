# NudgeWell development on Mac and Windows

Use GitHub to move committed work between computers. Each computer keeps its own Python environment and local AwareMind data; those folders are excluded from Git.

## Mac setup

This checkout is at `/Users/thynatos/Documents/IC`. Python 3.11 and OpenMP are installed through Homebrew, and `.venv` holds the analysis libraries and Jupyter.

To recreate the environment on another Mac:

```bash
brew install python@3.11 libomp
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

For an existing environment, start a session with:

```bash
cd /Users/thynatos/Documents/IC
source .venv/bin/activate
```

## Windows setup

Keep the existing PC checkout. After pulling these setup files, use Python 3.11 in PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

You can use `.\.venv\Scripts\python.exe` directly without changing PowerShell execution policy. Replace `python` with that path in the commands below if the environment is not activated.

## Switch computers

Before working, check that you are on the same branch you used on the other computer:

```bash
git status
git branch --show-current
git pull --ff-only
```

When finishing, review and commit the files you changed, then push:

```bash
git diff
git add <files-you-changed>
git commit -m "Describe the change"
git push
```

Use `git push -u origin <branch>` the first time you publish a new branch. On the other computer, run `git fetch` and `git switch --track origin/<branch>` the first time you use it. If a pull reports divergent histories, preserve both sets of commits and resolve them before continuing; do not force-push to bypass the conflict. Uncommitted or unpushed work on the PC will not appear on this Mac.

This Mac's repository uses the existing `Thynatos <badir03@hotmail.com>` commit identity, GitHub CLI credentials, fast-forward-only pulls, pruning of deleted remote branches and simple pushes. These are local settings; on the PC, `git config pull.ff only`, `git config fetch.prune true` and `git config push.default simple` apply the same sync defaults.

## Notebooks and analysis

Start Jupyter from `notebooks/`, because the existing notebook uses paths relative to that folder:

```bash
cd notebooks
python -m jupyterlab
```

Select the kernel belonging to this checkout's `.venv`. The Mac environment includes a **NudgeWell Python 3.11** kernel in its own Jupyter prefix. Stop Jupyter with Ctrl+C when finished.

From the repository root, run the Homework 4 analysis with:

```bash
python -I deliverables/04_data_preparation_model_exploration/code/hw4_pipeline.py data/raw/awaremind/full_data_all_feature.csv deliverables/04_data_preparation_model_exploration/run --quick
```

Remove `--quick` to include feature importance and demographics sensitivity analysis. Per-check-in predictions stay in the ignored `run/` folder. The existing synthetic checks also need a simulator that is not in this repository.

## Local dataset

Obtain the following files from the [AwareMind OSF project](https://osf.io/x6yzs/) and place them in `data/raw/awaremind/` on each computer:

- [full_data_all_feature.csv](https://osf.io/download/dz589/)
- [full_data_all_feature_dictonary.md](https://osf.io/download/a3zn2/)
- [app_categorization_dictionary.md](https://osf.io/download/wq7kb/)

The CSV used by the submitted work contains 5,772 rows, 92 columns and 5,627 unique rows. Follow [the dataset handling rules](data/README.md); raw data, processed data and participant predictions stay local. Re-download the original files separately on each computer rather than adding them to Git.

## Reports

The Python environment supports the analysis, figure builders and Word document builders. Rebuilding Homework 3 also requires the instructor's template at `guidelines/Concept_Note_and_Implementation_Plan_Template.docx`, which is not in Git; copy that file from the PC if needed. Existing PDF conversion scripts use Windows PowerShell and Microsoft Word; use the PC for that step. macOS may substitute fonts such as Segoe UI, so inspect layout before replacing a submitted report or figure. Existing submitted reports remain in `deliverables/`.
