# Session 11: The Iconostasis of EmberHeart
**Date:** 2026-02-23
**Focus:** Asset Stabilization & Repository Deployment

## Key Topics
- **Asset Migration**: Migrated 31 character portraits from external CDN links to local character-specific directories.
- **Portrayal Gap Closure**: Identified 16 characters without portraits. Generated 15 high-quality grimdark portraits via AI and integrated 1 user-provided portrait (Arin).
- **NPC Record Expansion**: Created specialized records and assets for 5 major Sovereignty NPCs (Commander Vex, Grand Marshal Malakor, Elder Thorne, Queen Elara, Rix the Scavenger).
- **GitHub Deployment**: Initialized and pushed the `EmberHeartReborn` repository to GitHub, ensuring security via `.gitignore` and stabilization of all 62 character files.
- **Remote Asset Serving**: Updated 49 character profiles to point towards GitHub raw content URLs for their avatars, ensuring cross-platform accessibility.

## Decisions Made
1.  **Local-First Hosting**: Moved away from Discord CDN links for character portraits to prevent asset loss or expiration.
2.  **Surgical Exclusions**: Configured Git to ignore `gamebooks` and `gamebooks_md` to keep the repository focused on core logic and public assets.
3.  **URL-based Avatar Resolution**: Standardized on raw GitHub URLs in `profile.json` as the primary `avatar_url` source.

## Action Items
- [ ] **Quota Reset**: Generate the final 15 missing portraits (CDN-only) once the 5-hour image generation quota resets.
- [ ] **Security Audit**: Perform a deep dive into `.env` handling and local configuration hardening (on Roadmap).
- [ ] **Campaign Resume**: Re-engage the story logic now that the visual library is stabilized.

## Insights
- **Network Resilience**: Automated Git operations on network shares (FUNISERVER) require surgical lock management to avoid `PermissionError` and `index.lock` collisions.
- **Consistency via Scripting**: Bulk updating character profiles via Python scripts ensured zero manual entry errors across 62+ files.
