# 🚀 Family Graph - Quick Deployment Guide (SQLite Version)

## What You Got

A complete family tree visualization website with **SQLite backend** that:
- ✅ Works with **private repositories** (no GitHub API!)
- ✅ Auto-builds database via GitHub Actions
- ✅ Loads fast (~88KB single file)
- ✅ Protects privacy with obfuscated names + spouse authentication
- ✅ Shows beautiful interactive graph with color-coded relationships
- ✅ Deploys to GitHub Pages (free hosting)

## Files Created

```
.github/workflows/
└── build-database.yml      # Auto-builds database on push

scripts/
└── build_database.py       # Python script to generate SQLite DB

docs/
├── index.html              # Main website page
├── app.js                  # All the logic (loads DB, auth, graph)
├── styles.css              # Styling
├── family_graph.db         # Generated database (auto-created)
└── README.md               # Full documentation
```

## ⚡ Quick Start (4 Steps)

### Step 1: Test Database Generation Locally

```bash
# Generate the database
python3 scripts/build_database.py

# Verify it was created
ls -lh docs/family_graph.db

# Should show: ~88KB file
```

### Step 2: Test the Website Locally

```bash
# Start a local web server
python3 -m http.server 8000 --directory docs

# Open http://localhost:8000 in your browser
# Login with any spouse pair from your data
```

### Step 3: Commit and Push Everything

```bash
git add .github/ scripts/ docs/ DEPLOYMENT_GUIDE.md
git commit -m "Add SQLite-based family graph visualization"
git push origin main
```

### Step 4: Enable GitHub Pages

1. Go to: `https://github.com/YOUR_USERNAME/family_graph/settings/pages`
2. Under "Source" → select **main** branch
3. Select folder: **/docs**
4. Click **Save**

Wait 1-2 minutes, then visit:
```
https://YOUR_USERNAME.github.io/family_graph/
```

## 🤖 GitHub Actions Setup

The workflow (`.github/workflows/build-database.yml`) will:
- Trigger automatically when you push changes to `People/` folder
- Run the Python script to rebuild the database
- Commit the updated `docs/family_graph.db` back to your repo

**Verify it works:**
1. Make a small change to any file in `People/`
2. Commit and push
3. Go to Actions tab on GitHub
4. Watch the "Build Family Graph Database" workflow run
5. Database will be auto-updated!

## 🎨 How to Use the Website

1. **Load the site** - Database loads automatically (fast!)
2. **Login** - Enter your name + one of your parent's names
3. **Explore** - Interactive graph shows family connections
4. **Privacy** - Only names within N levels are revealed

### Example Login:
- **Your Name:** `Amit Bhatia`
- **Parent's Name:** `Prakash Bhatia`

(Use real names from your `People/` folder)

## ⚙️ Configuration

Edit `docs/app.js` lines 2-4:

```javascript
const CONFIG = {
    DATABASE_URL: 'family_graph.db',
    REVEAL_DEPTH: 2,  // ← Change this!
};
```

### Reveal Depth Examples:
- `REVEAL_DEPTH: 0` → Only authenticated person visible
- `REVEAL_DEPTH: 1` → + parents, children, spouse, siblings
- `REVEAL_DEPTH: 2` → + grandparents, grandchildren (default)
- `REVEAL_DEPTH: 3` → Great-grandparents, etc.

### Admin Access

Edit `docs/app.js` line 5:

```javascript
const CONFIG = {
    DATABASE_URL: 'family_graph.db',
    REVEAL_DEPTH: 2,
    ADMIN_PASSWORD: 'family2024',  // ← CHANGE THIS!
};
```

**To login as admin:**
- Your Name: `admin`
- Parent's Name: `[your admin password]`

Admin mode shows **all 140 names** at once with orange-colored nodes.

**⚠️ Important:** Change the default admin password before deploying!

## 🎨 Relationship Colors

- **Blue** (solid) → Parent-Child
- **Red** (dashed) → Spouse
- **Green** (dashed) → Sibling

## 🔒 Privacy & Security

- Names are obfuscated as `person_123456`
- Repository can be **private** (no API tokens needed!)
- Only authenticated users see real names
- All data processing happens in the browser
- No server, no tracking, no data collection

## 🆘 Troubleshooting

### "Failed to load database: 404"
→ Database hasn't been generated yet. Run `python3 scripts/build_database.py` and commit.

### "Person not found in family tree"
→ Name spelling must match the markdown filename exactly (case-insensitive)

### GitHub Actions not running?
→ Check Actions tab for errors. Workflow only triggers on changes to `People/**` or `scripts/build_database.py`

### Graph won't load locally?
→ Use a web server: `python3 -m http.server 8000 --directory docs`
→ Don't open `file:///` directly (CORS issues with SQL.js)

## 🧪 Local Commands

```bash
# Build database
python3 scripts/build_database.py

# Test website
python3 -m http.server 8000 --directory docs

# Inspect database
sqlite3 docs/family_graph.db "SELECT * FROM people LIMIT 5;"

# Count records
sqlite3 docs/family_graph.db "SELECT COUNT(*) FROM people;"
```

## 🏗️ Architecture

```
Your Markdown Files (People/*.md)
         ↓
Python Script (scripts/build_database.py)
         ↓
SQLite Database (docs/family_graph.db)
         ↓
SQL.js (in browser) loads database
         ↓
JavaScript parses data & renders graph
         ↓
User authenticates → names revealed!
```

## 🎯 Key Advantages

| Feature | This (SQLite) | Old (GitHub API) |
|---------|--------------|------------------|
| **Private repos** | ✅ Yes | ❌ No |
| **Rate limits** | ✅ None | ⚠️ 60/hour |
| **Load speed** | ✅ Fast (1 file, 88KB) | ⚠️ Slow (140 API calls) |
| **Complexity** | ✅ Simple | ⚠️ Token management |
| **Offline** | ✅ Works | ❌ No |

## 🔐 Future: Database Encryption (Optional)

The Python script has a placeholder for encrypting the database. To add:

1. Install `cryptography` library
2. Set `FAMILY_GRAPH_KEY` in GitHub Secrets
3. Implement AES-256 encryption in `scripts/build_database.py`
4. Add decryption logic in `docs/app.js`

This would fully encrypt the database file, requiring a password in the browser.

## 🎯 Next Steps

After deploying:

1. ✅ Test the website works
2. ✅ Try logging in with different family members
3. ✅ Adjust `REVEAL_DEPTH` to your preference
4. ✅ Make a change to `People/` and watch GitHub Actions rebuild the DB!
5. ✅ Share the URL with family!

## 📝 Notes

- **Private repo OK** - No GitHub API tokens needed!
- **Auto-updates** - Just push changes to `People/`, database rebuilds automatically
- **Fast loading** - Single 88KB file vs 140+ API requests
- **Free hosting** - GitHub Pages costs $0
- **No build tools locally** - Just HTML/CSS/JS (unless you want to rebuild DB)

## 📚 Full Documentation

See `docs/README.md` for complete documentation including:
- Detailed architecture
- Database schema
- Troubleshooting guide
- Customization options
- Encryption setup

---

**Questions?** Check the browser console (F12) for detailed error messages!

**Enjoy your private, fast, interactive family tree! 🌳✨**
