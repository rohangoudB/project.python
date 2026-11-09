"""
Application autofill helper.

Opens a page, fills the simple repetitive fields (name, email, college...)
from profile.json, then STOPS. You review everything and click Submit yourself.

Usage:
    python autofill.py                      # uses the local practice form
    python autofill.py https://example.com/apply
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
PROFILE_PATH = HERE / "profile.json"
SAMPLE_FORM = HERE / "sample_form.html"

# profile key -> words that may appear in the field's label/placeholder/name.
# Order matters: the first rule that matches wins, so specific rules go first.
RULES = [
    ("first_name", ["first name", "given name", "firstname", "fname"]),
    ("last_name", ["last name", "surname", "family name", "lastname", "lname"]),
    ("full_name", ["full name", "your name", "applicant name"]),
    ("email", ["email", "e-mail"]),
    ("phone", ["phone", "mobile", "contact number"]),
    ("university", ["university", "college", "institution"]),
    ("degree", ["degree", "programme", "program of study", "course of study"]),
    ("cgpa", ["cgpa", "gpa"]),
    ("graduation_year", ["graduation year", "expected graduation", "year of graduation"]),
    ("city", ["city"]),
    ("country", ["country"]),
    ("github", ["github"]),
    ("linkedin", ["linkedin"]),
    ("website", ["portfolio", "website", "personal site"]),
]

# Field types we never touch (passwords, uploads, checkboxes, buttons...).
SKIP_TYPES = {"hidden", "submit", "button", "file", "password",
              "checkbox", "radio", "image", "reset"}

# Runs inside the browser: lists every field with a text "hint" describing it.
JS_COLLECT = r"""
() => [...document.querySelectorAll('input, textarea, select')].map((el, i) => {
  el.setAttribute('data-autofill-id', i);
  let label = '';
  if (el.id) {
    const l = document.querySelector('label[for="' + el.id + '"]');
    if (l) label = l.innerText;
  }
  if (!label) {
    const p = el.closest('label');
    if (p) label = p.innerText;
  }
  return {
    id: i,
    tag: el.tagName.toLowerCase(),
    type: (el.type || '').toLowerCase(),
    hint: [label, el.getAttribute('aria-label'), el.placeholder, el.name, el.id]
      .filter(Boolean).join(' '),
  };
})
"""


def load_profile():
    with open(PROFILE_PATH, encoding="utf-8") as f:
        data = json.load(f)
    # Anything still set to EDIT_ME or empty is ignored.
    return {k: v for k, v in data.items() if v and v != "EDIT_ME"}


def match_field(hint):
    """Return the profile key that best matches a field hint, or None."""
    text = hint.lower().replace("_", " ").replace("-", " ")
    if text.strip() in {"name", "name *"}:
        return "full_name"
    for key, words in RULES:
        if any(w in text for w in words):
            return key
    return None


def autofill(page, profile):
    filled, skipped = [], []
    for field in page.evaluate(JS_COLLECT):
        hint = field["hint"].strip().replace("\n", " ")[:50]
        if field["type"] in SKIP_TYPES:
            continue
        if field["tag"] == "textarea":
            skipped.append(f"{hint or 'textarea'}  -> long answer, write this yourself")
            continue
        key = match_field(field["hint"])
        if key is None or key not in profile:
            skipped.append(f"{hint or '(unlabeled field)'}  -> no match")
            continue

        el = page.locator(f'[data-autofill-id="{field["id"]}"]')
        try:
            if field["tag"] == "select":
                el.select_option(label=profile[key])
            else:
                if el.input_value():  # don't overwrite what's already there
                    continue
                el.fill(profile[key])
            filled.append(f"{hint}  <-  {key}")
        except Exception as err:
            skipped.append(f"{hint}  -> could not fill ({type(err).__name__})")
    return filled, skipped


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else SAMPLE_FORM.resolve().as_uri()
    profile = load_profile()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("domcontentloaded")

        filled, skipped = autofill(page, profile)

        print(f"\nFilled {len(filled)} field(s):")
        for line in filled:
            print("  +", line)
        print(f"\nLeft {len(skipped)} field(s) for you:")
        for line in skipped:
            print("  -", line)

        print("\nReview the form in the browser, fix anything, and submit it yourself.")
        input("Press Enter here when you're done to close the browser... ")
        browser.close()


if __name__ == "__main__":
    main()
