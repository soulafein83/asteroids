# Tasks: Power-upy (blok P)

## Task P-1: moduł `src/item.py` — klasa `PowerUp`

**Description:** Nowy top-level moduł `src/item.py` z klasą
`PowerUp(VectorSprite)`: literka (E/R/S), wolna dryfująca prędkość losowana
przy spawnie, TTL 900 klatek z mruganiem (ostatnie 120 klatek), wrapowanie
ekranu, usunięcie ze stage po wygaśnięciu. Przeniesienie `FONT_PATH` z
`asteroids.py` do `util/__init__.py` (import w obu miejscach z `util`).

**Acceptance criteria:**
- [x] `PowerUp(stage, position, letter)` tworzy sprite z `ttl = 900` i małą losową prędkością
- [x] `move()` deinkrementuje `ttl`; przy `ttl <= 0` sprite usuwa się z `stage.spriteList` (bez ValueError)
- [x] pozycja wrapuje się przez krawędzie ekranu jak inne sprite'y
- [x] `draw()` renderuje literkę (font Hyperspace, 20 pt) i nie crashuje headless; mruganie przy niskim TTL

**Verification:**
- [x] `python3 -m py_compile src/item.py src/asteroids.py src/util/__init__.py`
- [x] `python3 -m pytest` — istniejące 46 testów + nowe testy P-1 zielone
- [x] smoke: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy timeout 5 python3 src/asteroids.py` → EXIT=124, bez tracebacku

**Dependencies:** None
**Files likely touched:** `src/item.py` (nowy), `src/util/__init__.py`, `src/asteroids.py` (import FONT_PATH), `tests/test_pf.py` (nowy)
**Estimated scope:** M (3-4 pliki)

## Task P-2: spawn power-upów z zniszczonych skał

**Description:** `Asteroids` dostaje `powerUpList` (inicjalizacja + clear w
`initialiseGame()`) i metodę `maybeSpawnPowerUp(position)`: 10% szansy,
losowa literka z E/R/S, limit 3 power-upów na ekranie. Hook w gałęzi
`rockHit` w `checkCollisions()`.

**Acceptance criteria:**
- [x] przy wymuszonej wygranej losowaniu spawnuje się PowerUp w pozycji skały (lista + spriteList)
- [x] przy przegranej losowaniu nic się nie spawnuje
- [x] z 3 power-upami na ekranie kolejny spawn jest ignorowany
- [x] `initialiseGame()` czyści `powerUpList` i usuwa sprite'y

**Verification:**
- [x] `python3 -m pytest` zielony (regresja + nowe testy spawnu)
- [x] smoke EXIT=124

**Dependencies:** P-1
**Files likely touched:** `src/asteroids.py`, `tests/test_pf.py`
**Estimated scope:** S (2 pliki)

## Task P-3: podnoszenie power-upów + tarcza (S)

**Description:** W `checkCollisions()` pętka nad `powerUpList` (kopia):
overlap statek↔power-up → `applyPowerUp(letter)` + usunięcie. `Ship` dostaje
timery `shieldTimer`, `extraBulletsTimer`, `rapidFireTimer`, `cooldownTimer`
(dekrement w `move()`). Tarcza: `safe` obejmuje `shieldTimer > 0` — statek
nie ginie od skał ani saucera. `Ship.draw()` rysuje pierścień tarczy gdy
aktywna.

**Acceptance criteria:**
- [ ] statek nakładający się na power-up S dostaje `shieldTimer = 600`; power-up znika z listy i stage
- [ ] z aktywną tarczą kolizja statek↔skała i statek↔saucer nie zabijają statku
- [ ] tarcza wygasa po 600 `move()`; statek znów śmiertelny
- [ ] ponowne podniesienie S przedłuża timer do 600
- [ ] draw z tarczą nie crashuje (headless)

**Verification:**
- [ ] `python3 -m pytest` zielony
- [ ] smoke EXIT=124

**Dependencies:** P-2
**Files likely touched:** `src/asteroids.py`, `src/ship.py`, `tests/test_pf.py`
**Estimated scope:** M (3 pliki)

## Task P-4: extra pociski (E) + rapid fire (R) + baseline cooldown

**Description:** `Ship`: `baseMaxBullets = 4`, property `maxBullets`
(8 gdy `extraBulletsTimer > 0`); `baseFireCooldown = 10`, property
`fireCooldown` (3 gdy `rapidFireTimer > 0`); `cooldownTimer` blokujący
strzał w `fireBullet()` i ustawiany po udanym strzale.

**Acceptance criteria:**
- [ ] baseline: po strzale kolejny możliwy dopiero po 10 klatkach (bez power-upów `maxBullets == 4`)
- [ ] E: `maxBullets == 8` przez 600 klatek, potem wraca do 4
- [ ] R: `fireCooldown == 3` przez 600 klatek, potem wraca do 10
- [ ] `Shooter.fireBullet` nadal honoruje limit (stary test regresji strzału przechodzi)

**Verification:**
- [ ] `python3 -m pytest` zielony (regresja 46 + nowe)
- [ ] smoke EXIT=124
- [ ] manual: tempo ognia 6/s nie przeszkadza (checkpoint)

**Dependencies:** P-3
**Files likely touched:** `src/ship.py`, `tests/test_pf.py`
**Estimated scope:** S (2 pliki)

## Task P-5: HUD aktywnych power-upów

**Description:** `Asteroids.displayPowerUps()`: rząd liter E/R/S w prawym
górnym rogu; aktywna jasna, nieaktywna przyciemniona; renderowanie przez
cache'owane fonty (M-1) — statyczne surface w `__init__`, blit per frame.

**Acceptance criteria:**
- [ ] metoda nie crashuje headless przy każdym stanie timerów
- [ ] wywoływana w pętli gry (stan playing)
- [ ] statyczne surface w `__init__` (bez per-frame renderu)

**Verification:**
- [ ] `python3 -m pytest` zielony
- [ ] smoke EXIT=124
- [ ] manual: rząd liter widać w prawym górnym rogu

**Dependencies:** P-3
**Files likely touched:** `src/asteroids.py`, `tests/test_pf.py`
**Estimated scope:** S (2 pliki)

## Checkpoint: Fundament (po P-1, P-2)
- [ ] `py_compile` czysty
- [ ] `python3 -m pytest` zielony (46 + nowe)
- [ ] smoke EXIT=124
- [ ] atomic commit + push na fork

## Checkpoint: Efekty (po P-3, P-4)
- [ ] pełny suite zielony
- [ ] smoke EXIT=124
- [ ] atomic commit + push na fork
- [ ] manual: tempo ognia + tarcza w grze

## Checkpoint: Complete (po P-5)
- [ ] pełny suite zielony
- [ ] smoke EXIT=124
- [ ] atomic commit + push na fork
- [ ] manual: power-upy w akcji (spawn, pickup, HUD, tarcza)
