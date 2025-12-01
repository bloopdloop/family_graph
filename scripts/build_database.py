#!/usr/bin/env python3
"""
Build SQLite database from markdown files in People/ folder.
This script is run by GitHub Actions to generate the family graph database.
"""

import os
import re
import sqlite3
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from difflib import get_close_matches

# Configuration
PEOPLE_FOLDER = "People"
OUTPUT_DB = "docs/family_graph.db"
ENCRYPTION_KEY = os.environ.get("FAMILY_GRAPH_KEY", "")  # Optional encryption key


def extract_frontmatter(content: str) -> Dict[str, List[str]]:
    """Extract frontmatter from markdown content."""
    frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not frontmatter_match:
        return {}

    frontmatter = frontmatter_match.group(1)
    relationships = {}

    for rel_type in ['parent', 'child', 'wife', 'husband', 'alias']:
        pattern = rf'{rel_type}:\s*(.+)'
        match = re.search(pattern, frontmatter, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            # Handle alias format: [Name1, Name2] vs other formats: [[Name]]
            if rel_type == 'alias':
                # Aliases use simple list format: [Name1, Name2]
                value = value.strip('[]')
                names = [n.strip() for n in value.split(',')]
                relationships[rel_type] = names
                continue
            # Extract names from [[Name]] or [[[Name]]] format
            names = re.findall(r'\[\[+([^\]]+)\]+', value)
            relationships[rel_type] = [name.strip() for name in names]

    return relationships


def generate_person_id(name: str) -> str:
    """Generate consistent obfuscated ID from name."""
    hash_val = 0
    for char in name:
        hash_val = ((hash_val << 5) - hash_val) + ord(char)
        hash_val = hash_val & 0xFFFFFFFF  # Keep as 32-bit

    return f"person_{abs(hash_val)}"


def create_database(db_path: str):
    """Create SQLite database with schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create people table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS people (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            name_lower TEXT NOT NULL
        )
    ''')

    # Create relationships table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id TEXT NOT NULL,
            to_name TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            FOREIGN KEY (from_id) REFERENCES people(id)
        )
    ''')

    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_name_lower ON people(name_lower)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_from_id ON relationships(from_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rel_type ON relationships(relationship_type)')

    conn.commit()
    return conn


def parse_markdown_files(folder: str) -> List[Dict]:
    """Parse all markdown files and extract person data."""
    people = []
    folder_path = Path(folder)

    if not folder_path.exists():
        print(f"Error: {folder} directory not found!")
        return people

    for md_file in folder_path.glob("*.md"):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            name = md_file.stem  # Filename without .md
            relationships = extract_frontmatter(content)
            person_id = generate_person_id(name)

            people.append({
                'id': person_id,
                'name': name,
                'relationships': relationships
            })

        except Exception as e:
            print(f"Error parsing {md_file}: {e}")

    return people


def validate_and_resolve_relationships(people: List[Dict]) -> tuple[List[Dict], List[str]]:
    """Validate relationships and resolve names using fuzzy matching."""
    valid_names = {p['name'] for p in people}
    valid_names_lower = {name.lower(): name for name in valid_names}
    warnings = []

    for person in people:
        for rel_type, names in person['relationships'].items():
            if rel_type == 'alias':  # Skip aliases - they're not people
                continue

            resolved_names = []
            for name in names:
                if name in valid_names:
                    resolved_names.append(name)
                    continue

                # Try case-insensitive exact match
                if name.lower() in valid_names_lower:
                    correct_name = valid_names_lower[name.lower()]
                    warnings.append(f"⚠️  '{person['name']}' → {rel_type} → '{name}' (case mismatch, using '{correct_name}')")
                    resolved_names.append(correct_name)
                    continue

                # Try fuzzy match
                matches = get_close_matches(name, valid_names, n=1, cutoff=0.85)
                if matches:
                    warnings.append(f"⚠️  '{person['name']}' → {rel_type} → '{name}' (fuzzy matched to '{matches[0]}')")
                    resolved_names.append(matches[0])
                else:
                    warnings.append(f"❌ '{person['name']}' → {rel_type} → '{name}' (NOT FOUND - relationship will be orphaned)")
                    resolved_names.append(name)  # Keep for now but warn

            person['relationships'][rel_type] = resolved_names

    return people, warnings


def insert_data(conn: sqlite3.Connection, people: List[Dict]):
    """Insert people and relationships into database."""
    cursor = conn.cursor()

    # Insert people
    for person in people:
        cursor.execute(
            'INSERT OR REPLACE INTO people (id, name, name_lower) VALUES (?, ?, ?)',
            (person['id'], person['name'], person['name'].lower())
        )

    # Insert relationships
    for person in people:
        person_id = person['id']
        relationships = person['relationships']

        for rel_type, names in relationships.items():
            for name in names:
                # Skip empty names
                if not name or not name.strip():
                    continue
                cursor.execute(
                    'INSERT INTO relationships (from_id, to_name, relationship_type) VALUES (?, ?, ?)',
                    (person_id, name, rel_type)
                )

    conn.commit()
    print(f"✅ Inserted {len(people)} people into database")


def add_metadata(conn: sqlite3.Connection):
    """Add metadata table with build info."""
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    import datetime
    build_time = datetime.datetime.utcnow().isoformat()

    cursor.execute('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)',
                   ('build_time', build_time))
    cursor.execute('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)',
                   ('version', '1.0'))
    cursor.execute('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)',
                   ('encrypted', 'false'))

    conn.commit()


def encrypt_database(db_path: str, key: str):
    """Encrypt the database file using AES-256 (placeholder for now)."""
    # For now, this is a placeholder
    # Real encryption would use cryptography library
    # For simple obfuscation, we could XOR the bytes
    print("⚠️  Database encryption not implemented yet")
    print("    To add encryption, install: pip install cryptography")
    print("    And implement AES-256 encryption here")


def main():
    """Main function to build the database."""
    print("🚀 Building family graph database...")

    # Parse markdown files
    print(f"📖 Parsing markdown files from {PEOPLE_FOLDER}/")
    people = parse_markdown_files(PEOPLE_FOLDER)

    if not people:
        print("❌ No people found! Check that People/ folder exists and contains .md files")
        return

    print(f"✅ Found {len(people)} people")

    # Create output directory if needed
    # Validate and resolve relationships
    print("🔍 Validating relationships...")
    people, warnings = validate_and_resolve_relationships(people)

    if warnings:
        print(f"⚠️  Found {len(warnings)} relationship issues:")
        for warning in warnings[:10]:  # Show first 10
            print(f"   {warning}")
        if len(warnings) > 10:
            print(f"   ... and {len(warnings) - 10} more warnings")

    # Create output directory if needed
    os.makedirs(os.path.dirname(OUTPUT_DB), exist_ok=True)

    # Create database
    print(f"📦 Creating database: {OUTPUT_DB}")
    conn = create_database(OUTPUT_DB)

    # Insert data
    insert_data(conn, people)

    # Add metadata
    add_metadata(conn)

    # Close connection
    conn.close()

    # Check file size
    file_size = os.path.getsize(OUTPUT_DB)
    print(f"✅ Database created: {file_size:,} bytes")

    # Optional encryption
    if ENCRYPTION_KEY:
        print("🔒 Encrypting database...")
        encrypt_database(OUTPUT_DB, ENCRYPTION_KEY)

    print("✨ Done!")


if __name__ == "__main__":
    main()
