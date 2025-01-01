import sqlite3
import argparse
from datetime import datetime
import sys
import uuid

DB_PATH = "/home/lemon/Documents/Notes/journal/datasette-journal/journal.db"

def add_entry(entry_text, entry_type, sleep_metadata=None):
    """Add a new entry to the journal and sleep metadata if provided"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    entry_id = str(uuid.uuid4())
    current_time = datetime.now().isoformat()

    try:
        # Insert the journal entry
        cursor.execute(
            'INSERT INTO journal_entries (id, entry, type, date_added, date_updated) VALUES (?, ?, ?, ?, ?)',
            (entry_id, entry_text, entry_type, current_time, current_time)
        )

        # If this is a sleep entry, add the sleep metadata
        if sleep_metadata:
            cursor.execute(
                '''INSERT INTO sleep_metadata
                   (journal_entry_id, asleep_time, wake_time, alcohol, tech_excited)
                   VALUES (?, ?, ?, ?, ?)''',
                (entry_id,
                 sleep_metadata['asleep_time'],
                 sleep_metadata['wake_time'],
                 sleep_metadata['alcohol'],
                 sleep_metadata['tech_excited'])
            )

        conn.commit()
        return entry_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
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

    # Add sleep metadata arguments
    entry_parser.add_argument('--asleep-time', help='Time went to sleep (for sleep entries)')
    entry_parser.add_argument('--wake-time', help='Time woke up (for sleep entries)')
    entry_parser.add_argument('--alcohol', type=int, choices=[0, 1],
                            help='Alcohol consumed (0 or 1, for sleep entries)')
    entry_parser.add_argument('--tech-excited', type=int, choices=[0, 1],
                            help='Tech excitement before bed (0 or 1, for sleep entries)')

    entry_parser.add_argument('entry', nargs='*', help='The journal entry text')

    # Meeting entry parser
    meeting_parser = subparsers.add_parser('meeting-note', help='Add a journal entry with meeting ID')
    meeting_parser.add_argument('entry', nargs='*', help='The journal entry text')
    meeting_parser.add_argument('--meeting', required=True, help='Meeting ID to associate with the entry')

    args = parser.parse_args()

    if args.command == 'add':
        # Determine entry type
        entry_type = 2  # Default to personal
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
            # If this is a sleep entry, verify all required sleep metadata is provided
            sleep_metadata = None
            if args.sleep:
                if not all([args.asleep_time, args.wake_time,
                           args.alcohol is not None, args.tech_excited is not None]):
                    print("Error: Sleep entries require --asleep-time, --wake-time, --alcohol, and --tech-excited")
                    sys.exit(1)

                sleep_metadata = {
                    'asleep_time': args.asleep_time,
                    'wake_time': args.wake_time,
                    'alcohol': args.alcohol,
                    'tech_excited': args.tech_excited
                }

            entry_id = add_entry(entry_text, entry_type, sleep_metadata)
            print(f"Entry successfully added with type {entry_type} and ID {entry_id}")
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

