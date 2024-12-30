# Journal Entry CLI Tool

A simple command-line interface (CLI) tool for managing journal entries. This tool allows you to add regular journal entries and entries associated with meetings. It uses SQLite as its database backend.

### Features

- Add regular journal entries with different types: Work, Personal, Jobby, and Sleep.
- Add journal entries associated with specific meetings.
- Entry types are supported as command-line arguments.
- Each entry is timestamped, and unique IDs are generated for each entry.

### Prerequisites

- Python 3.x
- SQLite database
- A pre-existing SQLite database with a `journal_entries` table and a `meetings` table.
  
### Database Schema

The script assumes the following minimal structure for the database:

**journal_entries Table:**
```sql
CREATE TABLE journal_entries (
    id TEXT PRIMARY KEY,
    entry TEXT NOT NULL,
    type INTEGER,
    date_added TEXT,
    date_updated TEXT,
    meeting_id TEXT
);
```

**meetings Table:**
```sql
CREATE TABLE meetings (
    id TEXT PRIMARY KEY,
    date TEXT,
    name TEXT,
    subject TEXT
);
```

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/journal-entry-cli.git
   cd journal-entry-cli
   ```

2. Install any required dependencies (if applicable).

### Usage

The script can be invoked from the command line. The basic syntax is as follows:

```bash
python journal.py <command> [options]
```

#### Commands

1. **Add a Regular Journal Entry**
   ```bash
   python journal.py add [entry_text] [--work] [--personal] [--jobby] [--sleep]
   ```
   Example:
   ```bash
   python journal.py add --work "Completed project XYZ"
   ```

2. **Add a Meeting Note**
   ```bash
   python journal.py meeting-note [entry_text] --meeting <meeting_id>
   ```
   Example:
   ```bash
   python journal.py meeting-note "Discussed project timeline" --meeting meeting123
   ```

### Error Handling

- The script checks for the existence of the specified meeting ID before attempting to add a meeting note.
- Various error messages are displayed for missing entry text or database errors.

### Contribution

Feel free to fork the repository and submit issues or pull requests if you have improvements or bug fixes!

### License

This project is licensed under the terms of the [GNU General Public License v3.0 (GPL-3.0)](https://www.gnu.org/licenses/gpl-3.0.html). See the [LICENSE](LICENSE) file for details.

### Author

[yulqen](https://yulqen.org) - Poetry of the digital mind.
