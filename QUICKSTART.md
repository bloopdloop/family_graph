# 🎯 Family Graph - Quickstart (30 seconds)

## Test Locally Right Now:

```bash
# 1. Start web server
cd /path/to/family_graph
python3 -m http.server 8000 --directory docs

# OR use the convenience script:
./scripts/serve.sh

# 2. Open browser to: http://localhost:8000
#    ⚠️  IMPORTANT: Don't open file:/// directly!
#    Must use http://localhost:8000

# 3. Login with example credentials:
   Your Name: Amit Bhatia
   Parent's Name: Prakash Bhatia

# Or use admin mode to see everything:
   Your Name: admin
   Parent's Name: family2024
```

## ⚠️ Common Mistake:

**Don't** double-click `docs/index.html` - browsers block loading database from `file:///` URLs

**Do** use a web server: `python3 -m http.server 8000 --directory docs`

This is only for local testing - GitHub Pages works fine without this!

## Deploy to GitHub Pages:

```bash
# 1. Commit everything
git add .
git commit -m "Add SQLite family graph visualization"
git push

# 2. Enable GitHub Pages
# Go to: Settings → Pages → Source: main branch, /docs folder

# 3. Visit your site:
# https://YOUR_USERNAME.github.io/family_graph/
```

## Files You Got:

- ✅ **Python builder** (`scripts/build_database.py`) - Parses markdown → SQLite
- ✅ **GitHub Actions** (`.github/workflows/build-database.yml`) - Auto-rebuilds DB
- ✅ **Website** (`docs/`) - HTML/JS/CSS that loads and visualizes the graph
- ✅ **Database** (`docs/family_graph.db`) - 88KB SQLite file with 140 people

## Key Features:

- 🔒 **Private repo compatible** (no GitHub API needed!)
- ⚡ **Fast loading** (single 88KB file)
- 🤖 **Auto-updates** (GitHub Actions rebuilds on every push to People/)
- 🎨 **Interactive graph** (zoom, pan, color-coded relationships)
- 🔐 **Privacy** (names obfuscated until spouse authentication)

## Configuration:

Edit `docs/app.js` line 3:
```javascript
REVEAL_DEPTH: 2,  // 0=only you, 1=immediate family, 2=grandparents, 3+=extended
```

## Need Help?

- 📖 **Full guide:** `DEPLOYMENT_GUIDE.md`
- 📚 **Technical docs:** `docs/README.md`
- 🐛 **Errors?** Check browser console (F12)

---

**That's it! Enjoy your family tree! 🌳**
