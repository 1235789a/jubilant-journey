# Platform Registry

The seed file contains 31 destinations. Runtime seeding merges each record with a complete conservative default, then persists the full Platform object in SQLite. `null` and `UNVERIFIED` are intentional values, not omissions.

Official pages were checked on 2026-08-19 where `last_verified_at` is present. This means the linked evidence was inspected; it does not mean the complete platform/account/product/country/contract rule set is safe for live automation. No record is `VERIFIED` for live publication in V1.

## Coverage

| # | Platform | Vertical | Maturity | Rule state | V1 behavior |
|---:|---|---|---|---|---|
| 1 | 番茄小说 | 国内网文 | P0 | UNVERIFIED | Registry only |
| 2 | 七猫 / 奇妙 | 国内网文 | P0 | UNVERIFIED | Registry only |
| 3 | 起点 / 阅文 | 国内网文 | P0 | UNVERIFIED | Registry only |
| 4 | 纵横 | 国内网文 | P0 | UNVERIFIED | Registry only |
| 5 | Amazon KDP | 国际电子书 | P2 | REVIEW_REQUIRED | EPUB/listing package |
| 6 | Draft2Digital | 国际电子书 | P2 | REVIEW_REQUIRED | One aggregator package; no downstream duplicates |
| 7 | Chrome Web Store | 浏览器插件 | P2 | REVIEW_REQUIRED | Manifest/build/listing package |
| 8 | Microsoft Edge Add-ons | 浏览器插件 | P2 | REVIEW_REQUIRED | Adapted manifest/build package |
| 9 | Firefox Add-ons | 浏览器插件 | P2 | REVIEW_REQUIRED | Gecko manifest/build package |
| 10 | GitHub Marketplace | 开发者工具 / SaaS | P0 | UNVERIFIED | Registry only |
| 11 | VS Code Marketplace | 开发者工具 | P0 | UNVERIFIED | Registry only |
| 12 | JetBrains Marketplace | 开发者工具 | P0 | UNVERIFIED | Registry only |
| 13 | WordPress Plugin Directory | 开发者工具 | P0 | UNVERIFIED | Registry only |
| 14 | Slack Marketplace | B2B SaaS | P0 | UNVERIFIED | Registry only |
| 15 | Google Workspace Marketplace | B2B SaaS | P0 | UNVERIFIED | Registry only |
| 16 | Atlassian Marketplace | B2B SaaS | P0 | UNVERIFIED | Registry only |
| 17 | Shopify App Store | B2B SaaS | P0 | UNVERIFIED | Registry only |
| 18 | Google Play | App / 游戏 | P0 | BLOCKED_BY_AGE | Development/metadata only |
| 19 | Apple App Store | App / 游戏 | P0 | BLOCKED_BY_AGE | Development/testing only |
| 20 | Microsoft Store | App / 游戏 | P0 | UNVERIFIED | Registry only |
| 21 | itch.io | 游戏 / 素材 | P0 | UNVERIFIED | Recommended future low-cost pilot |
| 22 | Steam | 游戏 | P0 | UNVERIFIED | Fee/paperwork/review manual |
| 23 | Epic Games Store | 游戏 | P0 | BLOCKED_BY_AGE | Development/metadata only |
| 24 | Fab | 数字素材 | P0 | UNVERIFIED | Registry only |
| 25 | Unity Asset Store | 数字素材 / 工具 | P0 | UNVERIFIED | Registry only |
| 26 | Creative Market | 数字素材 | P0 | UNVERIFIED | Registry only |
| 27 | X | GEO 品牌 | P0 | UNVERIFIED | Brand connector planned |
| 28 | Facebook | GEO 品牌 | P0 | UNVERIFIED | Existing workflow connector boundary |
| 29 | LinkedIn | GEO 品牌 | P0 | UNVERIFIED | Brand connector planned |
| 30 | Reddit | GEO 品牌 | P0 | UNVERIFIED | Community-native connector planned |
| 31 | YouTube | GEO 品牌 | P0 | UNVERIFIED | Three platform-native channel slots planned |

Summary: P0 = 26, P1 = 0, P2 = 5, P3 = 0.

## Selected current official evidence

- [Chrome Web Store documentation](https://developer.chrome.com/docs/webstore) and [program policies](https://developer.chrome.com/docs/webstore/program-policies/policies).
- [Microsoft Edge extension publication](https://learn.microsoft.com/en-us/microsoft-edge/extensions/publish/publish-extension).
- [Firefox add-on submission](https://extensionworkshop.com/documentation/publish/submitting-an-add-on/) and [policies](https://extensionworkshop.com/documentation/publish/add-on-policies/).
- [KDP content guidelines](https://kdp.amazon.com/help/topic/G200672390) and [terms/eligibility](https://kdp.amazon.com/terms-and-conditions). KDP states that the account holder must be at least 18/majority age and permits a parent or guardian to be the publisher of a minor's book.
- [Draft2Digital knowledge base](https://draft2digital.com/knowledge-base/) and [partners](https://draft2digital.com/partners/).
- [Google Play Console onboarding](https://support.google.com/googleplay/android-developer/answer/6112435) states the account registrant must be at least 18.
- [Apple Developer enrollment](https://developer.apple.com/help/account/membership/program-enrollment/) requires the legal age of majority.
- [Epic Games Store requirements](https://dev.epicgames.com/docs/epic-games-store/requirements-guidelines/distribution-requirements/requirements-overview) require age 18 for publishing tools.
- [GitHub Marketplace requirements](https://docs.github.com/en/apps/github-marketplace/creating-apps-for-github-marketplace/requirements-for-listing-an-app), [Slack distribution](https://docs.slack.dev/slack-marketplace/distributing-your-app-in-the-slack-marketplace), [Google Workspace review](https://developers.google.com/workspace/marketplace/about-app-review), [Atlassian approval](https://developer.atlassian.com/platform/marketplace/app-approval-guidelines/), and [Shopify review](https://shopify.dev/docs/apps/launch/app-store-review/review-process).
- [Steam Direct](https://partner.steamgames.com/steamdirect), [itch.io creator guide](https://itch.io/docs/creators/getting-started), [Unity submission guidelines](https://assetstore.unity.com/publishing/submission-guidelines), and [Creative Market AI label](https://support.creativemarket.com/hc/en-us/articles/26926388691099-Navigating-Our-New-AI-Label).

## Updating a rule

1. Read current primary official sources.
2. Identify account, product, country, payout, AI, automation, exclusivity, and review implications.
3. Update the platform record, `rule_version`, evidence URLs, notes, and `last_verified_at`.
4. Keep unknown fields unknown.
5. Add or update route tests if a hard gate changes.
6. Run `make check`.

Do not change a record to `VERIFIED` until the complete hard-gate set for the intended live action has been reviewed.
