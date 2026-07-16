# Publishing the course website

The public website is published with GitHub Pages. The source lives on the
`main` branch and the rendered website is written automatically to the
`gh-pages` branch.

## First publication

1. Create an empty public repository on GitHub. Do not add a README, licence or
   `.gitignore` when creating it.
2. Copy the repository URL shown by GitHub.
3. In this project folder, connect the local repository and push it:

   ```bash
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
   git push -u origin main
   ```

4. Open the repository's **Actions** tab and wait for **Publish Quarto website**
   to finish. The first run creates the `gh-pages` branch automatically.
5. On GitHub, open **Settings > Pages**. Under **Build and deployment**, set
   **Source** to **Deploy from a branch**, select the `gh-pages` branch and the
   `/(root)` folder, then save.
6. GitHub will display the public URL in **Settings > Pages**.

The usual URL is:

```text
https://YOUR-USERNAME.github.io/YOUR-REPOSITORY/
```

## Publishing later changes

Check the project locally before publishing:

```bash
python3 scripts/check_project.py
quarto render
```

Then commit and push the changes:

```bash
git add .
git commit -m "Describe the course update"
git push
```

Every push to `main` starts the publishing workflow. It can also be run
manually from **Actions > Publish Quarto website > Run workflow**.

## Important details

- `_site/` is deliberately excluded from `main`; the workflow creates the
  published copy on `gh-pages`.
- Keep Quarto's `_freeze/` results under version control. This lets GitHub
  render the pages without rerunning the teaching notebooks.
- Publishing makes the website and the public repository visible to everyone.
- Notebook code is displayed on the website, but it runs only after a
  participant downloads and opens the notebook in a Python environment.
