# Skill: github-pages-fetch

## Trigger
Use this skill whenever the user shares a URL that contains `github.io`.

## Rule
Do NOT fetch the GitHub Pages URL directly. Rewrite it to the raw GitHub URL before fetching.

**URL rewrite pattern:**
```
https://<username>.github.io/<repo>/<path>
→
https://raw.githubusercontent.com/<username>/<repo>/main/<path>
```

Where `<username>` is extracted from the subdomain, `<repo>` is the first path segment, and `<path>` is the remainder.

**Special case — user root repo** (repo name equals `<username>.github.io`):
```
https://<username>.github.io/<path>
→
https://raw.githubusercontent.com/<username>/<username>.github.io/main/<path>
```
If the rewritten URL returns a 404, also try branch `master` instead of `main`.

## Steps
1. Parse the GitHub Pages URL to extract `username`, `repo`, and `path`.
2. Rewrite to `raw.githubusercontent.com` using the pattern above.
3. Fetch using WebFetch with the rewritten URL.
4. If the fetch fails (404/redirect), retry with branch `master`.
5. Proceed with the user's request on the fetched content.
