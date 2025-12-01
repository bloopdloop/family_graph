#!/usr/bin/env python3
"""
Check database consistency and report orphaned relationships.
Run this after building the database to ensure all relationships point to valid people.
"""

import sqlite3
import sys
from pathlib import Path

# Configuration
DB_PATH = "../docs/family_graph.db"


def check_orphaned_relationships(db_path: str) -> bool:
    """Check for relationships pointing to non-existent people."""
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Find orphaned relationship targets (excluding aliases)
    cursor.execute("""
        SELECT DISTINCT r.to_name, r.relationship_type, COUNT(*) as ref_count
        FROM relationships r
        LEFT JOIN people p ON r.to_name = p.name
        WHERE p.name IS NULL AND r.relationship_type != 'alias'
        GROUP BY r.to_name, r.relationship_type
        ORDER BY ref_count DESC
    """)

    orphans = cursor.fetchall()

    if orphans:
        print("⚠️  Found orphaned relationship targets:")
        print("   (These relationships point to people that don't have their own files)\n")
        for name, rel_type, count in orphans:
            print(f"  - '{name}' ({rel_type}, {count} reference{'s' if count > 1 else ''})")
        conn.close()
        return False

    # Check for duplicate people (same name, different IDs)
    cursor.execute("""
        SELECT name, COUNT(*) as count
        FROM people
        GROUP BY name_lower
        HAVING count > 1
        ORDER BY count DESC
    """)

    duplicates = cursor.fetchall()

    if duplicates:
        print("⚠️  Found duplicate people entries:")
        for name, count in duplicates:
            cursor.execute("SELECT id, name FROM people WHERE name_lower = ?", (name.lower(),))
            entries = cursor.fetchall()
            print(f"\n  '{name}' appears {count} times:")
            for person_id, person_name in entries:
                print(f"    - {person_name} (ID: {person_id})")
        conn.close()
        return False

    conn.close()
    print("✅ Database consistency check passed!")
    print("   - All relationships point to valid people")
    print("   - No duplicate entries found")
    return True


def get_database_stats(db_path: str):
    """Print database statistics."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM people")
    people_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM relationships WHERE relationship_type != 'alias'")
    rel_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM relationships WHERE relationship_type = 'alias'")
    alias_count = cursor.fetchone()[0]

    print(f"\n📊 Database Statistics:")
    print(f"   - {people_count} people")
    print(f"   - {rel_count} relationships")
    print(f"   - {alias_count} aliases")

    conn.close()


def main():
    """Main function."""
    print("🔍 Checking family graph database consistency...\n")

    is_valid = check_orphaned_relationships(DB_PATH)
    get_database_stats(DB_PATH)

    if not is_valid:
        print("\n💡 Tip: Run 'python scripts/build_database.py' to rebuild the database")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
