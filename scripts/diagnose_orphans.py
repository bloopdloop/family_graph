#!/usr/bin/env python3
"""
Diagnose orphaned nodes in the family graph.
Identifies people with no connections and potential naming mismatches.
"""

import sqlite3
import sys

DB_PATH = "docs/family_graph.db"


def find_orphaned_nodes(conn):
    """Find people with no relationships at all."""
    cursor = conn.cursor()

    query = """
    SELECT p.id, p.name
    FROM people p
    WHERE NOT EXISTS (
        SELECT 1 FROM relationships r
        WHERE r.from_id = p.id
    )
    AND p.id NOT IN (
        SELECT DISTINCT p2.id
        FROM people p2
        JOIN relationships r ON LOWER(r.to_name) = p2.name_lower
    )
    ORDER BY p.name
    """

    cursor.execute(query)
    return cursor.fetchall()


def find_people_with_only_outgoing(conn):
    """Find people who reference others but aren't referenced back."""
    cursor = conn.cursor()

    query = """
    SELECT p.id, p.name,
           COUNT(DISTINCT r.to_name) as references_count
    FROM people p
    JOIN relationships r ON r.from_id = p.id
    WHERE p.id NOT IN (
        SELECT DISTINCT p2.id
        FROM people p2
        JOIN relationships r2 ON LOWER(r2.to_name) = p2.name_lower
    )
    GROUP BY p.id, p.name
    ORDER BY p.name
    """

    cursor.execute(query)
    return cursor.fetchall()


def find_broken_references(conn):
    """Find relationships that reference non-existent people."""
    cursor = conn.cursor()

    query = """
    SELECT p.name as from_person,
           r.to_name,
           r.relationship_type
    FROM relationships r
    JOIN people p ON r.from_id = p.id
    WHERE NOT EXISTS (
        SELECT 1 FROM people p2
        WHERE LOWER(r.to_name) = p2.name_lower
    )
    ORDER BY p.name, r.to_name
    """

    cursor.execute(query)
    return cursor.fetchall()


def find_one_way_relationships(conn):
    """Find relationships that aren't reciprocated."""
    cursor = conn.cursor()

    # Find parent relationships without corresponding child
    query = """
    SELECT p1.name as person,
           r.to_name as parent_name,
           'parent->child missing' as issue
    FROM relationships r
    JOIN people p1 ON r.from_id = p1.id
    JOIN people p2 ON LOWER(r.to_name) = p2.name_lower
    WHERE r.relationship_type = 'parent'
    AND NOT EXISTS (
        SELECT 1 FROM relationships r2
        WHERE r2.from_id = p2.id
        AND r2.relationship_type = 'child'
        AND LOWER(r2.to_name) = p1.name_lower
    )

    UNION ALL

    SELECT p1.name as person,
           r.to_name as child_name,
           'child->parent missing' as issue
    FROM relationships r
    JOIN people p1 ON r.from_id = p1.id
    JOIN people p2 ON LOWER(r.to_name) = p2.name_lower
    WHERE r.relationship_type = 'child'
    AND NOT EXISTS (
        SELECT 1 FROM relationships r2
        WHERE r2.from_id = p2.id
        AND r2.relationship_type = 'parent'
        AND LOWER(r2.to_name) = p1.name_lower
    )

    ORDER BY person
    """

    cursor.execute(query)
    return cursor.fetchall()


def get_relationship_counts(conn):
    """Get relationship statistics."""
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM people")
    total_people = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(DISTINCT from_id) FROM relationships
    """)
    people_with_relationships = cursor.fetchone()[0]

    cursor.execute("""
        SELECT relationship_type, COUNT(*) as count
        FROM relationships
        GROUP BY relationship_type
    """)
    rel_counts = cursor.fetchall()

    return {
        'total_people': total_people,
        'people_with_relationships': people_with_relationships,
        'people_without_relationships': total_people - people_with_relationships,
        'relationship_counts': rel_counts
    }


def main():
    """Main diagnostic function."""
    print("🔍 Family Graph Orphan Diagnostic Tool")
    print("=" * 50)
    print()

    try:
        conn = sqlite3.connect(DB_PATH)
    except Exception as e:
        print(f"❌ Error: Could not open database: {e}")
        sys.exit(1)

    # Get statistics
    print("📊 Overall Statistics:")
    print("-" * 50)
    stats = get_relationship_counts(conn)
    print(f"Total people: {stats['total_people']}")
    print(f"People with relationships: {stats['people_with_relationships']}")
    print(f"People without relationships: {stats['people_without_relationships']}")
    print()
    print("Relationship counts:")
    for rel_type, count in stats['relationship_counts']:
        print(f"  - {rel_type}: {count}")
    print()

    # Find completely orphaned nodes
    print("🚨 Completely Orphaned Nodes (no connections at all):")
    print("-" * 50)
    orphans = find_orphaned_nodes(conn)
    if orphans:
        for person_id, name in orphans:
            print(f"  - {name} (ID: {person_id})")
        print(f"\nTotal: {len(orphans)} orphans")
    else:
        print("  ✅ No completely orphaned nodes found!")
    print()

    # Find people with only outgoing relationships
    print("⚠️  People with Only Outgoing References:")
    print("-" * 50)
    print("(These reference others but aren't referenced back)")
    one_way = find_people_with_only_outgoing(conn)
    if one_way:
        for person_id, name, ref_count in one_way:
            print(f"  - {name} → references {ref_count} people")
        print(f"\nTotal: {len(one_way)} people")
    else:
        print("  ✅ All people are referenced by others!")
    print()

    # Find broken references
    print("💔 Broken References (pointing to non-existent people):")
    print("-" * 50)
    broken = find_broken_references(conn)
    if broken:
        for from_person, to_name, rel_type in broken:
            print(f"  - {from_person} → {rel_type} → '{to_name}' (NOT FOUND)")
        print(f"\nTotal: {len(broken)} broken references")
        print("\n💡 Tip: Check for typos in markdown frontmatter!")
    else:
        print("  ✅ All references point to existing people!")
    print()

    # Find one-way relationships
    print("🔄 One-Way Relationships (not reciprocated):")
    print("-" * 50)
    one_way_rels = find_one_way_relationships(conn)
    if one_way_rels:
        for person, other, issue in one_way_rels[:20]:  # Limit to first 20
            print(f"  - {person} → {other}: {issue}")
        if len(one_way_rels) > 20:
            print(f"  ... and {len(one_way_rels) - 20} more")
        print(f"\nTotal: {len(one_way_rels)} one-way relationships")
    else:
        print("  ✅ All relationships are reciprocated!")
    print()

    conn.close()

    # Summary
    print("=" * 50)
    print("📝 Summary:")
    if orphans or broken:
        print("❌ Issues found! See details above.")
        if broken:
            print("\n🔧 Recommended fixes:")
            print("  1. Check markdown files for spelling errors in frontmatter")
            print("  2. Ensure names match filenames exactly")
            print("  3. Run: python3 scripts/build_database.py")
    else:
        print("✅ No critical issues found!")
        if one_way_rels:
            print("⚠️  Some one-way relationships exist (may be intentional)")


if __name__ == "__main__":
    main()
