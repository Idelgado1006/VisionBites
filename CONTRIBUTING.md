# Contributing to VisionBites

Thank you for contributing to VisionBites, an open-source AI project developed during Hacktoberfest Hack Day Panama City 2026.

## Project Principles

- Keep the project functional, reproducible, and easy to understand.
- Follow the existing code structure established by the development team.
- Keep changes focused and clearly documented.
- Never commit API keys, credentials, or local environment files.
- Do not invent nutritional information or present fictional inventory data as real-world measurements.
- Document AI-assisted development and verify generated outputs.

## Team Responsibilities

| Role | Responsibility |
|---|---|
| Repository Maintainer | Repository administration, documentation, code integration, and final submission |
| Development & UI | Application code, Gemma 4 integration, user interface, and optimization |
| Data & Validation | Inventory datasets, nutritional sources, testing, and verification |

The development team determines the internal application directory structure.

## Git Workflow

All development must take place in dedicated branches.

### Branch Naming

- `main` — Official stable version.
- `feat/desarrollo` — Application development and integrations.
- `feat/datos` — Data, nutritional references, and validation.
- `docs/*` — Documentation improvements.
- `fix/*` — Bug fixes.

### Creating a Branch

```bash
git switch main
git pull --ff-only origin main
git switch -c feat/desarrollo
```

Replace the branch name with the appropriate one for your role.

### Committing Changes

Use descriptive commits following Conventional Commits.

Example:

```bash
git add .
git commit -m "feat(ai): integrate Gemma 4 recipe generation" -m "Implement structured recipe generation through the Gemini API and validate model responses."
```

Never stage credentials or local secrets.

### Pushing Changes

```bash
git push -u origin feat/desarrollo
```

Replace the branch name as needed.

### Pull Requests

1. Push your changes to your assigned branch.
2. Open a pull request targeting `main`.
3. Describe what changed and why.
4. Explain how the changes were tested.
5. Disclose AI-assisted work where applicable.
6. Request review from the repository maintainer.

Only approved changes should be merged into `main`.

## Pull Request Checklist

- [ ] Changes follow the agreed project architecture.
- [ ] No credentials or sensitive files are included.
- [ ] The application or relevant module has been tested.
- [ ] Nutrition calculations use documented reference values.
- [ ] Ingredient quantities cannot exceed available inventory.
- [ ] README instructions are updated when necessary.
- [ ] AI-assisted changes have been reviewed and disclosed.

## Gemma 4 Requirements

For the MLH Gemma 4 challenge, the project must use a supported Gemma 4 model through the Gemini API.

Supported challenge model identifiers include:

- `gemma-4-26b-a4b-it`
- `gemma-4-31b-it`

Local-only Ollama inference does not fulfill the Gemma 4 API requirement for this challenge.

The selected model and tested API/SDK versions must be documented.

## Security

Store the Gemini API key locally:

```env
GEMINI_API_KEY=your_api_key_here
```

The `.env` file must never be committed.

If a credential is accidentally exposed, notify the maintainer immediately and revoke or rotate the credential.

## Data Integrity

Nutritional measurements must be traceable to identifiable sources.

The application must clearly distinguish:

- Fictional demo inventory data.
- Reference nutritional measurements.
- AI-generated candidate recipes.
- Mathematically computed production plans.

VisionBites does not provide clinical advice or certify food safety.

## License

By contributing, you agree that your contributions will be distributed under the project's MIT License.
