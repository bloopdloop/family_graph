#!/usr/bin/env python3
"""
Helper script to fix orphaned nodes by creating stub files for missing people.
"""

import sqlite3
import os
from pathlib import Path

DB_PATH = "docs/family_graph.db"
PEOPLE_FOLDER = "People"


def get_broken_references(conn):
    """Get all broken references."""
    cursor = conn.cursor()

    query = """
    SELECT DISTINCT r.to_name
    FROM relationships r
    WHERE NOT EXISTS (
        SELECT 1 FROM people p2
        WHERE LOWER(r.to_name) = p2.name_lower
    )
    ORDER BY r.to_name
    """

    cursor.execute(query)
    return [row[0] for row in cursor.fetchall()]


def create_stub_file(name, folder):
    """Create a stub markdown file for a missing person."""
    filepath = Path(folder) / f"{name}.md"

    if filepath.exists():
        return False

    content = f"""---
# TODO: Add relationships for {name}
---
# {name}
#people

### Photo

### About Me
- Born on
- Died on
- Location
- Maiden Name
- Nickname
- Gender
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return True


def main():
    """Main function."""
    print("🔧 Orphan Fixer Tool")
    print("=" * 50)
    print()

    # Load database
    try:
        conn = sqlite3.connect(DB_PATH)
    except Exception as e:
        print(f"❌ Error: Could not open database: {e}")
        return

    # Get broken references
    broken = get_broken_references(conn)
    conn.close()

    print(f"Found {len(broken)} missing people referenced in relationships")
    print()

    # Ask user what to do
    print("Options:")
    print("  1. Create stub files for ALL missing people")
    print("  2. Show list and let me decide")
    print("  3. Exit")
    print()

    choice = input("Choose (1/2/3): ").strip()

    if choice == "1":
        print()
        print("Creating stub files...")
        created = 0
        for name in broken:
            if create_stub_file(name, PEOPLE_FOLDER):
                print(f"  ✅ Created: {name}.md")
                created += 1

        print()
        print(f"✨ Created {created} stub files")
        print()
        print("Next steps:")
        print("  1. Edit the new files to add proper frontmatter")
        print("  2. Run: python3 scripts/build_database.py")
        print("  3. Run: python3 scripts/diagnose_orphans.py")

    elif choice == "2":
        print()
        print("Missing people (referenced but no file exists):")
        print("-" * 50)
        for i, name in enumerate(broken, 1):
            print(f"{i:3}. {name}")
        print()
        print(f"Total: {len(broken)} missing people")
        print()
        print("To create files manually:")
        print("  touch 'People/NAME.md'")

    else:
        print("Exiting...")


if __name__ == "__main__":
    main()
