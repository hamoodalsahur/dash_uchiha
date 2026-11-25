# GitHub for our team — the easy version

You only need **6 words** and **1 loop**. Everything else is details.

## The 6 words

| Word | Plain meaning |
|---|---|
| **Repo** | The shared project folder, stored on GitHub |
| **main** | The "official" version of the project. Always works. Nobody edits it directly |
| **Branch** | Your private copy to work on one task, e.g. `coder2/drop-persistent-first` |
| **Commit** | A save point with a short note ("what I changed") |
| **Push / Pull** | Push = upload your commits to GitHub. Pull = download everyone else's |
| **Pull request (PR)** | "Please add my branch into main." A teammate checks it, then it gets merged |

## The 1 loop (do this for every task)

```
1. Pull main            (get the latest)
2. Make a branch        (role/short-task-name)
3. Work + commit often  (small save points)
4. Push the branch
5. Open a pull request  → tests run automatically (green ✓ or red ✗)
6. One teammate reviews → Merge → delete the branch
7. Back to step 1
```

Rule of thumb: **one task = one branch = one pull request**, ideally finished the same day.

---

## Part A — One-time setup by the repo owner (≈ 15 min)

Pick **one** person as owner (suggest: Coder 1).

1. **Unzip** `atlas_repo.zip` somewhere **outside** OneDrive / Google Drive sync folders (sync tools corrupt Git folders).
2. **Create the repo from that folder with GitHub Desktop** (no need to create anything on github.com first):
   - Install GitHub Desktop (desktop.github.com) and sign in with your GitHub account.
   - **File → Add local repository →** choose the `atlas` folder → it says "this directory does not appear to be a Git repository" → click **create a repository** → keep Name `atlas`, set **Git ignore = None** and **License = None** (we already have them) → **Create repository**.
   - Left panel shows all files. Summary box: `Initial commit: Atlas starter pipeline` → **Commit to main**.
   - Click **Publish repository** → make sure **Keep this code private** is **ticked** → **Publish**.
3. **Invite the team.** On github.com: repo → **Settings → Collaborators → Add people** → add the other three GitHub usernames. They must accept the email invite.
   - Do **not** add the supervising lecturer as a collaborator with write access (the rules say the supervisor advises only). Read-only sharing of the final PDF is fine.
4. **Check automatic tests run.** Repo → **Actions** tab → you should see a "tests" run with a green ✓ within ~2 minutes. If GitHub asks to enable Actions, click enable.
5. **Protect main (if available).** Settings → Branches → **Add branch protection rule** → Branch name `main` → tick **Require a pull request before merging** and **Require status checks to pass** (choose `pytest`).
   - GitHub only allows this on private repos for **Pro** accounts. Students often get Pro free through the **GitHub Student Developer Pack** (education.github.com). If the option isn't there, skip it and follow the team rule: **nobody pushes directly to main.**

## Part B — Every member's setup (≈ 10 min)

1. Accept the invite email.
2. Install **GitHub Desktop** and **Python 3.11 or newer**. (Power BI pro: also Power BI Desktop.)
3. GitHub Desktop → **File → Clone repository** → pick `atlas` → choose a folder **outside** OneDrive/Google Drive sync folders (sync tools corrupt Git folders).
4. Open a terminal in that folder (GitHub Desktop: **Repository → Open in Command Prompt / Terminal**) and run:
   ```
   python -m venv .venv
   .venv\Scripts\activate          (Mac: source .venv/bin/activate)
   pip install -r requirements.txt
   python -m pytest -q
   ```
   You should see **36 passed**. If not, post the error in the group chat before doing anything else.
5. Set your Git name to your real name (GitHub Desktop → File → Options → Git). Commits are our evidence of who did what for the AI declaration.

## Part C — The daily loop in GitHub Desktop (click by click)

**Start a task**
1. Top bar: **Current branch → main**. Click **Fetch origin**, then **Pull origin**.
2. **Current branch → New branch** → name it `role/task`, e.g. `coder1/map-aliases`, `pbi/page1-map`, `docs/lit-review-refs`. Base it on **main**.

**Work**
3. Edit files normally (VS Code, Power BI, anything). GitHub Desktop shows changed files on the left.
4. Commit often: tick the files that belong to this change → write a summary like `map: add 5 district name aliases` → **Commit to coder1/map-aliases**.
   - Good message = *area: what changed*. Bad message = "update", "fix", "asdf".

**Share**
5. Click **Publish branch** (first time) / **Push origin** (after).
6. Click **Create Pull Request** → it opens GitHub in the browser → fill the template (it has a checklist) → **Create pull request**.
7. Wait for the automatic check: green ✓ = tests passed; red ✗ = something broke (click "Details" to see which test).

**Review (the teammate)**
8. Open the PR → **Files changed** → read it. If it changes code, pull the branch in GitHub Desktop and run `python -m pytest -q` yourself.
9. Comment on any line you don't understand. When happy: **Review changes → Approve**.
10. The author clicks **Merge pull request → Confirm** → **Delete branch**.

**Everyone else**
11. Next time you start a task: switch to main → **Pull origin**. Now you have the merged work.

## Part D — Team rules (read twice)

1. **Never commit directly to main.** Always branch → PR.
2. **Pull main every morning and before opening a PR.**
3. **Stay in your lane** (see the ownership table in README.md). Need a change in someone else's area? Open an Issue or ask them.
4. **The .pbix has one editor: the Power BI pro.** Power BI files can't be merged; two people editing = one person's work lost.
5. **data/ has one editor: Coder 1.** If DOSM data is re-downloaded, it's one PR with the new `retrieval_log.csv`.
6. **After the Thursday 22:00 gate, numbers are frozen.** Code changes only for bugs, and any PR that changes a number must list before/after in the PR template.
7. **Never commit:** videos, report drafts, passwords/API keys, personal files, anything over ~50 MB. Videos and the report live on Google Drive.
8. **Never use "force push"** or delete someone else's branch.
9. **Small PRs.** A reviewer can check 50 changed lines in 5 minutes; 2,000 lines never gets reviewed properly.
10. **Red ✗ on a PR = don't merge.** Fix it first (ask Coder 2 if stuck).

## Part E — Tonight's practice round (≈ 20 min, everyone)

Each person makes one real, tiny PR, so you learn the loop before it matters:

| Who | Branch | Task |
|---|---|---|
| Coder 2 | `coder2/drop-persistent-first` | In `export_powerbi.py` (line 56, inside `modes`), delete `, "Persistent first": "s_persistent_first"` so the line ends `"KPX": "s_kpx_2022"},` (decision D11). Run tests + `python export_powerbi.py`. Commit code **and** the regenerated `powerbi_tables/`. |
| Coder 1 | `coder1/map-aliases` | Add a `dashboard/map/aliases.csv` with the 5 alias rows from Handbook Section 8 (Kulai→Kulaijaya, Tangkak→Ledang, Nabawan→Nabawan / Persiangan, W.P. Kuala Lumpur→Kuala Lumpur, W.P. Labuan→Labuan). |
| Power BI pro | `pbi/dashboard-skeleton` | Save an empty `dashboard/Atlas.pbix` with the 5 CSVs loaded and relationships set. |
| Document maker | `docs/team-names` | In `docs/decision_log.md`, add D15: the real names next to each role. |

Review each other's PRs in a circle: Coder 1 → Coder 2 → Power BI pro → Document maker → Coder 1.

## Part F — When things go wrong

| Problem | What it means | Fix |
|---|---|---|
| **"Push rejected" / "fetch first"** | Someone pushed to your branch, or you're on main | Click **Pull origin**, then push again. If you were on main by mistake, see next row |
| **I committed to main by accident** (not pushed yet) | The commit is only on your laptop | **History** tab → right-click your commit → **Undo commit** (your edits come back as unsaved changes) → **Current branch → New branch** → choose **Bring my changes** → commit there → push → PR. Already pushed to main? Tell the team; don't try to undo it yourself |
| **Merge conflict** | Two people changed the same lines | GitHub Desktop shows the conflicted file → **Open in editor** → you'll see `<<<<<<<`, `=======`, `>>>>>>>` markers. Keep the right lines, delete the markers, save → **Continue merge**. Not sure? Ask the file's owner and decide together |
| **Conflict in a .pbix** | Two people edited the dashboard | Can't merge. Keep the Power BI pro's version (**Use the version from main**), redo the other change manually |
| **Red ✗ on my PR** | A test failed | Click **Details** → read the failing test name → run `python -m pytest -q` locally → fix → commit → push (the PR updates itself) |
| **I committed a file I shouldn't** (video, password) | It's in history | Tell the owner immediately. For a password/API key: change the password first. Don't try to rewrite history yourself |
| **My local copy is a mess** | Happens to everyone | Commit or copy out anything you need, then **Repository → Show in Explorer**, delete the folder, and clone again |
| **Python can't find `kantung`** | Running from the wrong folder | Open the terminal in the repo's top folder (the one with README.md) |

## Part G — Optional but handy

- **Issues as a task board:** repo → **Issues → New issue** for each task (title + owner). Put `Closes #12` in a PR description and the issue closes on merge. **Projects** tab can show them as a board (To do / Doing / Done).
- **Command-line cheat sheet** (if you prefer it over GitHub Desktop):
  ```
  git switch main && git pull
  git switch -c coder1/map-aliases
  git add dashboard/map/aliases.csv
  git commit -m "map: add 5 district name aliases"
  git push -u origin coder1/map-aliases
  # then open the PR on github.com
  ```
- **Commit message prefixes:** `data:`, `model:`, `export:`, `dashboard:`, `map:`, `docs:`, `test:`, `fix:`.
- **Ask your Claude:** paste the error message and say "I'm using GitHub Desktop and I'm new to Git; tell me the safest fix step by step."
