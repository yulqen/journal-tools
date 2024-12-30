import sqlite3
import argparse
from datetime import datetime
import sys
import uuid

DB_PATH = "/home/lemon/Documents/Notes/journal/datasette-journal/journal.db"

def add_entry(entry_text, entry_type):
    """Add a new entry to the journal"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    entry_id = str(uuid.uuid4())
    current_time = datetime.now().isoformat()

    cursor.execute(
        'INSERT INTO journal_entries (id, entry, type, date_added, date_updated) VALUES (?, ?, ?, ?, ?)',
        (entry_id, entry_text, entry_type, current_time, current_time)
    )

    conn.commit()
    conn.close()

def add_meeting_entry(entry_text, meeting_id):
    """Add a new entry to the journal with a meeting ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # First, verify that the meeting_id exists
    cursor.execute('SELECT id FROM meetings WHERE id = ?', (meeting_id,))
    if not cursor.fetchone():
        print(f"Error: Meeting ID {meeting_id} does not exist")
        conn.close()
        sys.exit(1)

    entry_id = str(uuid.uuid4())
    current_time = datetime.now().isoformat()

    cursor.execute(
        'INSERT INTO journal_entries (id, entry, date_added, date_updated, meeting_id) VALUES (?, ?, ?, ?, ?)',
        (entry_id, entry_text, current_time, current_time, meeting_id)
    )

    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description='Journal Entry CLI Tool')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command')

    # Regular entry parser
    entry_parser = subparsers.add_parser('add', help='Add a regular journal entry')
    type_group = entry_parser.add_mutually_exclusive_group()
    type_group.add_argument('--work', action='store_true', help='Work entry (type 1)')
    type_group.add_argument('--personal', action='store_true', help='Personal entry (type 2)')
    type_group.add_argument('--jobby', action='store_true', help='Jobby entry (type 3)')
    type_group.add_argument('--sleep', action='store_true', help='Sleep entry (type 4)')
    entry_parser.add_argument('entry', nargs='*', help='The journal entry text')

    # Meeting entry parser
    meeting_parser = subparsers.add_parser('meeting-note', help='Add a journal entry with meeting ID')
    meeting_parser.add_argument('entry', nargs='*', help='The journal entry text')
    meeting_parser.add_argument('--meeting', required=True, help='Meeting ID to associate with the entry')

    args = parser.parse_args()

    if args.command == 'add':
        # Determine entry type
        entry_type = 2  # Default to peronal
        if args.work:
            entry_type = 1
        elif args.jobby:
            entry_type = 3
        elif args.sleep:
            entry_type = 4

        # Get entry text
        entry_text = ' '.join(args.entry)
        
        if not entry_text:
            print("Error: No entry text provided")
            sys.exit(1)

        try:
            add_entry(entry_text, entry_type)
            print(f"Entry successfully added with type {entry_type}")
        except Exception as e:
            print(f"Error: Failed to add entry - {str(e)}")
            sys.exit(1)

    elif args.command == 'meeting-note':
        entry_text = ' '.join(args.entry)
        
        if not entry_text:
            print("Error: No entry text provided")
            sys.exit(1)

        try:
            add_meeting_entry(entry_text, args.meeting)
            print(f"Entry successfully added with meeting ID {args.meeting}")
        except Exception as e:
            print(f"Error: Failed to add entry - {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    main()
