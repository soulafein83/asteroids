# Implementation Plan: Power-upy (blok P)

## Overview
Klasyczne arcade'owe power-upy: zniszczone skały z niewielką szansą wyrzucają
literkę **E** (extra pociski), **R** (rapid fire) lub **S** (tarcza). Statek
zbiera je przez kontakt; każdy efekt trwa 600 klatek (~10 s), ponowne
podniesienie przedłuża timer. Nowy moduł `src/item.py`, logika spawnu i
podnoszenia w `Asteroids`, efekty i cooldown strzału w `Ship`.

## Architecture Decisions
- **Nowy moduł `src/item.py`** — klasa `PowerUp(VectorSprite)`: literka,
  wolna dryfująca prędkość, TTL 900 klatek (15 s) z mruganiem na końcu,
  wrapowanie ekranu. Max 3 power-upy jednocześnie na ekranie.
- **Spawn** — `Asteroids.maybeSpawnPowerUp(position)`: 10% szansy per
  zniszczona skała, losowa literka z `E/R/S`, limit 3 na ekranie.
  Clear w `initialiseGame()`. Power-upy przetrwają `levelUp()`.
- **Podnoszenie** — w `checkCollisions()`: overlap rect statek↔power-up
  → `applyPowerUp(letter)`, usunięcie z listy i stage. Pociski NIE trafiają
  w power-upy (klasyka).
- **Efekty na `Ship`** — trzy timery (`shieldTimer`, `extraBulletsTimer`,
  `rapidFireTimer`), dekrementowane w `Ship.move()` (wzorzec W-5: logika w
  move(), nie w draw()).
  - **S**: `shieldTimer` → statek nietykalny (łączy się z istniejącym
    `safe = respawnTimer > 0`); rysowanie pierścienia wokół statku.
  - **E**: `maxBullets` 4 → 8. Zaimplementowane jako **property** na `Ship`
    (renaming atrybutu klasowego `maxBullets` → `baseMaxBullets`);
    `Shooter.fireBullet` bez zmian — czyta `self.maxBullets`.
  - **R**: cooldown strzału. Nowe: `baseFireCooldown = 10` klatek
    (baseline 6 strzałów/s — deterministyczne, arcade'owe), property
    `fireCooldown` → 3 klatek gdy R aktywny (20 strzałów/s).
    `Ship.fireBullet()` blokuje strzał gdy `cooldownTimer > 0` i ustawia
    `cooldownTimer = fireCooldown` po udanym strzale.
- **FONT_PATH** — przeniesiony z `asteroids.py` do `util/__init__.py`
  (razem z `RES_DIR`), żeby `item.py` mógł renderować literki fontem
  Hyperspace bez importu z `asteroids`.
- **HUD (P-5)** — rząd aktywnych liter w prawym górnym rogu (jak w
  oryginale), rysowany przez `displayPowerUps()` przy użyciu cache'owanych
  fontów (M-1).

## Task List

### Phase 1: Fundament
- [ ] Task P-1: moduł `src/item.py` — klasa `PowerUp` + `FONT_PATH` w util
- [ ] Task P-2: spawn power-upów z zniszczonych skał (Asteroids)

### Checkpoint: Fundament
- [ ] `py_compile` czysty, `python3 -m pytest` zielony, smoke EXIT=124
- [ ] commit + push

### Phase 2: Efekty
- [ ] Task P-3: podnoszenie + tarcza (S)
- [ ] Task P-4: extra pociski (E) + rapid fire (R) + baseline cooldown

### Checkpoint: Efekty
- [ ] wszystkie testy zielone (regresja: stare 46 + nowe)
- [ ] commit + push
- [ ] krótka sesja manualna: czy tempo ognia nie przeszkadza

### Phase 3: Oprawa
- [ ] Task P-5: HUD aktywnych power-upów + pierścień tarczy (gdy brak w P-3)

### Checkpoint: Complete
- [ ] pełny suite zielony, smoke zielony, commit + push
- [ ] manual check: gra działa, power-upy się pojawiają i działają

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Property `maxBullets` cieniuje atrybut klasowy | Med | `Shooter.fireBullet` tylko czyta; `Saucer`/inneShootery mają własne klasowe `maxBullets` — bez kolizji; testy regresji strzału |
| Baseline cooldown zmienia odczuwalne tempo ognia (OS key-repeat → 6/s) | Med | User-approved (decyzja z ankiety); checkpoint manualny po P-4 |
| Spawn losowy utrudnia testy | Low | monkeypatch `random.uniform`/`choice` w testach; deterministyczne ścieżki |
| Iteracja nad `rockList` + dodawanie power-upów w pętli `checkCollisions` | Low | power-upy trafiają do osobnej listy `powerUpList`, nie do `rockList` |

## Open Questions
- (zdecydowane w ankiecie) zestaw E+R+S; TTL 600 klatek z odświeżaniem;
  baseline cooldown 10 klatek, R → 3 klatek.
- Brak nowego pliku audio (pick-up) — opcja na później, jeśli gracz zechce.

---

# Plan: Power-up B — bomba (blok Q)

## Overview
Czwarta literka power-upu: **B** (bomba). Podniesienie natychmiast niszczy
wszystkie skały na ekranie ("wyczyść planszę"): punkty + debris za każdą,
bez podziału. Krótki flash literki B w HUD (30 klatek) sygnalizuje efekt.
Zakres: minimum — bez nowych dźwięków i statystyk.

## Architecture Decisions
- **Pool liter** — `powerUpLetters = "ERBS"`: B wchodzi do puli równo
  (szansa 1/4 w `maybeSpawnPowerUp`→`random.choice`). Kolejność HUD:
  S zostaje na prawym krańcu, B obok niej (iteracja `reversed`).
  Pętle `powerUpSurfaces` i `displayPowerUps()` są już generyczne —
  literka B renderuje się automatycznie.
- **Efekt** — nowa `Asteroids.explodeAllRocks()`: dla każdej skały w
  `rockList`: usunięcie z listy i stage, dźwięk + punkty jak przy trafieniu
  pociskiem (large 50 / medium 100 / small 200), `createDebris(rock)` oraz
  `maybeSpawnPowerUp` na pozycji skały (spójnie z inwariantem "zniszczona
  skała może upuścić power-up"). **Brak podziału** — bomba jest eksplozją
  końcową: large nie zostawia dwóch medium.
- **Pickup** — pętla power-upów w `checkCollisions()` rozgałęzia:
  "B" → `explodeAllRocks()`, E/R/S → `ship.applyPowerUp(letter)` (klasa
  `Ship` bez zmian — bomba to efekt globalny, nie stateku).
- **HUD** — timer `bombFlashTimer` na `Asteroids` (klasa
  `bombFlashTtl = 30`): ustawiany w `explodeAllRocks()`, dekrementowany w
  `playing()`, wpis w słowniku `timers` w `displayPowerUps()` — B jasna
  podczas flashu, przyciemniona poza nim. Inicjalizacja 0 w `__init__` +
  reset w `initialiseGame()`.
- **Efekty emergentne (bez specjalnej obsługi):**
  - bomba czyszczący ekran → `levelUp()` w tej samej klatce (istniejąca
    logika `playing()`: pusty `rockList` → kolejny poziom);
  - skała zniszczona bombą może upuścić power-up — w tym nową "B"
    (kaskadowa bomba; samolimitująco: cap 3, szansa 1/4);
  - saucer, pociski w locie i dryfujące power-upy — bez zmian.

## Task List
- **Q-1** — B w puli i HUD: `powerUpLetters = "ERBS"`,
  `bombFlashTimer = 0` w `__init__` + reset w `initialiseGame()`, wpis "B"
  w słowniku `timers` HUD (przyciemniona, jeszcze bez efektu).
- **Q-2** — efekt bomby: rozgałęzienie pickupu w `checkCollisions`,
  `explodeAllRocks()` (punkty, dźwięk, debris, hook spawnu, bez podziału),
  flash TTL + dekrement w `playing()`.

## Checkpoint: Complete (po Q-2)
- [ ] pełny suite zielony
- [ ] smoke EXIT=124
- [ ] atomic commit + push na fork
- [ ] manual: w grze podniesienie B czyści ekran i B zapala się w HUD

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Bomba + `levelUp` w tej samej klatce zmienia rozgrywkę | Low | zachowanie to identyczne z ręcznym zniszczeniem ostatniej skały — spójne; test Q-2 weryfikuje |
| Kaskadowe bomby (B upuszczone z bomby) | Low | samolimitująco (cap 3, 1/4); parametry do tuningu po playteście |
| Ponowne renderowanie B w HUD przy 4 literach zmienia region testów | Low | testy P-5 sprawdzają max jasność regionu 100 px — wystarczająco szeroki na 4 literki |
