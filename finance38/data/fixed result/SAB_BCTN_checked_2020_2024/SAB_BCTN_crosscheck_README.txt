SAB BCTN cross-check notes (2020-2024)

What was rechecked against the uploaded annual reports (BCTN):
1) Ownership / disclosure rows:
   - 1 Managerial ownership
   - 2 State ownership
   - 3 Institutional ownership
   - 4 Foreign ownership

2) Other clearly verifiable rows:
   - 5 Total share outstanding
   - 6 Total sales revenue and Net sales revenue
   - 36 Number of employees
   - 38 Firm age

3) Binary / disclosure-sensitive rows:
   - 18 R&D expenditure
   - 19 Product innovation
   - 20 Process innovation

Rules used:
- State ownership was coded from the SCIC holding shown in the shareholder table.
- Foreign ownership was coded from the foreign-shareholder line in the shareholder table.
- Institutional ownership was computed from organization ownership in the BCTN shareholder table:
    state institution + Vietnam Beverage + domestic organizations + foreign organizations.
  This overlaps with foreign ownership by design.
- Managerial ownership was computed from the insider-shareholding table:
    2020-2021 include 100 shares of a board member plus 1,700 shares of the chief accountant;
    2022 only 1,700 shares of the chief accountant;
    2023-2024 3,400 shares of the chief accountant after the 1:1 bonus-share issuance.
  All of these round to 0.0003%.
- Total share outstanding was corrected to 641,281,186 for 2020-2022 and 1,282,562,372 for 2023-2024.
- Net sales revenue was corrected from the annual-report financial highlights:
    2020 = 27,961 bn VND
    2021 = 26,374 bn VND
    2022 = 34,979 bn VND
    2023 = 30,461 bn VND
    2024 = 31,872 bn VND
- Number of employees was coded from consolidated / group-level BCTN disclosures:
    2020 = 8,388
    2021 = 8,135
    2022 = 8,550
    2023 = 8,139
    2024 = 7,829
  This replaces parent-only headcount values such as 774 / 804 / 815 / 738 where applicable.
- Firm age was computed from 1875 as the historical starting point stated in SABECO’s company-history pages:
    2020=145, 2021=146, 2022=147, 2023=148, 2024=149.
- R&D expenditure was set to 0 because the uploaded BCTN does not separately disclose a monetary R&D expense line.
- Product innovation was coded 1 for all years because the BCTN shows clear product / brand launch evidence across the period
  (for example Bia Lạc Việt, Bia Saigon Chill, relaunches / premium variants, Saigon Export Premium, 333 Pilsner).
- Process innovation was coded 1 for all years because the BCTN shows strong process / system / digital / operational innovation evidence
  across the period (for example SABECO 4.0, distribution / logistics improvements, governance upgrades, solar / efficiency projects, SRC setup).

Key corrected values:
- State ownership:
    2020 = 36.00%
    2021 = 36.00%
    2022 = 36.00%
    2023 = 36.00%
    2024 = 36.00%

- Foreign ownership:
    2020 = 9.50%
    2021 = 8.94%
    2022 = 9.01%
    2023 = 8.11%
    2024 = 7.11%

- Institutional ownership:
    2020 = 89.92%
    2021 = 99.09%
    2022 = 90.79%
    2023 = 99.01%
    2024 = 97.31%

Important cautions:
- 2023 ownership in the annual-report shareholder section is shown at 05/01/2024 after the 1:1 bonus-share issuance; I therefore kept
  the post-issuance share count for 2023 in the checked CSV, matching the ownership section presented in the uploaded BCTN.
- Product innovation and process innovation are evidence-based codings from the annual reports, but they are still judgment-based binary variables,
  not directly disclosed checkbox fields.
- I did not force unsupported fixes for rows that were not clearly recoverable from the uploaded BCTN / BCTC text alone.
