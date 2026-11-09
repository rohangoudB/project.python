# Application Autofill Helper

Fills the repetitive fields on an application form from `profile.json`, then
stops so you can review and submit it yourself. It never clicks Submit, never
touches passwords or file uploads, and leaves essay boxes for you to write.

## Setup
```
pip install -r requirements.txt
playwright install chromium
```

## Run
1. Open `profile.json` and replace every `EDIT_ME` (those fields are skipped until you do).
2. Try the practice form first: `python autofill.py`
3. On a real application: `python autofill.py https://the-application-url`

## How it works
1. Opens the page in a visible browser.
2. Reads every input and works out its label, placeholder, and name.
3. Matches that text against keyword rules (`RULES` in autofill.py).
4. Fills matches, lists what it filled and skipped, and waits for you.

## Limits
- Fields inside iframes, and multi-step wizards, are not handled yet.
- Login-protected pages: log in yourself first, then run it on the form page.
- `profile.json` holds personal data. It is in `.gitignore`, so don't commit it.

## Ideas to extend it (good learning)
- Add rules for new fields (for example, "date of birth").
- Support multiple profiles (`profile_research.json`, `profile_industry.json`).
- Handle multi-step forms by re-running after clicking Next.
