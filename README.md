# World News — 24 November 2026 (one-image summary)

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/sutenosakamoto-gif/news-image-20261124/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/sutenosakamoto-gif/news-image-20261124/reward.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

A one-image broadsheet front page summarising thirty world news
stories of Tuesday, 24 November 2026, prepared as an entry
for the make.fun bounty "Sum up 24 November's world news in one image"
(final deadline 2026-11-26 09:00 JST).

## Contents

- `main.py` — the entry point: a standard-library only, self-contained
  renderer. Running `python3 main.py` renders the image to
  `/output/entry.png` (no network).
- `SOURCES.md` — the thirty stories, their sources (outlet + date)
  and URLs.

## How to run

```bash
python3 main.py   # standard library only, no dependencies
```

Running `python3 main.py` renders the image to `/output/entry.png`,
falling back to `./entry.png` next to the script when `/output` is not
writable. The render is deterministic: repeated runs produce identical
bytes.

## The thirty stories

Lead panels (large):

1. Asian stocks surge on Huang's return to Nvidia: Taiwan +9.1%, Nikkei +3.9%, KOSPI +6.5% (AP / Reuters)
2. Explosion kills 6, injures 10 in Hanoi (Reuters)
3. Russian attack on Zaporizhzhia kills 2, wounds 22 (Reuters)

Medium panels:

4. Suspected North Korean aircraft breaches South's airspace near Ulleung (The Times of India)
5. South Korea scrambles jets as Russian warplanes enter air zone (The Japan Times)
6. Solomon Islands to drop China security pact for Australia treaty (Reuters)
7. Sheikh Hasina plans return to Bangladesh on 16 December (Reuters)
8. Trump to meet NATO chief Rutte on Wednesday (Reuters)
9. Fourteen countries back ICJ Rohingya genocide ruling (Horizon)
10. UN chief seeks AI-risk framework within a year (Horizon)
11. States sue Musk firms over Grok sexualised images (AP)
12. Magnitude 5.6 earthquake strikes Nepal near China border (Horizon)
13. Pennsylvania measles outbreak claims ninth death (Horizon)
14. UN seeks probe after strike on Russian warship in Libya (iqmia)

One-line list ("Also on 24 November"): Israeli strikes in Gaza kill at
least three, including a UNRWA worker; Russia warns Estonia's moves are
"on verge of triggering open war"; Houthis say Saudi airstrike kills 17
in Hodeida; Iran flogs singer Parastoo Ahmadi with 74 lashes; Iran rules
out talks until US meets seven conditions; China opens Tiangong station
to first foreign astronaut; eleven die in UAE coach-truck crash; car
bomb destroys buildings in Villavicencio, Colombia; Indonesia charges
ex-police chief with treason; UN food agency warns wars put food aid
for 7.3 million more at risk; allies say Russia may launch nuclear
space weapon next month; Somalia and Uganda step up operations against
Al-Shabaab; Democrats flipped nine US Senate seats; Anthropic launches
Claude Ship; Greece reopens Acropolis Museum after seven-year
restoration; Commanders stun Bengals 22-20 on Monday Night Football.

## Submission layout

- `main.py` — the entry point. Standard-library only and self-contained:
  it draws the infographic itself (including its own bitmap font and PNG
  encoder) and writes it to `/output/entry.png`, byte-identical on
  every run, with no network access.
- `.makefun/owner.json` — claim file naming the linked Solana wallet
  that receives any reward.
