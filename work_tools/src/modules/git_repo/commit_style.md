# Commit Message Style Guide

Follow the **Conventional Commits** specification.

## Format

```
[<module>] <type>: <subject>

<body>
```

- **module** (optional): Short name of the affected module or scope.
- **type**: One of `feat`, `fix`, `refactor`, `docs`, `style`, `test`, `chore`, `build`, `ci`, `perf`.
- **subject**: Imperative, lowercase, no period at the end. Keep under 72 characters.
- **body** (optional): Explain *what* and *why*, not *how*. Use bullet points for multiple changes.

## Examples

```
[auth] feat: add browser-based cookie authentication

- Implement BrowserTokenBaseClient base class
- Support both Bearer token and Cookie auth modes
- Add automatic token-expiration detection with user guidance
```

```
[git] fix: handle empty staged diff gracefully
```

```
refactor: migrate TaigaClient to httpx
```

## Rules

1. Match the style of recent commit logs provided below.
2. If a module name is provided, always prefix the subject with `[module]`.
3. Write in English.
4. One commit should represent one logical change.
