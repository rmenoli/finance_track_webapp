# Adding a New User

Each user gets their own isolated Neon database branch and a unique API key.

---

## Step 1 — Create a Neon branch

1. Go to your [Neon dashboard](https://console.neon.tech)
2. Select the project
3. Click **Branches** → **Create branch**
4. Branch from **main** (the production branch, NOT from another user branch)
5. Name it something like `user-<name>`
6. Copy the **connection string** (PostgreSQL URL) — you'll need it in the next steps

> **Important:** always branch from `main`. Branching from another user branch inherits their data.

---

## Step 2 — Generate an API key

Generate a secure random string to use as the API key:

```bash
openssl rand -hex 32
```

Keep this safe — you'll share it with the user and add it to the config.

---

## Step 3 — Update `API_KEY_DB_MAP`

This map lives in two places and both need to be updated.

### 3a. Lambda environment variable (production)

1. Go to **AWS Console** → **Lambda** → your function
2. **Configuration** → **Environment variables** → **Edit**
3. Find `API_KEY_DB_MAP` and add the new entry:
   ```json
   {
     "existing-key": "postgresql://...",
     "new-user-key": "postgresql://new-user-connection-string"
   }
   ```
4. **Save**

### 3b. GitHub secret (CI/CD migrations)

1. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Edit the `API_KEY_DB_MAP` secret with the same updated JSON as above
3. **Save**

> Both must match. The Lambda env var controls authentication in production. The GitHub secret controls which databases get migrated on each deploy.

---

## Step 4 — Trigger a deploy

Push any commit to `main` or manually trigger the **Deploy to AWS** workflow from GitHub Actions.

The CI/CD pipeline will automatically run `alembic upgrade head` against the new database. No manual migration commands needed — the pipeline handles it.

- Branched from `main`: new branch already has the schema, pipeline sees it's at head and does nothing
- Fresh empty branch: pipeline runs all migrations from scratch and creates all tables

---

## Step 5 — Share the API key with the user

Send the user their API key. They enter it on the login page of the app.

---

## Troubleshooting

**Migration fails with `type already exists`**

The new branch was created from a user branch instead of `main`, inheriting a schema created without Alembic tracking. Fix by stamping:

```bash
cd backend
DATABASE_URL="postgresql://new-user-connection-string" uv run alembic stamp head
```

Then re-trigger the deploy.

**User gets 401 on all requests**

The API key in Lambda env var doesn't match what the user is entering. Double-check `API_KEY_DB_MAP` in the Lambda configuration.
