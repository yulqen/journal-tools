import sqlite3
import argparse
from datetime import datetime
import sys
import uuid
from dataclasses import dataclass
from typing import Optional, Dict, Any

DB_PATH = "/home/lemon/Documents/Notes/journal/datasette-journal/journal.db"


@dataclass
class SleepMetadata:
    asleep_time: str
    wake_time: str
    alcohol: int
    tech_excited: int


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()


class JournalEntry:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def delete_entry(self, entry_id: str) -> str:
        with DatabaseManager(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, entry FROM journal_entries WHERE id=?", (entry_id,)
            )

            entry = cursor.fetchone()

            if not entry:
                raise ValueError(f"Journal ID {entry_id} does not exist")

            # Ask for user confirmation before deleting
            confirmation = input(
                f"Are you sure you want to delete the entry with ID {entry_id}: {entry[1]}? (yes/no): "
            )
            if confirmation.lower() != "yes":
                print("Deletion canceled.")
                return "Deletion canceled."

            cursor.execute("DELETE FROM journal_entries WHERE id=?", (entry_id,))

            return f"Entry with ID {entry_id} has been deleted."

    def add_entry(
        self,
        entry_text: str,
        entry_type: int,
        sleep_metadata: Optional[SleepMetadata] = None,
    ) -> str:
        entry_id = str(uuid.uuid4())
        current_time = datetime.now().isoformat()

        with DatabaseManager(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO journal_entries (id, entry, type, date_added, date_updated) VALUES (?, ?, ?, ?, ?)",
                (entry_id, entry_text, entry_type, current_time, current_time),
            )

            if sleep_metadata:
                cursor.execute(
                    """INSERT INTO sleep_metadata
                       (journal_entry_id, asleep_time, wake_time, alcohol, tech_excited)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        entry_id,
                        sleep_metadata.asleep_time,
                        sleep_metadata.wake_time,
                        sleep_metadata.alcohol,
                        sleep_metadata.tech_excited,
                    ),
                )

        return entry_id

    def add_meeting_entry(self, entry_text: str, meeting_id: str) -> None:
        with DatabaseManager(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM meetings WHERE id = ?", (meeting_id,))
            if not cursor.fetchone():
                raise ValueError(f"Meeting ID {meeting_id} does not exist")

            entry_id = str(uuid.uuid4())
            current_time = datetime.now().isoformat()

            cursor.execute(
                "INSERT INTO journal_entries (id, entry, date_added, date_updated, meeting_id) VALUES (?, ?, ?, ?, ?)",
                (entry_id, entry_text, current_time, current_time, meeting_id),
            )

    def add_exercise_entry(self, entry_text: str, entry_type: int) -> str:
        entry_id = str(uuid.uuid4())
        current_time = datetime.now().isoformat()

        with DatabaseManager(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO exercise_entries (id, entry, type, date_added) VALUES (?, ?, ?, ?)",
                (entry_id, entry_text, entry_type, current_time),
            )

        return entry_id


class CommandLineInterface:
    def __init__(self):
        self.journal = JournalEntry(DB_PATH)
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="Journal Entry CLI Tool")
        subparsers = parser.add_subparsers(dest="command")

        self._add_entry_parser(subparsers)
        self._add_meeting_parser(subparsers)
        self._delete_entry_parser(subparsers)

        return parser

    def _add_entry_parser(self, subparsers):
        entry_parser = subparsers.add_parser("add", help="Add a regular journal entry")
        type_group = entry_parser.add_mutually_exclusive_group()
        type_group.add_argument(
            "--work", action="store_true", help="Work entry (type 1)"
        )
        type_group.add_argument(
            "--personal", action="store_true", help="Personal entry (type 2)"
        )
        type_group.add_argument(
            "--jobby", action="store_true", help="Jobby entry (type 3)"
        )
        type_group.add_argument(
            "--sleep", action="store_true", help="Sleep entry (type 4)"
        )
        type_group.add_argument(
            "--exercise", action="store_true", help="Exercise entry"
        )

        entry_parser.add_argument(
            "--exercise-type",
            type=int,
            help="Type of exercise - consult exercise_types table for integers",
        )

        entry_parser.add_argument(
            "--asleep-time", help="Time went to sleep (for sleep entries)"
        )
        entry_parser.add_argument(
            "--wake-time", help="Time woke up (for sleep entries)"
        )
        entry_parser.add_argument(
            "--alcohol",
            type=int,
            choices=[0, 1],
            help="Alcohol consumed (0 or 1, for sleep entries)",
        )
        entry_parser.add_argument(
            "--tech-excited",
            type=int,
            choices=[0, 1],
            help="Tech excitement before bed (0 or 1, for sleep entries)",
        )
        entry_parser.add_argument("entry", nargs="*", help="The journal entry text")

    def _add_meeting_parser(self, subparsers):
        meeting_parser = subparsers.add_parser(
            "meeting-note", help="Add a journal entry with meeting ID"
        )
        meeting_parser.add_argument("entry", nargs="*", help="The journal entry text")
        meeting_parser.add_argument(
            "--meeting", required=True, help="Meeting ID to associate with the entry"
        )

    def _delete_entry_parser(self, subparsers):
        delete_parser = subparsers.add_parser(
            "delete", help="Delete a journal entry with ID"
        )
        delete_parser.add_argument("entry_id", help="Journal ID to delete")

    def _get_entry_type(self, args) -> int:
        if args.work:
            return 1
        elif args.jobby:
            return 3
        elif args.sleep:
            return 4
        elif args.exercise:
            return 5
        return 2  # Default to personal

    def _validate_sleep_metadata(self, args) -> Optional[SleepMetadata]:
        if args.sleep:
            if not all(
                [
                    args.asleep_time,
                    args.wake_time,
                    args.alcohol is not None,
                    args.tech_excited is not None,
                ]
            ):
                raise ValueError(
                    "Sleep entries require --asleep-time, --wake-time, --alcohol, and --tech-excited"
                )

            return SleepMetadata(
                asleep_time=args.asleep_time,
                wake_time=args.wake_time,
                alcohol=args.alcohol,
                tech_excited=args.tech_excited,
            )
        return None

    def _validate_exercise_metadata(self, args) -> Optional[Dict[str, Any]]:
        if args.exercise:
            if not args.exercise_type:
                raise ValueError("Exercise entries require --exercise-type")

            return {"exercise_type": args.exercise_type}
        return None

    def run(self):
        args = self.parser.parse_args()

        if not args.command:
            self.parser.print_help()
            return

        try:
            if args.command == "add":
                self._handle_add_command(args)
            elif args.command == "meeting-note":
                self._handle_meeting_command(args)
            elif args.command == "delete":
                self._handle_delete_entry_command(args)
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)

    def _handle_add_command(self, args):
        entry_text = " ".join(args.entry)
        if not entry_text:
            raise ValueError("No entry text provided")

        entry_type = self._get_entry_type(args)
        sleep_metadata = self._validate_sleep_metadata(args)
        exercise_metadata = self._validate_exercise_metadata(args)

        if args.command == "add" and entry_type == 5:
            exercise_entry_type = exercise_metadata["exercise_type"]
            entry_id = self.journal.add_exercise_entry(entry_text, exercise_entry_type)
            print(
                f"Entry successfully added with type {exercise_entry_type} and ID {entry_id}"
            )
        else:
            entry_id = self.journal.add_entry(entry_text, entry_type, sleep_metadata)
            print(f"Entry successfully added with type {entry_type} and ID {entry_id}")

    def _handle_meeting_command(self, args):
        entry_text = " ".join(args.entry)
        if not entry_text:
            raise ValueError("No entry text provided")

        self.journal.add_meeting_entry(entry_text, args.meeting)
        print(f"Entry successfully added with meeting ID {args.meeting}")

    def _handle_delete_entry_command(self, args):
        msg = self.journal.delete_entry(args.entry_id)
        print(msg)


def main():
    cli = CommandLineInterface()
    cli.run()


if __name__ == "__main__":
    main()
