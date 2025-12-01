#!/usr/bin/env python3
"""
Add reciprocal relationships to markdown files.

If Person A lists Person B as their wife, this script ensures
Person B lists Person A as their husband (and vice versa).

Reciprocal mappings:
- parent ↔ child
- child ↔ parent
- wife ↔ husband
- husband ↔ wife
- sibling ↔ sibling

Additionally infers parent relationships from siblings:
- If A is parent of B and B is sibling of C, then A is parent of C
"""

import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set

PEOPLE_FOLDER = "People"

# Reciprocal relationship mappings
RECIPROCAL = {
    'parent': 'child',
    'child': 'parent',
    'wife': 'husband',
    'husband': 'wife',
    'sibling': 'sibling'  # Sibling is symmetric
}


def extract_frontmatter(content: str) -> tuple[str, Dict[str, List[str]], str]:
    """
    Extract frontmatter from markdown content.
    Returns: (frontmatter_text, relationships_dict, body_text)
    """
    frontmatter_match = re.match(r'^---\n(.*?)\n---\n?(.*)', content, re.DOTALL)
    if not frontmatter_match:
        return '', {}, content

    frontmatter = frontmatter_match.group(1)
    body = frontmatter_match.group(2)
    relationships = {}

    for rel_type in ['parent', 'child', 'wife', 'husband', 'sibling']:
        pattern = rf'^{rel_type}:\s*(.+)$'
        match = re.search(pattern, frontmatter, re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1).strip()
            names = re.findall(r'\[\[+([^\]]+)\]+', value)
            relationships[rel_type] = [name.strip() for name in names]

    return frontmatter, relationships, body


def build_relationship_graph() -> Dict[str, Dict[str, List[str]]]:
    """
    Build a complete graph of all relationships from all files.
    Returns: {person_name: {rel_type: [related_names]}}
    """
    graph = defaultdict(lambda: defaultdict(list))
    folder_path = Path(PEOPLE_FOLDER)

    for md_file in folder_path.glob("*.md"):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            name = md_file.stem
            _, relationships, _ = extract_frontmatter(content)

            for rel_type, related_names in relationships.items():
                graph[name][rel_type].extend(related_names)

        except Exception as e:
            print(f"⚠️  Error reading {md_file}: {e}")

    return graph


def compute_missing_reciprocals(graph: Dict) -> Dict[str, Dict[str, Set[str]]]:
    """
    Find missing reciprocal relationships.
    Returns: {person_name: {rel_type_to_add: {names_to_add}}}
    """
    missing = defaultdict(lambda: defaultdict(set))

    for person, relationships in list(graph.items()):
        for rel_type, related_people in relationships.items():
            reciprocal_type = RECIPROCAL.get(rel_type)
            if not reciprocal_type:
                continue

            for related_person in related_people:
                # Check if related_person has reciprocal relationship back to person
                if person not in graph[related_person].get(reciprocal_type, []):
                    # Missing reciprocal relationship!
                    missing[related_person][reciprocal_type].add(person)

    return missing


def infer_parent_relationships_from_siblings(graph: Dict) -> Dict[str, Dict[str, Set[str]]]:
    """
    Infer parent-child relationships from sibling relationships.

    If A is parent of B, and B is sibling of C, then A should be parent of C.

    Returns: {person_name: {rel_type_to_add: {names_to_add}}}
    """
    inferred = defaultdict(lambda: defaultdict(set))

    # For each person, find their siblings
    for person, relationships in graph.items():
        siblings = relationships.get('sibling', [])
        parents = relationships.get('parent', [])

        # For each sibling, ensure they share the same parents
        for sibling in siblings:
            # Get sibling's parents
            sibling_parents = graph[sibling].get('parent', [])

            # Add any missing parent relationships
            for parent in parents:
                if parent not in sibling_parents:
                    # Sibling is missing this parent
                    inferred[sibling]['parent'].add(parent)
                    # Parent is missing this child
                    inferred[parent]['child'].add(sibling)

            for parent in sibling_parents:
                if parent not in parents:
                    # Current person is missing this parent
                    inferred[person]['parent'].add(parent)
                    # Parent is missing this child
                    inferred[parent]['child'].add(person)

    return inferred


def format_relationship_line(rel_type: str, names: List[str]) -> str:
    """Format a relationship line for frontmatter."""
    if len(names) == 1:
        return f"{rel_type}: [[{names[0]}]]"
    else:
        formatted_names = ', '.join([f'[[{name}]]' for name in names])
        return f"{rel_type}: [{formatted_names}]"


def update_file_with_relationships(filepath: Path, new_relationships: Dict[str, Set[str]]):
    """Update a markdown file with new relationships."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    frontmatter_text, existing_rels, body = extract_frontmatter(content)

    # Merge new relationships with existing ones
    merged_rels = defaultdict(list)
    for rel_type, names in existing_rels.items():
        merged_rels[rel_type].extend(names)

    for rel_type, new_names in new_relationships.items():
        for name in new_names:
            if name not in merged_rels[rel_type]:
                merged_rels[rel_type].append(name)

    # Build new frontmatter
    new_frontmatter_lines = []
    for rel_type in ['parent', 'child', 'wife', 'husband', 'sibling']:
        if rel_type in merged_rels and merged_rels[rel_type]:
            line = format_relationship_line(rel_type, merged_rels[rel_type])
            new_frontmatter_lines.append(line)

    # Reconstruct file
    new_content = "---\n"
    new_content += "\n".join(new_frontmatter_lines)
    new_content += "\n---\n"
    new_content += body

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)


def main():
    """Main function."""
    print("🔄 Reciprocal Relationship Fixer + Sibling Inference")
    print("=" * 60)
    print()
    print("This script:")
    print("1. Adds missing reciprocal relationships")
    print("2. Adds sibling ↔ sibling reciprocals")
    print("3. Infers parent relationships from siblings")
    print()

    # Build relationship graph
    print("📖 Reading all markdown files...")
    graph = build_relationship_graph()
    print(f"✅ Found {len(graph)} people with relationships")
    print()

    # Find missing reciprocals
    print("🔍 Computing missing reciprocal relationships...")
    missing = compute_missing_reciprocals(graph)

    reciprocal_count = sum(len(names) for rels in missing.values() for names in rels.values())
    print(f"✅ Found {reciprocal_count} missing reciprocal relationships")
    print()

    # Infer parent relationships from siblings
    print("🧠 Inferring parent relationships from siblings...")
    inferred = infer_parent_relationships_from_siblings(graph)

    inferred_count = sum(len(names) for rels in inferred.values() for names in rels.values())
    print(f"✅ Found {inferred_count} inferred parent/child relationships")
    print()

    # Merge missing and inferred
    all_updates = defaultdict(lambda: defaultdict(set))
    for person, rels in missing.items():
        for rel_type, names in rels.items():
            all_updates[person][rel_type].update(names)

    for person, rels in inferred.items():
        for rel_type, names in rels.items():
            all_updates[person][rel_type].update(names)

    total_updates = sum(len(names) for rels in all_updates.values() for names in rels.values())

    if not all_updates:
        print("🎉 No missing relationships! All relationships are complete.")
        return

    print(f"📊 Total updates needed: {total_updates} relationships for {len(all_updates)} people")
    print()

    # Show summary
    print("📊 Sample updates (first 10):")
    print("-" * 60)
    for person, rels in sorted(all_updates.items())[:10]:
        for rel_type, names in rels.items():
            print(f"  {person} will get {rel_type}: {', '.join(sorted(names))}")

    if len(all_updates) > 10:
        print(f"  ... and {len(all_updates) - 10} more people")
    print()

    # Ask for confirmation
    response = input("Apply these changes? (y/n): ").strip().lower()

    if response != 'y':
        print("Aborted.")
        return

    # Apply updates
    print()
    print("✏️  Updating files...")
    updated_count = 0
    folder_path = Path(PEOPLE_FOLDER)

    for person, new_rels in all_updates.items():
        filepath = folder_path / f"{person}.md"
        if not filepath.exists():
            print(f"⚠️  Warning: {filepath} doesn't exist, skipping...")
            continue

        try:
            update_file_with_relationships(filepath, new_rels)
            updated_count += 1
            if updated_count <= 10:  # Show first 10
                print(f"  ✅ Updated: {person}")
        except Exception as e:
            print(f"❌ Error updating {person}: {e}")

    if updated_count > 10:
        print(f"  ... and {updated_count - 10} more")

    print()
    print(f"✨ Updated {updated_count} files!")
    print()
    print("Next steps:")
    print("  1. Review the changes: git diff People/")
    print("  2. Rebuild database: python3 scripts/build_database.py")
    print("  3. Re-diagnose: python3 scripts/diagnose_orphans.py")
    print("  4. Test: python3 -m http.server 8000 --directory docs")


if __name__ == "__main__":
    main()
