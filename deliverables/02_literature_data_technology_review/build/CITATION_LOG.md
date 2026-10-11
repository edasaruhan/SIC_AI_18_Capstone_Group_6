# Citation log: milestone 2 review

Every source in the report was checked on **11 Oct 2026** before it was cited. The machine-readable record is in `references_verified.json`. The include/exclude decisions are also recorded in scite (session `339835e5-59fb-4be3-ab5f-d67d2387ce71`): 38 sources cited, 5 excluded.

## How sources were verified

- **Journal and conference papers (22 DOIs).** Checked in Crossref for title, authors, venue, volume and pages, and in OpenAlex for abstract and retraction flag. None are retracted. Elhai et al. (2017) was additionally checked in PubMed.
- **arXiv papers (4).** Checked through the arXiv API: AwareMind 2609.08909, Bai 1803.01271, Lundberg 1705.07874 and Vaswani 1706.03762.
- **Web sources (12).** Each fact was read on the official page: WHO, KVKK (official English text plus the Turkish Official Gazette PDF), Android Developers, Google Play policy, Apple Developer, Google Digital Wellbeing, LiteRT, ONNX Runtime, Yeşilay YEDAM, OSF and Kaggle.
- **Paper summaries in Table 1** use only what the abstract or full text states. Where a number wasn't available it was left out; for example, the sample size of Shin and Dey (2013) is not stated.

## Caveats

| Item | Note |
|---|---|
| AwareMind publisher DOI `10.1145/3821659` | **Not registered yet**: doi.org returned 404 on 11 Oct 2026. The report cites the arXiv preprint (`10.48550/arXiv.2609.08909`, MobileHCI 2026). The M1 proposal cited the publisher DOI, which will probably work once the paper is published. |
| Olson et al. (2022) | No abstract is available from open sources, so it is cited only for the claim in its title (smartphone addiction is increasing across 24 countries) and is not in Table 1. |
| Noyan et al. (2015) | The metadata gives only the first page (73), so the reference shows that page and the DOI. Author names are spelled as in Crossref (Darcin, Yilmaz). |
| Monge Roffarello & De Russis (2023) | Crossref splits the surname; it is cited with the correct compound surname. Online in 2023, TOCHI 30(4). |

## Excluded

| Source | Reason |
|---|---|
| "Landolfi et al. (2021)", DOI `10.1145/3447526.3472020` from the archived idea-phase notes | The DOI belongs to a different paper ("StepUp Forecast"), and no correct record was found. **The archived notes contain this wrong citation.** |
| Kwon et al. (2013), full SAS | The short version (SAS-SV) is cited instead |
| Cho et al. (2021) | Verified but not needed in the final text |
| Oulasvirta et al. (2012); Rozgonjuk et al. (2018) | No abstract was available to summarize accurately |
