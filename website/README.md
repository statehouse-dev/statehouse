# Statehouse Documentation Website

This directory contains the Docusaurus-based documentation website for Statehouse.

## Prerequisites

- Node.js >= 18.0
- npm or yarn

If using devbox:

```bash
devbox shell
```

## Local Development

Install dependencies:

```bash
cd website
npm install
```

Start the development server:

```bash
npm start
```

This starts a local server at `http://localhost:3000/` with hot reloading.

## Building

Build the static site:

```bash
npm run build
```

The output is in `build/`. Preview locally:

```bash
npm run serve
```

## Project Structure

```
website/
├── docs/                    # Documentation content
│   ├── index.md            # Docs landing page
│   ├── introduction/       # Introduction section
│   ├── concepts/           # Core concepts
│   ├── getting-started/    # Quickstart guides
│   ├── python-sdk/         # Python SDK reference
│   ├── grpc-internals/     # gRPC implementation details
│   ├── operations/         # Operational guides
│   ├── failure-modes/      # Failure handling
│   ├── examples/           # Example implementations
│   ├── faq.md             # FAQ
│   └── license.md         # License explanation
├── src/
│   ├── css/
│   │   └── custom.css      # Theme customization
│   └── pages/
│       └── index.tsx       # Homepage
├── docusaurus.config.ts    # Site configuration
├── sidebars.ts             # Sidebar structure
├── package.json            # Dependencies
└── tsconfig.json           # TypeScript config
```

## Configuration

Key configuration in `docusaurus.config.ts`:

| Setting | Value |
|---------|-------|
| Site name | Statehouse |
| Base URL | `/` (custom domain statehouse.dev) |
| Default theme | Dark |
| Blog | Disabled |

## Adding Documentation

1. Create a markdown file in the appropriate `docs/` subdirectory
2. Add frontmatter if needed:

```markdown
---
sidebar_position: 3
title: My Page Title
---

# My Page

Content here...
```

3. Update `sidebars.ts` if needed

## Styling

Custom styles are in `src/css/custom.css`:

- Dark theme with slate/blue palette
- Restrained, professional appearance
- No animations or flashy elements

## Deployment

The site is deployed to **GitHub Pages** at **https://statehouse.dev** via GitHub Actions on push to `main` (see `.github/workflows/deploy-docs.yml`).

**Required (one-time):** In the repo go to **Settings** → **Pages**. Under **Build and deployment**, set **Source** to **GitHub Actions**. If Source is "Deploy from a branch", the workflow will get a 404 when deploying.

Manual deployment:

After DNS propagates (up to 48 hours, often minutes), GitHub will show a green check and HTTPS will work.

Manual deploy (optional): `npm run deploy` builds and pushes to the `gh-pages` branch; the primary deployment is via the Actions workflow above.

## Broken Links

The build fails on broken links:

```typescript
onBrokenLinks: 'throw',
onBrokenMarkdownLinks: 'throw',
```

Fix broken links before pushing.

## Writing Style

Documentation follows these guidelines:

- Declarative, technical language
- No marketing copy or hype
- No emojis or exclamation marks
- Short paragraphs and lists
- Explicit about tradeoffs
- "Draft / MVP" notices where appropriate
