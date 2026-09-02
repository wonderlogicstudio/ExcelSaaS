# Pre-launch user-test playbook

> Historical reference: the approved M3 pass protocol is now the staged 8-person plan in `docs/m3/` (Round 1: 3, Round 2: 5). The 10-person counts below remain an earlier exploratory/revenue reference and must not be used to declare M3 pass or fail.

## Goal

Validate whether target users understand the value, trust the diagnosis, and accept the quote **before** building payment or production repair.

## Recruit the first 10 testers

Recruit across three groups:

- 4 office workers who regularly receive or send operational Excel files;
- 3 small-business owners or administrators who maintain sales, inventory, or settlement files;
- 3 advanced Excel users who can challenge the credibility of findings.

Do not recruit only developers or acquaintances who want to be supportive. At least half should have a workbook problem they personally experienced.

## Test protocol

1. Show the landing page without explaining it.
2. After five seconds, ask: “What do you think this service does?”
3. Ask the tester to choose between sample mode and a synthetic workbook.
4. Observe whether they understand risk score, finding evidence, repair classes, exclusions, and price.
5. Ask what they expect to receive after payment.
6. Ask whether they would pay the displayed amount today and why.
7. Ask what information would be required before uploading a company file.
8. Do not defend the design during the task; record confusion verbatim.

## Core questions

- Which finding would you act on first?
- Do you believe the service actually found this issue? What evidence changed your confidence?
- What does “safe candidate” mean to you?
- Is the difference between diagnosis and repair clear?
- Is the quote too cheap, reasonable, or too expensive?
- What should happen if a larger issue is found after payment?
- Would you upload a work file? If not, what would need to change?
- Would you prefer a browser-only private scan, server scan, or desktop agent?

## Pass thresholds for M3

- 8/10 correctly explain the service after five seconds.
- 8/10 distinguish free diagnosis from paid repair.
- 7/10 can identify included and excluded work without help.
- 6/10 say they would consider paying for a real problem file.
- No more than 2/10 believe all Excel errors are guaranteed to be found.
- At least 5/10 trust a synthetic upload; record separate willingness for real company files.

## Evidence to retain

- anonymous tester ID and segment;
- task completion and time;
- exact confusion statements;
- quote willingness and price reaction;
- privacy objection category;
- feature requests, separated into recurring and one-off;
- decision: preserve, revise, or reject the value proposition.

Do not store the tester's workbook, company name, email, or raw screen recording unless separately consented.
