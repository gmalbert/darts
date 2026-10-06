# Repository instructions

- When committing and/or pushing something to GitHub as part of a PR, always include a detailed description in Markdown.
- Serve cached odds from the previous overnight GitHub Actions run. Never add visitor-triggered odds-provider calls, startup refreshes, browser polling, or a continuous odds worker on Render.
- Keep heavy scraping, historical rebuilds, Elo calculations, and model training on GitHub Actions.
- Odds-provider credentials and refresh permission belong only to the dedicated overnight GitHub job. Show snapshot timestamps; do not describe cached prices as live.
