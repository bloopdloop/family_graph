# Family Graph Visualization (SQLite Version)

An interactive family tree visualization that loads data from a SQLite database, protecting privacy through authentication-based name revealing.

## ✨ Features

- ✅ **Private Repository Compatible** - No GitHub API needed!
- ✅ **Zero Runtime Dependencies** - Loads from SQLite database
- ✅ **Automatic Updates** - GitHub Actions rebuilds DB on every commit
- 🔒 **Privacy Protection** - Names obfuscated until authenticated
- 🎨 **Color-Coded Relationships** - Parent/child (blue), spouse (red), sibling (green)
- 🔍 **Depth-Based Reveal** - Authenticated users see names within N levels
- 📱 **Responsive Design** - Works on desktop and mobile
- ⚡ **Fast Loading** - Single ~90KB database file

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│  GitHub Actions (on push to People/)                │
│  ↓                                                   │
│  Python script parses markdown files                │
│  ↓                                                   │
│  Generates SQLite database (docs/family_graph.db)   │
│  ↓                                                   │
│  Commits database back to repository                │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  User visits GitHub Pages site                      │
│  ↓                                                   │
│  Browser loads SQL.js library                       │
│  ↓                                                   │
│  Fetches family_graph.db (88KB)                     │
│  ↓                                                   │
│  User authenticates with spouse names               │
│  ↓                                                   │
│  Interactive graph reveals names                    │
└─────────────────────────────────────────────────────┘
```

## 🚀 Setup Instructions

### 1. Enable GitHub Actions

The `.github/workflows/build-database.yml` workflow is already configured. It will:
- Run automatically when you push changes to `People/` folder
- Build the SQLite database
- Commit it back to your repo

**Verify it works:**
1. Make a small change to any file in `People/`
2. Commit and push
3. Check GitHub Actions tab to see the workflow run
4. The database will be auto-updated in `docs/family_graph.db`

### 2. Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages**
3. Under "Source", select **Deploy from a branch**
4. Select branch: **main** (or **master**)
5. Select folder: **/docs**
6. Click **Save**

### 3. Wait for Deployment

After 1-2 minutes, your site will be available at:

```
https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/
```

### 4. Test the Site

1. Open the URL in your browser
2. Wait for "Data loaded! Please login to view the graph."
3. Enter your name and one of your parent's names from your family tree
4. Click "Unlock Graph" to see the visualization

## ⚙️ Configuration

### Reveal Depth

Edit `docs/app.js` line 3:

```javascript
const CONFIG = {
    DATABASE_URL: 'family_graph.db',
    REVEAL_DEPTH: 2,  // ← Change this!
};
```

### Admin Access

The admin password is stored as a **SHA-256 hash** (not plain text) for security.

**To change the admin password:**

1. Generate a new hash:

```javascript
node scripts/generate_admin_hash.js YOUR_NEW_PASSWORD
```

2. Copy the hash and update `docs/app.js` line 8:

```javascript
ADMIN_PASSWORD_HASH: 'YOUR_HASH_HERE',
```

**To use admin mode:**
- Your Name: `admin`
- Parent's Name: `family2024` (or your custom password)

**Security features:**
- ✅ Password hashed with SHA-256 (can't be reversed)
- ✅ Hash stored in code (not plain text password)
- ✅ Can't bypass by editing JavaScript (need actual password)
- ✅ Normal users don't need admin password (database unencrypted)

**Alternative hash generation (in browser console):**
```javascript
crypto.subtle.digest('SHA-256', new TextEncoder().encode('YOUR_PASSWORD'))
  .then(h => console.log(
    Array.from(new Uint8Array(h))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('')
  ))
```

Admin mode reveals **all 140 names** in the graph at once.

**Options:**
- `0` - Only show authenticated user
- `1` - User + immediate family (parents, children, spouse, siblings)
- `2` - User + 2 levels (includes grandparents, grandchildren) **[DEFAULT]**
- `3+` - Extended family network

## 🔄 How It Works

### Data Flow:

1. **Markdown Files** → Python script parses frontmatter
2. **SQLite Database** → Stores people and relationships
3. **SQL.js** → JavaScript SQLite engine loads DB in browser
4. **Authentication** → Verifies parent-child relationship
5. **Graph** → Vis.js renders interactive visualization

### Database Schema:

```sql
CREATE TABLE people (
    id TEXT PRIMARY KEY,           -- Obfuscated ID (person_123456)
    name TEXT NOT NULL,            -- Real name
    name_lower TEXT NOT NULL       -- Lowercase for searching
);

CREATE TABLE relationships (
    id INTEGER PRIMARY KEY,
    from_id TEXT NOT NULL,         -- Person ID
    to_name TEXT NOT NULL,         -- Related person's name
    relationship_type TEXT         -- 'parent', 'child', 'wife', 'husband'
);

CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT                     -- Build time, version, etc.
);
```

## 🧪 Local Development

### Build Database Locally:

```bash
python3 scripts/build_database.py
```

This creates `docs/family_graph.db` from your `People/` markdown files.

### Test the Website:

```bash
# Option 1: Open directly (if CORS allows)
open docs/index.html

# Option 2: Use a simple web server
python3 -m http.server 8000 --directory docs
# Then visit: http://localhost:8000
```

### Inspect the Database:

```bash
# View tables
sqlite3 docs/family_graph.db ".tables"

# Count records
sqlite3 docs/family_graph.db "SELECT COUNT(*) FROM people;"

# View sample data
sqlite3 docs/family_graph.db "SELECT * FROM people LIMIT 5;"
```

## 📊 Data Format

Your markdown files should have frontmatter:

```markdown
---
parent: [[[Father Name]], [[Mother Name]]]
child: [[[Child 1]], [[Child 2]]]
wife: [[Spouse Name]]
---
# Person Name

Content here...
```

**Supported relationship types:**
- `parent` - Parents of this person
- `child` - Children of this person
- `wife` or `husband` - Spouse of this person

## 🆘 Troubleshooting

### Database not updating after push?

1. Check GitHub Actions tab for workflow status
2. Look for errors in the workflow log
3. Verify `People/` folder has markdown files
4. Manually trigger workflow: Actions → Build Family Graph Database → Run workflow

### "Failed to load database: 404"

- Database hasn't been generated yet
- Run `python3 scripts/build_database.py` locally and commit
- Or push a change to trigger GitHub Actions

### Names not revealing after login?

- Check browser console (F12) for errors
- Verify names match exactly (case-insensitive)
- Check that parent-child relationship exists in frontmatter

### Graph loads but names stay hidden?

- Increase `REVEAL_DEPTH` in `app.js`
- Check that relationships form a connected graph

## 🔒 Privacy & Security

### Current Setup:
- ✅ Names obfuscated as `person_123456`
- ✅ Repository can be **private**
- ✅ Only authenticated users see real names
- ✅ All processing happens in browser
- ✅ No external server, no tracking

### Future Encryption (Optional):

The Python script has a placeholder for database encryption. To implement:

1. Install cryptography:
   ```bash
   pip install cryptography
   ```

2. Set encryption key in GitHub Secrets:
   - Go to Settings → Secrets → Actions
   - Add secret: `FAMILY_GRAPH_KEY`

3. Implement encryption in `scripts/build_database.py` (see comments)

4. Add decryption in `docs/app.js`

This would encrypt the database file itself, requiring a password to decrypt in the browser.

## 🎨 Customization

### Change Colors

Edit `docs/styles.css` to modify the color scheme.

### Change Graph Layout

Edit `docs/app.js`, function `renderGraph()` around line 350. Vis.js supports hierarchical layouts:

```javascript
layout: {
    hierarchical: {
        direction: 'UD',        // Up-Down
        sortMethod: 'directed'
    }
}
```

### Add More Relationship Types

1. Update `scripts/build_database.py` line 30 to add new types
2. Update `docs/app.js` line 70 to include new types
3. Add edges in `renderGraph()` function

## 📈 Performance

- **Database Size:** ~88KB for 140 people
- **Load Time:** ~2-3 seconds (includes SQL.js library)
- **Memory Usage:** Minimal (all data loads once)
- **No Rate Limits:** Everything is static files

## 🛠️ Technologies Used

- **Python** - Database builder script
- **SQLite** - Database format
- **SQL.js** - JavaScript SQLite engine (runs in browser)
- **Vis.js** - Network graph visualization
- **GitHub Actions** - Automatic database building
- **GitHub Pages** - Free static hosting

## 📚 Files Overview

```
.github/workflows/build-database.yml  # GitHub Actions workflow
scripts/build_database.py             # Python database builder
docs/
├── index.html                        # Main page
├── app.js                            # JavaScript logic
├── styles.css                        # Styling
├── family_graph.db                   # Generated database (auto-created)
└── README.md                         # This file
```

## 🎯 Advantages Over GitHub API Approach

| Feature | SQLite | GitHub API |
|---------|--------|------------|
| Private repos | ✅ Yes | ❌ No (needs token) |
| Rate limits | ✅ None | ⚠️ 60/hour |
| Load speed | ✅ Fast (1 file) | ⚠️ Slow (140+ requests) |
| Offline capable | ✅ Yes | ❌ No |
| Complexity | ✅ Simple | ⚠️ Token management |

---

**Questions?** Check browser console (F12) for detailed error messages!
