To launch a local postgres instance via Docker, run `docker run --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=postgres -d postgres`

To connect to this postgres DB, set environment variable in .env file `DATABASE_URL=postgres://postgres:postgres@postgres:5432/postgres`

Setup:
- Once you add a phone, add a user to Twilio verified numbers