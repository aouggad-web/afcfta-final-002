# Contributing to AfCFTA / ZLECAf Trade Calculator

Thank you for your interest in contributing! This guide explains how to upload a new file from your local computer to this repository.

---

## How to Upload a File from Your Local Machine

### Option 1: Using the GitHub Web Interface (Easiest)

1. Go to the repository page: [https://github.com/aouggad-web/afcfta-final-001](https://github.com/aouggad-web/afcfta-final-001)
2. Navigate to the folder where you want to add your file.
3. Click **"Add file"** → **"Upload files"**.
4. Drag and drop your file, or click **"choose your files"** to browse.
5. Scroll down, add a short commit message (e.g., `Add my new file`).
6. Click **"Commit changes"**.

---

### Option 2: Using Git on Your Desktop (Recommended for developers)

**Step 1 – Clone the repository** (skip this step if you already have a local copy):

```bash
git clone https://github.com/aouggad-web/afcfta-final-001.git
cd afcfta-final-001
```

**Step 2 – Copy your new file** into the cloned folder (e.g., using Finder, File Explorer, or `cp`):

```bash
cp /path/to/your/file .
```

**Step 3 – Stage the file:**

```bash
git add your-file-name
```

**Step 4 – Commit the file:**

```bash
git commit -m "Add my new file"
```

**Step 5 – Push to GitHub:**

```bash
git push origin main
```

> If you are working on a feature branch, replace `main` with your branch name.

---

### Option 3: Fork → Branch → Pull Request (for external contributors)

1. **Fork** the repository by clicking the **Fork** button at the top-right of the GitHub page.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/afcfta-final-001.git
   cd afcfta-final-001
   ```
3. **Create a branch** for your changes:
   ```bash
   git checkout -b add-my-file
   ```
4. **Add and commit** your file:
   ```bash
   cp /path/to/your/file .
   git add your-file-name
   git commit -m "Add my new file"
   ```
5. **Push** to your fork:
   ```bash
   git push origin add-my-file
   ```
6. On GitHub, open a **Pull Request** from your branch to `main` in this repository.

---

## Questions?

If you have any trouble, please [open an issue](https://github.com/aouggad-web/afcfta-final-001/issues) and describe what you are trying to do.
