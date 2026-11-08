# Contributing to MechWar-X

MechWar-X is an FIU group project. Coordinate work with teammates before changing shared database definitions or user-interface flows.

## Git workflow

1. Clone the repository and create a branch for your change:

   ```bash
   git clone https://github.com/abtahac-hue/MechWar-X.git
   cd MechWar-X
   git switch -c feature/short-description
   ```

2. Install dependencies using `python -m pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and configure **your own local database**.
4. Work in your branch, and test against a separate backed-up MySQL database.
5. Commit changes with a clear message, push your branch, and open a pull request.
6. Have at least one teammate review SQL or data-changing modifications before merging.

## Security and data-handling rules

- **Never commit** `.env`, database passwords, API tokens, private keys, real customer details, `.ibd` files, or local database exports.
- Use placeholder values in documentation and screenshots.
- Do not commit SQL test scripts that insert invalid records or modify live data without labeling and isolating them.
- Do not run the setup scripts against an existing populated database.
- Keep the sample dataset fictional.

## Review checklist

- [ ] App starts with a locally running MySQL 8 server
- [ ] All five navigation pages open
- [ ] No real credentials or private data added
- [ ] Changes to SQL are explained and tested on a disposable database
- [ ] Screenshots accurately represent the current UI
- [ ] Existing data isn't silently deleted or modified

## Local synchronization

Updates to README and SQL files are sometimes committed directly on GitHub. Before editing locally, check for local uncommitted work with `git status`, save it if needed, and then `git pull --rebase origin main`. Never force-push over a teammate's changes.
