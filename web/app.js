'use strict';

// ============================================================
// SECTION 1 — BIP-39 word list (2048 words, English)
// Used to generate and validate 12-word seed phrases locally.
// ============================================================
const BIP39 = "abandon ability able about above absent absorb abstract absurd abuse access accident account accuse achieve acid acoustic acquire across act action actor actress actual adapt add addict address adjust admit adult advance advice aerobic afford afraid again age agent agree ahead aim air airport aisle alarm album alcohol alert alien all alley allow almost alone alpha already also alter always amateur amazing among amount amused analyst anchor ancient anger angle angry animal ankle announce annual another answer antenna antique anxiety any apart apology appear apple approve april arch arctic area arena argue arm armed armor army around arrange arrest arrive arrow art artefact artist artwork ask aspect assault asset assist assume asthma athlete atom attack attend attitude attract auction audit august aunt author auto autumn average avocado avoid awake aware away awesome awful awkward axis baby bachelor bacon badge bag balance balcony ball bamboo banana banner bar barely bargain barrel base basic basket battle beach bean beauty because become beef before begin behave behind believe below belt bench benefit best betray better between beyond bicycle bid bike bind biology bird birth bitter black blade blame blanket blast bleak bless blind blood blossom blouse blue blur blush board boat body boil bomb bone book boost border boring borrow boss bottom bounce box boy bracket brain brand brave breeze brick bridge brief bright bring brisk broccoli broken bronze broom brother brown brush bubble buddy budget buffalo build bulb bulk bullet bundle bunker burden burger burst bus business busy butter buyer buzz cabbage cabin cable cactus cage cake call calm camera camp can canal cancel candy cannon canvas canyon capable capital captain car carbon card cargo carpet carry cart case cash casino castle casual cat catalog catch category cattle cause caution cave ceiling celery cement census chair chaos chapter charge chase chat cheap check cheese chef cherry chest chicken chief child chimney choice choose chronic chuckle chunk cigar cinnamon circle citizen city civil claim clap clarify claw clay clean clerk clever click client cliff climb clinic clip clock clog close cloth cloud clown club clump cluster clutch coach coast coconut code coffee coil coin collect color column combine come comfort comic common company concert conduct confirm congress connect consider control convince cook cool copper copy coral core corn correct cost cotton couch country couple course cousin cover coyote crack cradle craft cram crane crash crater crawl crazy cream credit creek crew cricket crime crisp critic cross crouch crowd crucial cruel cruise crumble crunch crush cry crystal cube culture cup cupboard curious current curtain curve cushion custom cute cycle dad damage damp dance danger daring dash daughter dawn day deal debate debris decade december decide decline decorate decrease deer defense define defy degree delay deliver demand demise denial dentist deny depart depend deposit depth deputy derive describe desert design desk despair destroy detail detect develop device devote diagram dial diamond diary dice diesel diet differ digital dignity dilemma dinner dinosaur direct dirt disagree discover disease dish dismiss disorder display distance divert divide divorce dizzy doctor document dog doll dolphin domain donate donkey donor door dose double dove draft dragon drama drastic draw dream dress drift drill drink drip drive drop drum dry duck dumb dune during dust dutch duty dwarf dynamic eager eagle early earn earth easily east easy echo ecology edge edit educate effort egg eight either elbow elder electric elegant element elephant elevator elite else embark embody embrace emerge emotion employ empower empty enable enact endless endorse enemy engage engine enhance enjoy enlist enough enrich enroll ensure enter entire entry envelope episode equal equip erase erase erosion errupt escape essay essence estate eternal ethics evidence evil evoke evolve exact example excess exchange excite exclude exercise exhaust exhibit exile exist exit exotic expand expire explain expose express extend extra eye fable face faculty fade faint faith fall false fame family famous fan fancy fantasy far fashion fat fatal father fatigue fault favorite feature february federal fee feed feel feet fellow felt fence festival fetch fever few fiber fiction field figure file film filter final find fine finger finish fire firm first fiscal fish fit fitness fix flag flame flash flat flavor flee flight flip float flock floor flower fluid flush fly foam focus fog foil follow food force forest forget fork fortune forum forward fossil foster found fox fragile frame frequent fresh friend fringe frog front frost frown frozen fruit fuel fun funny furnace fury future gadget gain galaxy gallery game gap garbage garden garlic garment gasp gate gather gauge gaze general genius genre gentle genuine gesture ghost giant gift giggle ginger giraffe girl give glad glance glare glass glide glimpse globe gloom glory glove glow glue goat goddess gold good goose gorilla gospel gossip govern gown grab grace grain grant grape grasp grass gravity great green grid grief grit grocery group grow grunt guard guide guilt guitar gun gym habit hair half hamster hand happy harsh harvest hat have hawk hazard head health heart heavy hedgehog height hello helmet help hero hidden high hill hint hip hire history hobby hockey hold hole holiday hollow home honey hood hope horn hospital host hour hover hub huge human humble humor hundred hungry hunt hurdle hurry hurt husband hybrid ice icon ignore ill illegal image imitate immense immune impact impose improve impulse inbox income increase index indicate indoor industry infant inflict inform inhale inject inner innocent input inquiry insane insect inside inspire install intact interest into invest invite involve iron island isolate issue item ivory jacket jaguar jar jazz jealous jeans jelly jewel job join joke journey joy judge juice jump jungle junior junk just kangaroo keen keep ketchup key kick kid kingdom kiss kit kitchen kite kitten kiwi knee knife knock know lab ladder lady lake lamp language laptop large later laugh laundry lava law lawn lawsuit layer lazy leader learn leave lecture left leg legal legend leisure lemon lend length lens leopard lesson letter level liar liberty library license life lift light like limb limit link lion liquid list little live lizard load loan lobster local lock logic lonely long loop lottery loud lounge love loyal lucky luggage lumber lunar lunch luxury lyrics machine mad magic magnet maid main major make mammal mango mansion manual maple marble march margin marine market marriage mask master match material math matrix matter maximum maze meadow mean medal media melody melt member memory mention mentor menu mercy merge merit merry mesh message metal method middle midnight milk million mimic mind minimum minor minute miracle miss mixed mixture mobile model modify mom monitor monkey monster month moon moral more morning mosquito mother motion motor mountain mouse move movie much muffin mule multiply muscle museum mushroom music must mutual myself mystery naive name napkin narrow nasty nature near neck need negative neglect neither nephew nerve nest network neutral never news next nice night noble noise nominee noodle normal north notable note nothing notice novel now nuclear nurse nut oak obey object oblige obscure obtain ocean october odor off offer office often oil okay old olive olympic omit once onion open oppose option orange orbit orchard order ordinary organ orient original orphan ostrich other outdoor outside oval over own oyster ozone pact paddle page pair palace palm panda panel panic panther paper parade parent park parrot party pass patch path patrol pause pave payment peace peanut peasant pelican pen penalty pencil people pepper perfect permit person pet phone photo phrase physical piano picnic picture piece pig pigeon pill pilot pink pioneer pipe pistol pitch pizza place planet plastic plate play please pledge pluck plug plunge poem poet point polar pole police pond pony popular portion position possible post potato pottery poverty powder power practice praise predict prefer prepare present pretty prevent price pride primary print priority prison private prize problem process produce profit program project promote proof property prosper protect proud provide public pudding pull pulp pulse pumpkin punish pupil puppy purchase purity purpose push put puzzle pyramid quality quantum quarter question quick quit quiz quote rabbit raccoon race rack radar radio rage rail rain raise rally ramp ranch random range rapid rare rate rather raven reach ready real reason rebel rebuild recall receive recipe record recycle reduce reflect reform refuse region regret regular reject relax release relief rely remain remember remind remove render renew rent reopen repair repeat replace report require rescue resemble resist resource response result retire retreat return reunion reveal review reward rhythm ribbon rice rich ride ridge rifle right rigid ring riot ripple risk ritual rival river road roast robot robust rocket romance roof rooster rose rotate rough round route royal rubber rude rug rule run runway rural sad saddle sadness safe sail salad salmon salon salt salute same sample sand satisfy satoshi sauce sausage save say scale scan scare scatter scene scheme school science scissors scorpion scout scrap screen script scrub search season seat second secret section security seek segment select sell seminar senior sense sentence series service session settle setup seven shadow shaft shallow share shed shell sheriff shield shift shine ship shiver shock shoe shoot shop short shoulder shove shrimp shrug shuffle shy sibling siege sight sign silent silk silly silver similar simple since sing siren sister situate six size ski skill skin skirt skull slab slam sleep slender slice slide slight slim slogan slot slow slush small smart smile smoke smooth snack snake snap sniff snow soap soccer social sock solar soldier solid solution solve someone song soon sorry soul sound soup source south space spare spatial spawn speak special speed spell spend sphere spice spider spike spin spirit split spoil sponsor spoon spray spread spring spy square squeeze squirrel stable stadium staff stage stairs stamp stand start state stay steak steel stem step stereo stick still sting stock stomach stone stop store storm story stove strategy street strike strong struggle student stuff stumble style subject submit subway success such sudden suffer sugar suggest suit summer sun sunny sunset super supply supreme sure surface surge surprise sustain swallow swamp swap swear sweet swift swim swing switch sword symbol symptom syrup table tackle tag tail talent tamper tank tape target task tattoo taxi teach team tell ten tenant tennis tent term test text thank that theme then theory there they thing this thought three thrive throw thumb thunder ticket tilt timber time tiny tip tired title toast tobacco today together toilet token tomato tomorrow tone tongue tonight tool tooth top topic topple torch tornado tortoise toss total tourist toward tower town toy track trade traffic tragic train transfer trap trash travel tray treat tree trend trial tribe trick trigger trim trip trophy trouble truck truly trumpet trust truth tube tuition tumble tuna tunnel turkey turn turtle twelve twenty twice twin twist two type typical ugly umbrella unable unaware uncle uncover under undo unfair unfold unhappy uniform unique universe unknown unlock until unusual unwrap update upgrade uphold upon upper upset urban usage use used useful useless usual utility vacant vacuum vague valid valley valve van vanish vapor various vast vault vehicle velvet vendor venture venue verb verify version very vessel veteran viable vibrant vicious victory video view village vintage violin virtual virus visa visit visual vital vivid vocal voice void volcano volume vote voyage wage wagon wait walk wall walnut want warfare warm warrior wash wasp waste water wave way wealth weapon wear weasel weather web_old wedding weekend weird welcome well west wet whale wheat wheel when where whip whisper wide width wife wild will win window wine wing wink winner winter wire wisdom wise wish witness wolf woman wonder wood wool word world worry worth wrap wreck wrestle wrist write wrong yard year yellow you young youth zebra zero zone zoo";
const WORDS = BIP39.split(' ');

// ============================================================
// SECTION 2 — Crypto helpers
//
// NOTE ON THE CURVE: the node (wallet/wallet.py) uses secp256k1, and
// browsers do NOT implement secp256k1 in native WebCrypto (only the
// NIST curves P-256/P-384/P-521 are supported there). So elliptic-curve
// math is done with @noble/curves — a widely used, audited, dependency-
// free JS implementation — while SHA-256/PBKDF2/AES-GCM still use the
// browser's native, faster SubtleCrypto.
//
// (The previous version of this file tried to do everything through
// SubtleCrypto with a P-256 curve, and used
// `crypto.subtle.importKey('raw', bits, {name:'ECDSA', namedCurve:'P-256'}, true, ['sign'])`
// to build a private key from raw seed material. This is invalid per the
// WebCrypto spec — 'raw' import for EC keys is public-key-only — so every
// call threw a SyntaxError and wallet creation/recovery silently failed.)
// ============================================================

let _secp256k1Promise = null;
function getSecp256k1() {
  if (!_secp256k1Promise) {
    _secp256k1Promise = import('https://esm.sh/@noble/curves@2.2.0/secp256k1.js')
      .then(m => m.secp256k1);
  }
  return _secp256k1Promise;
}

function _bytesToHex(bytes) {
  return Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
}
function _hexToBytes(hex) {
  return Uint8Array.from(hex.match(/../g).map(h => parseInt(h, 16)));
}

// Generate a random 12-word recovery phrase using browser entropy.
function generateSeedPhrase() {
  const words = [];
  const unbiasedRange = 65536 - (65536 % WORDS.length);
  while (words.length < 12) {
    const random = new Uint16Array(1);
    crypto.getRandomValues(random);
    if (random[0] < unbiasedRange) words.push(WORDS[random[0] % WORDS.length]);
  }
  return words.join(' ');
}

// Derive a deterministic secp256k1 key pair from a seed phrase.
// Flow: seed phrase → PBKDF2(SHA-256, 100k iters) → 32-byte scalar
//       → secp256k1 private/public key pair (same curve the node uses).
async function seedToKeyPair(phrase) {
  const enc  = new TextEncoder();
  const base = await crypto.subtle.importKey(
    'raw', enc.encode(phrase.trim()), { name: 'PBKDF2' }, false, ['deriveBits']
  );
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt: enc.encode('helix-wallet-v1'), iterations: 100000, hash: 'SHA-256' },
    base, 256
  );
  const privateKey = new Uint8Array(bits); // 32-byte scalar
  const secp256k1  = await getSecp256k1();
  const publicKey  = secp256k1.getPublicKey(privateKey, true); // compressed, 33 bytes
  return { privateKey, publicKey };
}

// Derive wallet address exactly the way the node does it (wallet/wallet.py
// generate_address): SHA-256 of the *compressed* SEC1 public key point,
// first 40 hex chars.
async function publicKeyToAddress(publicKeyCompressed) {
  const hash = await crypto.subtle.digest('SHA-256', publicKeyCompressed);
  return _bytesToHex(new Uint8Array(hash)).slice(0, 40);
}

// Fixed ASN.1 DER prefix for a secp256k1 SubjectPublicKeyInfo header
// (SEQUENCE { SEQUENCE { OID ecPublicKey, OID secp256k1 } BIT STRING }),
// followed by the 65-byte uncompressed point (0x04 || X || Y). This
// reproduces byte-for-byte what Python's `cryptography` library emits for
// serialization.PublicFormat.SubjectPublicKeyInfo on a secp256k1 key —
// verified against it directly.
const SECP256K1_SPKI_PREFIX_HEX = '3056301006072a8648ce3d020106052b8104000a034200';

// Export public key as PEM (SubjectPublicKeyInfo / SPKI format), parseable
// by Python's serialization.load_pem_public_key().
async function exportPublicKeyPEM(publicKeyCompressed) {
  const secp256k1    = await getSecp256k1();
  const Point        = secp256k1.Point || secp256k1.ProjectivePoint;
  const uncompressed = Point.fromHex(_bytesToHex(publicKeyCompressed)).toBytes(false);
  const der          = _hexToBytes(SECP256K1_SPKI_PREFIX_HEX + _bytesToHex(uncompressed));
  const b64           = btoa(String.fromCharCode(...der));
  const lines         = b64.match(/.{1,64}/g).join('\n');
  return `-----BEGIN PUBLIC KEY-----\n${lines}\n-----END PUBLIC KEY-----\n`;
}

// Sign transaction data: returns hex-encoded DER signature.
// The payload must match Python's compact json.dumps(sort_keys=True) exactly.
function transactionPayload(sender, receiver, amount) {
  const amt = parseInt(amount);
  // Match Python json.dumps(sort_keys=True, separators=(",", ":")).
  return JSON.stringify({ amount: amt, receiver, sender });
}

// Equivalent to Python json.dumps(sort_keys=True, separators=(",", ":")).
// Token signatures use more fields than a normal HLX transfer.
function canonicalJson(value) {
  const sortValue = item => {
    if (Array.isArray(item)) return item.map(sortValue);
    if (item && typeof item === 'object') {
      return Object.keys(item).sort().reduce((result, key) => {
        result[key] = sortValue(item[key]);
        return result;
      }, {});
    }
    return item;
  };
  return JSON.stringify(sortValue(value)).replace(/[\u007f-\uffff]/g, char =>
    `\\u${char.charCodeAt(0).toString(16).padStart(4, '0')}`);
}

async function signPayload(privateKey, payload) {
  const secp256k1 = await getSecp256k1();
  const derSig = secp256k1.sign(
    new TextEncoder().encode(canonicalJson(payload)), privateKey, { format: 'der' });
  return _bytesToHex(derSig);
}

async function tokenMintAddress(creator, nonce) {
  const enc = new TextEncoder();
  const mintHash = await crypto.subtle.digest(
    'SHA-256', enc.encode(`helix-token-mint:${creator}:${nonce}`));
  return _bytesToHex(new Uint8Array(mintHash)).slice(0, 40);
}

async function signTransaction(privateKey, sender, receiver, amount) {
  const payload  = transactionPayload(sender, receiver, amount);
  const enc      = new TextEncoder();
  const secp256k1 = await getSecp256k1();
  // prehash defaults to true, i.e. it signs sha256(payload) — matching
  // Python's ec.ECDSA(hashes.SHA256()) exactly.
  const derSig = secp256k1.sign(enc.encode(payload), privateKey, { format: 'der' });
  return _bytesToHex(derSig);
}

// ============================================================
// SECTION 3 — Local wallet storage (AES-GCM encrypted localStorage)
// ============================================================

const WALLET_STORE_KEY = 'hlx_wallets_v1';
const WALLET_KDF_ITERATIONS = 600000;

function _loadStore() {
  try { return JSON.parse(localStorage.getItem(WALLET_STORE_KEY) || '{}'); }
  catch { return {}; }
}
function _saveStore(store) {
  localStorage.setItem(WALLET_STORE_KEY, JSON.stringify(store));
}

// Derive AES-GCM key from password using PBKDF2
async function _passwordToAesKey(password, saltHex, iterations = 100000) {
  const enc  = new TextEncoder();
  const salt = Uint8Array.from(saltHex.match(/../g).map(h => parseInt(h, 16)));
  const base = await crypto.subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveKey']);
  return crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt, iterations, hash: 'SHA-256' },
    base, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']
  );
}

function _hexRandom(bytes) {
  const arr = new Uint8Array(bytes);
  crypto.getRandomValues(arr);
  return Array.from(arr).map(b => b.toString(16).padStart(2,'0')).join('');
}

// Save a wallet entry — stores: address, AES-GCM-encrypted private key
// (hex scalar), public key (hex, not secret), salt, iv. Nothing here ever
// leaves the browser — this function only writes to localStorage.
async function saveWallet(name, password, privateKey, publicKey, seedPhrase) {
  const store   = _loadStore();
  const saltHex = _hexRandom(16);
  const ivHex   = _hexRandom(12);
  const seedIvHex = _hexRandom(12);
  const iv      = _hexToBytes(ivHex);
  const seedIv  = _hexToBytes(seedIvHex);
  const aesKey  = await _passwordToAesKey(password, saltHex, WALLET_KDF_ITERATIONS);
  const enc     = new TextEncoder();
  const cipher  = await crypto.subtle.encrypt({ name:'AES-GCM', iv }, aesKey, enc.encode(_bytesToHex(privateKey)));
  const address = await publicKeyToAddress(publicKey);
  store[name] = {
    address,
    pubHex: _bytesToHex(publicKey),
    saltHex,
    ivHex,
    seedIvHex,
    kdfIterations: WALLET_KDF_ITERATIONS,
    cipherHex: _bytesToHex(new Uint8Array(cipher)),
    // Store encrypted seed phrase too for recovery display
    seedCipherHex: await _encryptString(seedPhrase, aesKey, seedIv),
  };
  _saveStore(store);
}

async function _encryptString(str, aesKey, iv) {
  const enc    = new TextEncoder();
  const cipher = await crypto.subtle.encrypt({ name:'AES-GCM', iv }, aesKey, enc.encode(str));
  return Array.from(new Uint8Array(cipher)).map(b=>b.toString(16).padStart(2,'0')).join('');
}

async function _decryptString(cipherHex, aesKey, iv) {
  const cipher = _hexToBytes(cipherHex);
  const plain = await crypto.subtle.decrypt({ name:'AES-GCM', iv }, aesKey, cipher);
  return new TextDecoder().decode(plain);
}

// Load and decrypt a wallet — returns { privateKey, publicKey, address } or null on bad password
async function loadWallet(name, password) {
  const store = _loadStore();
  const entry = store[name];
  if (!entry) return null;
  try {
    // Records created before kdfIterations was added remain readable at their
    // original work factor and are upgraded whenever they are overwritten.
    const iterations = entry.kdfIterations === undefined ? 100000 : Number(entry.kdfIterations);
    if (!Number.isInteger(iterations) || iterations < 100000 || iterations > 1000000) return null;
    const aesKey = await _passwordToAesKey(password, entry.saltHex, iterations);
    const iv     = Uint8Array.from(entry.ivHex.match(/../g).map(h=>parseInt(h,16)));
    const cipher = Uint8Array.from(entry.cipherHex.match(/../g).map(h=>parseInt(h,16)));
    const plain      = await crypto.subtle.decrypt({ name:'AES-GCM', iv }, aesKey, cipher);
    const privateKey = _hexToBytes(new TextDecoder().decode(plain));
    const publicKey  = _hexToBytes(entry.pubHex);
    if (iterations < WALLET_KDF_ITERATIONS || !entry.seedIvHex) {
      try {
        const oldSeedIv = entry.seedIvHex ? _hexToBytes(entry.seedIvHex) : iv;
        const seedPhrase = await _decryptString(entry.seedCipherHex, aesKey, oldSeedIv);
        await saveWallet(name, password, privateKey, publicKey, seedPhrase);
      } catch (_) {
        // A legacy seed backup should not prevent access to a valid private key.
      }
    }
    return { privateKey, publicKey, address: entry.address, name };
  } catch { return null; }
}

function listWalletNames() {
  return Object.keys(_loadStore());
}

function walletExists(name) {
  return name in _loadStore();
}

function deleteWalletRecord(name) {
  const store = _loadStore();
  if (!Object.prototype.hasOwnProperty.call(store, name)) return false;
  delete store[name];
  _saveStore(store);
  return true;
}

// Overwrite an existing wallet entry's encryption (used by recover)
async function overwriteWallet(name, password, privateKey, publicKey, seedPhrase) {
  return saveWallet(name, password, privateKey, publicKey, seedPhrase);
}

// Download the wallet's encrypted record as a portable backup file. The file
// stays password-protected — it is the same ciphertext held in localStorage,
// so it can be restored on any device but is useless without the password.
function downloadWalletBackup(name) {
  const entry = _loadStore()[name];
  if (!entry) return false;
  const payload = {
    type: 'helix-wallet-backup',
    version: 1,
    name,
    address: entry.address,
    exported_at: new Date().toISOString(),
    entry,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `helix-wallet-${name.replace(/[^a-z0-9_-]+/gi, '_')}.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  return true;
}

// Load a backup file back into local storage. Validates the structure but
// never needs the password here — the record stays encrypted until unlocked.
async function importWalletBackup(file, preferredName) {
  let data;
  try { data = JSON.parse(await file.text()); }
  catch { throw new Error('That file is not valid JSON.'); }
  const entry = data && data.entry;
  if (!data || data.type !== 'helix-wallet-backup' || !entry || typeof entry !== 'object') {
    throw new Error('That does not look like a Helix wallet backup file.');
  }
  for (const field of ['address', 'pubHex', 'saltHex', 'ivHex', 'cipherHex']) {
    if (typeof entry[field] !== 'string' || !entry[field]) {
      throw new Error('The backup file is missing required wallet data.');
    }
  }
  const name = (preferredName || data.name || '').trim();
  if (!name) throw new Error('Enter a name for the restored wallet.');
  const store = _loadStore();
  if (store[name]) throw new Error(`A wallet named "${name}" already exists here. Choose a different name.`);
  store[name] = entry;
  _saveStore(store);
  return name;
}

// ============================================================
// SECTION 4 — Node connection
// ============================================================
const CANDIDATE_PORTS = [8000, 8001, 8002, 8003, 8004, 8005];
const LOCAL_HOSTS = new Set(['localhost', '127.0.0.1', '::1']);

function _buildCandidates() {
  // A deployed Pages site talks to the bundled same-origin Worker gateway.
  // Local development keeps direct node discovery for ports 8000-8005.
  if (!LOCAL_HOSTS.has(window.location.hostname)) {
    return [`${window.location.origin}/api`];
  }

  const list = [window.location.origin];
  const host = window.location.hostname || 'localhost';
  for (const port of CANDIDATE_PORTS) {
    const url = `http://${host}:${port}`;
    if (!list.includes(url)) list.push(url);
  }
  return list;
}

let NODE_URL = null;
let _connectPromise = null;

async function connectToNode() {
  if (_connectPromise) return _connectPromise;
  _connectPromise = (async () => {
    const candidates = _buildCandidates();
    for (const url of candidates) {
      try {
        const r = await fetch(url + '/chain', { method:'GET', signal: AbortSignal.timeout(1500) });
        if (r.ok) {
          const data = await r.json();
          if ('chain' in data) {
            NODE_URL = url;
            setNodeStatus('connected', NODE_URL);
            return NODE_URL;
          }
        }
      } catch (_) {}
    }
    setNodeStatus('offline', null);
    return null;
  })();
  return _connectPromise;
}

function setNodeStatus(state, url) {
  const banner = document.getElementById('node-banner');
  const dot    = document.getElementById('banner-dot');
  const text   = document.getElementById('banner-text');
  if (state === 'connected') {
    dot.style.background = 'var(--green)';
    dot.style.animation  = '';
    text.textContent = `Connected to node at ${url}`;
    banner.style.display = 'flex';
    clearTimeout(banner._t);
    banner._t = setTimeout(() => { banner.style.display = 'none'; }, 3000);
  } else {
    dot.style.background = 'var(--red)';
    dot.style.animation  = '';
    text.replaceChildren(document.createTextNode('No Helix node found. Start the node then '));
    const retry = document.createElement('button');
    retry.type = 'button';
    retry.className = 'btn-link';
    retry.textContent = 'retry';
    retry.addEventListener('click', retryConnect);
    text.append(retry, document.createTextNode('.'));
    banner.style.display = 'flex';
  }
}

async function retryConnect() {
  _connectPromise = null;
  NODE_URL = null;
  document.getElementById('banner-text').textContent = 'Searching for node…';
  await connectToNode();
}

async function api(method, path, body) {
  if (!NODE_URL) await connectToNode();
  if (!NODE_URL) throw new Error('No node available');
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const r = await fetch(NODE_URL + path, opts);
  const data = await r.json().catch(() => ({ message: `HTTP ${r.status}` }));
  if (!r.ok) throw new Error(data.message || data.detail || `HTTP ${r.status}`);
  return data;
}

// ============================================================
// SECTION 5 — Session state
// ============================================================
// S holds the live decrypted key objects. sessionStorage keeps a tab-scoped
// copy for refresh recovery and clears it on lock or after one hour.
let S = null; // { name, address, privateKey, publicKey }
const SESSION_STORAGE_KEY = 'hlx_session_v2';
const SESSION_LIFETIME_MS = 60 * 60 * 1000;
let _sessionExpiryTimer = null;
let _sessionExpiresAt = 0;

function clearSessionRecord() {
  sessionStorage.removeItem(SESSION_STORAGE_KEY);
  // Remove the name-only record written by older versions too.
  sessionStorage.removeItem('hlx_session');
  clearTimeout(_sessionExpiryTimer);
  _sessionExpiryTimer = null;
  _sessionExpiresAt = 0;
}

function scheduleSessionExpiry(expiresAt) {
  clearTimeout(_sessionExpiryTimer);
  _sessionExpiresAt = expiresAt;
  const remaining = expiresAt - Date.now();
  if (remaining <= 0) {
    lockWallet('Session expired', 'Your one-hour session expired. Unlock your wallet to continue.');
    return;
  }
  _sessionExpiryTimer = setTimeout(() => {
    lockWallet('Session expired', 'Your one-hour session expired. Unlock your wallet to continue.');
  }, remaining);
}

function hasActiveSession() {
  if (!S) return false;
  if (!_sessionExpiresAt || Date.now() >= _sessionExpiresAt) {
    lockWallet('Session expired', 'Your one-hour session expired. Unlock your wallet to continue.');
    return false;
  }
  return true;
}

function persistSession() {
  const expiresAt = Date.now() + SESSION_LIFETIME_MS;
  // Private keys are NEVER stored. We keep only a non-sensitive breadcrumb (the
  // wallet name) so the unlock form can pre-fill after a page refresh; the user
  // re-enters their password, which decrypts the key held in localStorage. The
  // decrypted key exists only in memory while the wallet is unlocked.
  sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify({
    name: S.name,
    expiresAt,
  }));
  scheduleSessionExpiry(expiresAt);
}

async function restoreSession() {
  const raw = sessionStorage.getItem(SESSION_STORAGE_KEY);
  clearSessionRecord();
  if (!raw) return false;
  try {
    const saved = JSON.parse(raw);
    const expiresAt = Number(saved.expiresAt);
    if (typeof saved.name === 'string' && _loadStore()[saved.name]
        && Number.isFinite(expiresAt) && expiresAt > Date.now()) {
      // No key is stored, so we cannot silently restore the unlocked wallet;
      // pre-fill the name and require the password again.
      switchToLoginTab(saved.name, 'Unlock your wallet to continue.');
    }
  } catch (_) {}
  return false;
}

// ============================================================
// SECTION 6 — UI helpers
// ============================================================
function toast(msg, type = 'ok') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'show ' + type;
  clearTimeout(el._t);
  el._t = setTimeout(() => el.className = '', 3500);
}

function setAlert(id, message, type = 'err') {
  const el = document.getElementById(id);
  el.replaceChildren();
  if (!message) return;
  const alert = document.createElement('div');
  alert.className = `alert alert-${type === 'ok' ? 'ok' : type === 'info' ? 'info' : 'err'}`;
  alert.textContent = String(message);
  el.appendChild(alert);
}

function copyEl(id) {
  navigator.clipboard.writeText(document.getElementById(id).textContent.trim())
    .then(() => toast('Copied!'))
    .catch(() => toast('Copy failed', 'err'));
}

document.querySelectorAll('[data-copy-id]').forEach(button => {
  button.addEventListener('click', () => copyEl(button.dataset.copyId));
});

function short(addr) {
  if (!addr || addr === 'SYSTEM') return addr || '—';
  return addr.slice(0,8) + '…' + addr.slice(-6);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[char]);
}

function fmtDate(ts) {
  return ts ? new Date(ts * 1000).toLocaleString() : '';
}

function transactionDetailRow(label, value, rawHtml = false) {
  const shown = value === null || value === undefined || value === '' ? '—' : value;
  return `<div class="detail-label">${escapeHtml(label)}</div><div class="detail-value">${rawHtml ? shown : escapeHtml(shown)}</div>`;
}

function closeTransactionDetails() {
  const modal = document.getElementById('tx-modal');
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden', 'true');
}

async function openTransactionDetails(txId) {
  if (!txId) return;
  const modal = document.getElementById('tx-modal');
  const body = document.getElementById('tx-modal-body');
  body.innerHTML = '<div class="empty">Loading transaction&hellip;</div>';
  modal.classList.add('open');
  modal.setAttribute('aria-hidden', 'false');
  document.getElementById('btn-close-tx-modal').focus();

  try {
    const detail = await api('GET', `/transaction/${encodeURIComponent(txId)}`);
    if (!detail.transaction) throw new Error(detail.message || 'Transaction not found');
    const tx = detail.transaction;
    const status = detail.status || (detail.block === null ? 'pending' : 'confirmed');
    const badge = `<span class="status-badge ${status === 'pending' ? 'pending' : 'confirmed'}">${escapeHtml(status)}</span>`;
    const isToken = tx.tx_type && tx.tx_type !== 'transfer';
    const amountDisplay = tx.tx_type === 'token_buy' ? `${tx.amount} HLX spent`
      : tx.tx_type === 'token_pool_add_hlx' ? `${tx.amount} HLX added`
      : isToken ? `${tx.amount} token base units` : `${tx.amount} HLX`;
    const tokenRows = isToken ? `
      ${transactionDetailRow('Transaction type', tx.tx_type)}
      ${transactionDetailRow('MNT address', tx.mint_address)}
      ${transactionDetailRow('Operation nonce', tx.nonce)}
      ${transactionDetailRow('DAD authority', tx.dad_address)}
      ${transactionDetailRow('Token name', tx.name)}
      ${transactionDetailRow('Token symbol', tx.symbol)}
      ${transactionDetailRow('Description', tx.description)}
      ${transactionDetailRow('Image URL', tx.image)}
      ${transactionDetailRow('Metadata hash', tx.metadata_hash)}
      ${transactionDetailRow('Decimals', tx.decimals)}
      ${transactionDetailRow('Metadata URI', tx.uri)}
      ${transactionDetailRow('HLX liquidity', tx.hlx_amount)}
      ${transactionDetailRow('Target MNT address', tx.target_mint_address)}
      ${transactionDetailRow('Minimum received', tx.min_receive)}` : '';
    body.innerHTML = `<div class="detail-grid">
      ${transactionDetailRow('Status', badge, true)}
      ${transactionDetailRow('Transaction ID', tx.id)}
      ${transactionDetailRow('Amount', amountDisplay)}
      ${tokenRows}
      ${transactionDetailRow('Sender', tx.sender)}
      ${transactionDetailRow('Receiver', tx.receiver)}
      ${transactionDetailRow('Block height', detail.block)}
      ${transactionDetailRow('Confirmations', detail.confirmations)}
      ${transactionDetailRow('Timestamp', fmtDate(detail.timestamp))}
      ${transactionDetailRow('Block hash', detail.block_hash)}
      ${transactionDetailRow('Signature', tx.signature)}
      ${transactionDetailRow('Public key', tx.public_key)}
    </div>`;
  } catch (error) {
    body.innerHTML = `<div class="alert alert-err">${escapeHtml(error.message || 'Could not load transaction details.')}</div>`;
  }
}

document.getElementById('btn-close-tx-modal').addEventListener('click', closeTransactionDetails);
document.getElementById('tx-modal').addEventListener('click', event => {
  if (event.target.id === 'tx-modal') closeTransactionDetails();
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') closeTransactionDetails();
  if (event.target.closest?.('[data-cancel-tx-id]')) return;
  const row = event.target.closest?.('[data-tx-id]');
  if (row && (event.key === 'Enter' || event.key === ' ')) {
    event.preventDefault();
    openTransactionDetails(row.dataset.txId);
  }
});
document.addEventListener('click', event => {
  if (event.target.closest('[data-cancel-tx-id]')) return;
  const row = event.target.closest('[data-tx-id]');
  if (row) openTransactionDetails(row.dataset.txId);
});

function buildSeedGrid(phrase, gridId) {
  const words = phrase.trim().split(/\s+/);
  document.getElementById(gridId).innerHTML = words.map((w, i) =>
    `<div class="seed-word"><span class="seed-num">${i+1}</span><span class="seed-w">${w}</span></div>`
  ).join('');
}

function prepareWalletNameInput() {
  const input = document.getElementById('login-name');
  input.placeholder = listWalletNames().length
    ? 'Type your wallet name'
    : 'No local wallets found - create one first';
}

// ============================================================
// SECTION 7 — Navigation
// ============================================================
function showPanel(name) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('panel-' + name).classList.add('active');
  document.querySelectorAll('.nav-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.panel === name));
  if (name === 'dashboard') loadDashboard();
  if (name === 'send')      loadPending();
  if (name === 'tokens')    loadTokens();
  if (name === 'history')   loadHistory();
  if (name === 'activity')  loadActivity(ACTIVITY_PAGE);
  if (name === 'nodes')     loadNodes();
  if (name === 'pools')     loadPools();
}

function setMobileNav(open) {
  const shouldOpen = Boolean(open && S);
  document.body.classList.toggle('mobile-nav-open', shouldOpen);
  const toggle = document.getElementById('btn-mobile-nav');
  if (toggle) {
    toggle.setAttribute('aria-expanded', String(shouldOpen));
    toggle.setAttribute('aria-label', shouldOpen ? 'Close navigation' : 'Open navigation');
  }
  if (shouldOpen) document.getElementById('btn-close-mobile-nav')?.focus();
}

document.getElementById('btn-mobile-nav').addEventListener('click', () =>
  setMobileNav(!document.body.classList.contains('mobile-nav-open')));
document.getElementById('btn-close-mobile-nav').addEventListener('click', () => setMobileNav(false));
document.getElementById('mobile-nav-backdrop').addEventListener('click', () => setMobileNav(false));
document.getElementById('btn-mobile-logout').addEventListener('click', () => {
  setMobileNav(false);
  lockWallet();
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && document.body.classList.contains('mobile-nav-open')) {
    setMobileNav(false);
    document.getElementById('btn-mobile-nav')?.focus();
  }
});
window.addEventListener('resize', () => {
  if (window.innerWidth > 700) setMobileNav(false);
});

document.querySelectorAll('.nav-btn').forEach(b =>
  b.addEventListener('click', () => {
    if (b.dataset.panel === 'nodes') hideSyncPill();
    showPanel(b.dataset.panel);
    setMobileNav(false);
  }));

document.querySelectorAll('.auth-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.auth-pane').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('pane-' + tab.dataset.pane).classList.add('active');
  });
});

function switchToLoginTab(preFillName, alertMsg) {
  document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.auth-pane').forEach(p => p.classList.remove('active'));
  document.querySelector('[data-pane="login"]').classList.add('active');
  document.getElementById('pane-login').classList.add('active');
  prepareWalletNameInput();
  if (preFillName) {
    const input = document.getElementById('login-name');
    input.value = preFillName;
  }
  document.getElementById('login-pass').value = '';
  if (alertMsg) setAlert('login-alert', alertMsg, 'ok');
}

// ============================================================
// SECTION 8 — Auth: Unlock, Create, Recover
// ============================================================

// ── Unlock ──
document.getElementById('btn-login').addEventListener('click', doLogin);
['login-name', 'login-pass'].forEach(id =>
  document.getElementById(id).addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); }));

async function doLogin() {
  const btn  = document.getElementById('btn-login');
  const name = document.getElementById('login-name').value.trim();
  const pass = document.getElementById('login-pass').value;
  setAlert('login-alert', '');
  if (!name) { setAlert('login-alert', 'Enter your wallet name.'); return; }
  if (!pass) { setAlert('login-alert', 'Password is required.'); return; }
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span>';
  try {
    const wallet = await loadWallet(name, pass);
    if (!wallet) { setAlert('login-alert', 'Wallet name or password is incorrect.'); return; }
    S = wallet;
    afterLogin();
  } finally { btn.disabled = false; btn.textContent = 'Unlock'; }
}

// ── Create ──
document.getElementById('btn-create').addEventListener('click', async () => {
  const btn   = document.getElementById('btn-create');
  const name  = document.getElementById('create-name').value.trim();
  const pass  = document.getElementById('create-pass').value;
  const pass2 = document.getElementById('create-pass2').value;
  setAlert('create-alert', '');
  if (!name)           { setAlert('create-alert', 'Wallet name is required.'); return; }
  if (walletExists(name)) { setAlert('create-alert', 'A wallet with that name already exists.'); return; }
  if (pass.length < 8) { setAlert('create-alert', 'Password must be at least 8 characters.'); return; }
  if (pass !== pass2)  { setAlert('create-alert', 'Passwords do not match.'); return; }
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Creating…';
  try {
    const phrase              = generateSeedPhrase();
    const { privateKey, publicKey } = await seedToKeyPair(phrase);
    const address             = await publicKeyToAddress(publicKey);
    await saveWallet(name, pass, privateKey, publicKey, phrase);
    // Show seed phrase — wipe form fields immediately
    document.getElementById('create-pass').value  = '';
    document.getElementById('create-pass2').value = '';
    buildSeedGrid(phrase, 'seed-reveal-grid');
    document.getElementById('seed-reveal-addr').textContent = address;
    window._pendingWallet = { name, privateKey, publicKey, address };
    document.getElementById('create-step-form').style.display = 'none';
    document.getElementById('create-step-seed').style.display = 'block';
  } finally { btn.disabled = false; btn.textContent = 'Create Wallet'; }
});

document.getElementById('btn-seed-saved').addEventListener('click', () => {
  const w = window._pendingWallet;
  if (!w) return;
  document.getElementById('seed-reveal-grid').innerHTML = '';
  window._pendingWallet = null;
  document.getElementById('create-step-seed').style.display = 'none';
  document.getElementById('create-step-form').style.display = 'block';
  document.getElementById('create-name').value = '';
  switchToLoginTab(w.name, 'Wallet created! Unlock it with your password to continue.');
  toast('Wallet created — seed phrase cleared', 'ok');
});

// ── Recover ──
document.getElementById('btn-recover').addEventListener('click', async () => {
  const btn   = document.getElementById('btn-recover');
  const name  = document.getElementById('recover-name').value.trim();
  const seed  = document.getElementById('recover-seed').value.trim();
  const pass  = document.getElementById('recover-pass').value;
  const pass2 = document.getElementById('recover-pass2').value;
  setAlert('recover-alert', '');
  if (!name)                          { setAlert('recover-alert', 'Wallet name is required.'); return; }
  if (seed.split(/\s+/).length !== 12){ setAlert('recover-alert', 'Seed phrase must be exactly 12 words.'); return; }
  if (pass.length < 8)                { setAlert('recover-alert', 'Password must be at least 8 characters.'); return; }
  if (pass !== pass2)                 { setAlert('recover-alert', 'Passwords do not match.'); return; }
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Recovering…';
  try {
    const { privateKey, publicKey } = await seedToKeyPair(seed);
    await overwriteWallet(name, pass, privateKey, publicKey, seed);
    // Wipe sensitive fields immediately
    document.getElementById('recover-seed').value  = '';
    document.getElementById('recover-pass').value  = '';
    document.getElementById('recover-pass2').value = '';
    switchToLoginTab(name, 'Wallet recovered! Unlock it with your new password.');
    toast('Wallet recovered', 'ok');
  } finally { btn.disabled = false; btn.textContent = 'Recover Wallet'; }
});

// ── After login / logout ──
function afterLogin({ persist = true, expiresAt = null } = {}) {
  document.body.classList.add('wallet-unlocked');
  document.getElementById('main-nav').style.display = 'flex';
  document.getElementById('user-bar').style.display = 'flex';
  document.getElementById('hdr-wallet-name').textContent = S.name;
  document.getElementById('hdr-wallet-addr').textContent = S.address;
  document.getElementById('dash-addr').textContent = S.address;
  document.getElementById('recv-addr').textContent  = S.address;
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  if (persist) persistSession();
  else scheduleSessionExpiry(expiresAt);
  showPanel('dashboard');
}

function lockWallet(toastMessage = 'Wallet locked', alertMessage = '') {
  setMobileNav(false);
  document.body.classList.remove('wallet-unlocked');
  S = null;
  clearSessionRecord();
  document.getElementById('main-nav').style.display = 'none';
  document.getElementById('user-bar').style.display = 'none';
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('panel-auth').classList.add('active');
  document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.auth-pane').forEach(p => p.classList.remove('active'));
  document.querySelector('[data-pane="login"]').classList.add('active');
  document.getElementById('pane-login').classList.add('active');
  setAlert('login-alert', alertMessage, alertMessage ? 'info' : 'err');
  document.getElementById('login-pass').value = '';
  prepareWalletNameInput();
  toast(toastMessage);
}

document.getElementById('btn-logout').addEventListener('click', () => lockWallet());

document.getElementById('btn-export-wallet').addEventListener('click', () => {
  setAlert('backup-alert', '');
  if (!hasActiveSession()) { setAlert('backup-alert', 'Unlock a wallet first.'); return; }
  if (downloadWalletBackup(S.name)) {
    setAlert('backup-alert', 'Encrypted backup downloaded. Keep the file and its password safe.', 'ok');
    toast('Backup downloaded', 'ok');
  } else {
    setAlert('backup-alert', 'Could not find this wallet to back up.');
  }
});

document.getElementById('btn-restore-file').addEventListener('click', async () => {
  const button = document.getElementById('btn-restore-file');
  const fileInput = document.getElementById('restore-file');
  const preferredName = document.getElementById('restore-name').value.trim();
  setAlert('restore-alert', '');
  const file = fileInput.files && fileInput.files[0];
  if (!file) { setAlert('restore-alert', 'Choose a backup file first.'); return; }
  button.disabled = true;
  try {
    const restored = await importWalletBackup(file, preferredName);
    fileInput.value = '';
    document.getElementById('restore-name').value = '';
    switchToLoginTab(restored, 'Wallet restored. Unlock it with the password you set for it.');
    toast('Wallet restored', 'ok');
  } catch (error) {
    setAlert('restore-alert', error.message || 'Could not restore that file.');
  } finally {
    button.disabled = false;
  }
});

document.getElementById('btn-delete-wallet').addEventListener('click', async () => {
  if (!hasActiveSession()) return;
  const button = document.getElementById('btn-delete-wallet');
  const walletName = S.name;
  setAlert('delete-wallet-alert', '');
  const password = window.prompt(`Enter the password for "${walletName}" to delete its local wallet record:`);
  if (password === null) return;

  button.disabled = true;
  button.textContent = 'Verifying Password...';
  try {
    const verified = await loadWallet(walletName, password);
    if (!verified) {
      setAlert('delete-wallet-alert', 'Incorrect password. The wallet was not deleted.');
      return;
    }
    if (verified.privateKey instanceof Uint8Array) verified.privateKey.fill(0);

    const confirmed = window.confirm(
      `Permanently remove "${walletName}" from this browser?\n\n` +
      'This does not delete funds from the blockchain. You will need the seed phrase to recover access.'
    );
    if (!confirmed) return;
    if (!deleteWalletRecord(walletName)) {
      setAlert('delete-wallet-alert', 'The local wallet record could not be found.');
      return;
    }

    document.getElementById('login-name').value = '';

    lockWallet(
      'Local wallet deleted',
      `"${walletName}" was removed from this browser. Use its seed phrase to recover it.`
    );
  } finally {
    button.disabled = false;
    button.textContent = 'Delete This Wallet';
  }
});

// ============================================================
// SECTION 9 — Dashboard
// ============================================================
async function loadDashboard() {
  if (!hasActiveSession()) return;
  setSyncState('syncing');
  try {
    const [bal, pend, tokenResult, stats] = await Promise.all([
      api('GET', `/balance/${S.address}`),
      api('GET', '/pending'),
      api('GET', `/tokens?holder=${encodeURIComponent(S.address)}`),
      api('GET', '/stats'),
    ]);
    TOKENS = tokenResult.tokens || [];
    await hydrateTokenCollection(TOKENS);
    HLX_BALANCE = Number(bal.balance || 0);
    HLX_TOTAL_SUPPLY = Number(stats.total_supply || 0);
    NETWORK_STATS = stats;
    renderSendAssets();
    document.getElementById('dash-balance').textContent = formatWalletValue(walletTotalValueHlx());
    document.getElementById('dash-pending-count').textContent =
      pend.pending ? pend.pending.length : '—';
    renderDashboardTokens();
    setSyncState('synced');
  } catch (_) {
    document.getElementById('dash-token-list').innerHTML = '<div class="empty">Could not load token balances.</div>';
    setSyncState('error');
  }
}

function setSyncState(state) {
  const dot   = document.getElementById('sync-dot');
  const label = document.getElementById('sync-label');
  if (state === 'syncing') { dot.className = 'dot syncing'; label.textContent = 'Syncing…'; }
  else if (state === 'synced') { dot.className = 'dot'; label.textContent = 'Synced'; }
  else { dot.className = 'dot'; dot.style.background = 'var(--red)'; label.textContent = 'Offline'; }
}

document.getElementById('btn-dash-refresh').addEventListener('click', loadDashboard);
document.getElementById('btn-sync-now').addEventListener('click', async () => {
  setSyncState('syncing');
  try { await api('POST', '/nodes/sync_now'); await loadDashboard(); toast('Sync triggered', 'ok'); }
  catch (_) { toast('Sync failed', 'err'); setSyncState('error'); }
});

// ============================================================
// SECTION 10 — Send (signs locally, posts only signed payload)
// ============================================================
function renderSendAssets() {
  const select = document.getElementById('send-asset');
  const previous = select.value;
  select.replaceChildren(new Option(`Helix (HLX) - ${HLX_BALANCE} available`, 'HLX'));
  for (const token of heldTokens()) {
    const balance = formatTokenAmount(token.balance, token.decimals);
    select.appendChild(new Option(`${token.name} (${token.symbol}) - ${balance} available`, token.mint_address));
  }
  select.value = [...select.options].some(option => option.value === previous) ? previous : 'HLX';
  updateSendAssetUi();
}

function updateSendAssetUi() {
  const mintAddress = document.getElementById('send-asset').value;
  const token = TOKENS.find(item => item.mint_address === mintAddress);
  const symbol = token?.symbol || 'HLX';
  document.getElementById('send-amount-label').textContent = `Amount (${symbol})`;
  document.getElementById('btn-send').textContent = `Send ${symbol}`;
  document.getElementById('send-amount').value = '';
  setAlert('send-alert', '');
}

document.getElementById('send-asset').addEventListener('change', updateSendAssetUi);
document.getElementById('btn-send').addEventListener('click', async () => {
  if (!hasActiveSession()) return;
  const btn    = document.getElementById('btn-send');
  const to     = document.getElementById('send-to').value.trim().toLowerCase();
  const amount = document.getElementById('send-amount').value;
  const mintAddress = document.getElementById('send-asset').value;
  const token = TOKENS.find(item => item.mint_address === mintAddress) || null;
  const symbol = token?.symbol || 'HLX';
  setAlert('send-alert', '');

  if (!to)              { setAlert('send-alert', 'Recipient address is required.'); return; }
  if (!/^[0-9a-f]{40}$/.test(to)) { setAlert('send-alert', 'Address must be exactly 40 hex characters.'); return; }
  if (to === S.address) { setAlert('send-alert', 'Cannot send to your own address.'); return; }

  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Signing…';
  try {
    // Sign entirely in the browser — private key never leaves this page
    let payload;
    if (token) {
      const units = parseTokenAmount(amount, token.decimals);
      if (BigInt(units) > tokenBalanceUnits(token)) throw new Error(`Insufficient ${symbol} balance.`);
      payload = {
        tx_type: 'token_transfer', sender: S.address, receiver: to,
        amount: units, mint_address: token.mint_address, nonce: _hexRandom(16),
      };
      payload.signature = await signPayload(S.privateKey, payload);
    } else {
      if (!/^[1-9]\d*$/.test(amount)) throw new Error('HLX amount must be a positive whole number.');
      const units = Number(amount);
      if (!Number.isSafeInteger(units)) throw new Error('Amount is above the network limit.');
      payload = {
        sender: S.address, receiver: to, amount: units,
        signature: await signTransaction(S.privateKey, S.address, to, units),
      };
    }
    const publicKeyPem = await exportPublicKeyPEM(S.publicKey);
    payload.public_key = publicKeyPem;

    btn.innerHTML = '<span class="spinner"></span> Sending…';

    // Only send what the node needs to verify ownership
    const r = await api('POST', '/transaction', payload);

    if (r.message === 'Transaction added') {
      setAlert('send-alert', `${symbol} transfer submitted successfully.`, 'ok');
      document.getElementById('send-to').value     = '';
      document.getElementById('send-amount').value = '';
      toast(`${symbol} transfer submitted`, 'ok');
    } else {
      setAlert('send-alert', r.message || 'Transaction failed.');
    }
  } catch (e) { setAlert('send-alert', e.message || 'Could not reach the node.'); }
  finally { btn.disabled = false; btn.textContent = `Send ${symbol}`; }
});

// ============================================================
// SECTION 11 — Custom tokens
// ============================================================
let TOKENS = [];
let MARKET_MINT = null;
let HLX_BALANCE = 0;
let HLX_TOTAL_SUPPLY = 0;
let NETWORK_STATS = {};

function parseTokenAmount(value, decimals, allowZero = false) {
  const input = String(value).trim();
  const match = /^(0|[1-9]\d*)(?:\.(\d+))?$/.exec(input);
  if (!match) throw new Error('Enter a valid non-negative token amount.');
  const fraction = match[2] || '';
  if (fraction.length > decimals) throw new Error(`This token allows ${decimals} decimal places.`);
  const factor = 10n ** BigInt(decimals);
  const units = BigInt(match[1]) * factor + BigInt((fraction + '0'.repeat(decimals)).slice(0, decimals) || '0');
  if (units < 0n || (!allowZero && units === 0n)) throw new Error('Amount must be greater than zero.');
  if (units > BigInt(Number.MAX_SAFE_INTEGER)) throw new Error('Amount is above the network limit.');
  return Number(units);
}

function formatTokenAmount(units, decimals) {
  const amount = BigInt(units || 0);
  if (!decimals) return amount.toString();
  const factor = 10n ** BigInt(decimals);
  const fraction = (amount % factor).toString().padStart(decimals, '0').replace(/0+$/, '');
  return `${amount / factor}${fraction ? `.${fraction}` : ''}`;
}

function swapQuote(amountIn, reserveIn, reserveOut) {
  const input = BigInt(amountIn);
  const inputReserve = BigInt(reserveIn);
  const outputReserve = BigInt(reserveOut);
  if (input <= 0n || inputReserve <= 0n || outputReserve <= 0n) return 0n;
  const amountWithFee = input * 997n;
  return amountWithFee * outputReserve / (inputReserve * 1000n + amountWithFee);
}

function tokenPoolActive(token) {
  return BigInt(token.pool_hlx_reserve || 0) > 0n
    && BigInt(token.pool_token_reserve || 0) > 0n;
}

function tokenSpotPrice(token) {
  if (!tokenPoolActive(token)) return null;
  const price = Number(token.pool_hlx_reserve) * (10 ** Number(token.decimals || 0))
    / Number(token.pool_token_reserve);
  return Number.isFinite(price) ? price : null;
}

function formatTokenPrice(token) {
  const price = tokenSpotPrice(token);
  if (price === null) return 'No exchange pool';
  return `${price.toLocaleString(undefined, { maximumSignificantDigits: 8 })} HLX per ${token.symbol}`;
}

function tokenDistributionStats(token) {
  const supply = BigInt(token.supply || 0);
  const pooled = BigInt(token.pool_token_reserve || 0);
  const distributed = supply > pooled ? supply - pooled : 0n;
  const percent = supply > 0n ? Number(distributed * 10000n / supply) / 100 : 0;
  return { supply, pooled, distributed, percent };
}

function marketPointPrice(point, decimals) {
  const tokenReserve = Number(point.pool_token_reserve);
  const price = Number(point.pool_hlx_reserve) * (10 ** Number(decimals || 0)) / tokenReserve;
  return tokenReserve > 0 && Number.isFinite(price) && price > 0 ? price : null;
}

function compactPrice(value) {
  return value.toLocaleString(undefined, { maximumSignificantDigits: 7 });
}

const TOKEN_CHART_MIN_HEIGHT = 220;
const TOKEN_CHART_MAX_HEIGHT = 720;
const TOKEN_CHART_MIN_WIDTH = 360;
const TOKEN_CHART_MAX_WIDTH = 1800;
let TOKEN_CHART_HEIGHT = 320;
let TOKEN_CHART_WIDTH = 720;
let TOKEN_CHART_VIEW = null;
let TOKEN_CHART_POINTS = [];
let TOKEN_CHART_TOKEN = null;
let TOKEN_CHART_INTERVAL = null; // forced candle width in seconds; null = auto-fit
const TOKEN_CHART_RANGES = [
  { key: 'minute', label: 'Minute', seconds: 60 },
  { key: 'hour', label: 'Hour', seconds: 3600 },
  { key: 'day', label: 'Day', seconds: 86400 },
  { key: 'month', label: 'Month', seconds: 2592000 },
  { key: 'auto', label: 'Auto', seconds: null },
];

// Earliest confirmed point and "now" bound the whole selectable timeline.
function tokenChartBounds(points) {
  const stamps = points.map(point => point.timestamp).filter(Number.isFinite);
  const earliest = stamps.length ? Math.min(...stamps) : Date.now() / 1000 - 30;
  const latest = Math.max(Date.now() / 1000, stamps.length ? Math.max(...stamps) : 0);
  return { earliest, latest };
}

// Format epoch seconds as a local "YYYY-MM-DDTHH:MM:SS" string for a
// <input type="datetime-local">. Parsing back is `new Date(value)` (local).
function toLocalDatetimeValue(seconds) {
  const date = new Date(seconds * 1000);
  const pad = value => String(value).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
    + `T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

function chartRangePoints(points, startSeconds, endSeconds) {
  if (!points.length) return [];
  const inside = points.filter(point => point.timestamp > startSeconds && point.timestamp <= endSeconds);
  const before = points.filter(point => point.timestamp <= startSeconds).at(-1);
  const ranged = before
    ? [{ ...before, timestamp: startSeconds, carried: true }, ...inside]
    : inside.length ? [{ ...inside[0], timestamp: startSeconds, carried: true }, ...inside] : [];
  const latestKnown = ranged.at(-1) || before;
  if (latestKnown && latestKnown.timestamp < endSeconds) {
    ranged.push({ ...latestKnown, timestamp: endSeconds, carried: true });
  }
  return ranged;
}

function chartCandleInterval(spanSeconds) {
  if (TOKEN_CHART_INTERVAL) return TOKEN_CHART_INTERVAL;
  const targetCandles = Math.max(18, Math.min(90, Math.floor(TOKEN_CHART_WIDTH / 12)));
  const desired = spanSeconds / targetCandles;
  const intervals = [1, 5, 10, 15, 30, 60, 300, 900, 1800, 3600, 14400, 21600, 43200, 86400, 604800];
  return intervals.find(value => value >= desired) || intervals.at(-1);
}

function buildChartCandles(points, startSeconds, endSeconds) {
  if (!points.length) return [];
  const interval = chartCandleInterval(endSeconds - startSeconds);
  const count = Math.max(1, Math.ceil((endSeconds - startSeconds) / interval));
  const candles = [];
  let pointIndex = 0;
  let carriedPrice = points[0].price;
  for (let index = 0; index < count; index += 1) {
    const bucketStart = startSeconds + index * interval;
    const bucketEnd = Math.min(endSeconds, bucketStart + interval);
    const updates = [];
    while (pointIndex < points.length && points[pointIndex].timestamp <= bucketEnd) {
      if (points[pointIndex].timestamp >= bucketStart) updates.push(points[pointIndex]);
      pointIndex += 1;
    }
    const values = [carriedPrice, ...updates.map(point => point.price)];
    const open = carriedPrice;
    const close = updates.length ? updates.at(-1).price : carriedPrice;
    candles.push({
      timestamp: (bucketStart + bucketEnd) / 2,
      open, high: Math.max(...values, open), low: Math.min(...values, open), close,
      carried: updates.every(point => point.carried),
      block: updates.filter(point => !point.carried).at(-1)?.block,
    });
    carriedPrice = close;
  }
  return candles;
}

function chartTimeLabel(timestamp, spanSeconds) {
  const date = new Date(timestamp * 1000);
  if (spanSeconds > 2 * 24 * 60 * 60) return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  if (spanSeconds > 2 * 60) return date.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
  return date.toLocaleTimeString(undefined, { minute: '2-digit', second: '2-digit' });
}

// Default view mirrors a chart landing on "fit to data": the very first
// confirmed price update sits flush against the left edge and the latest
// one sits at the right, with nothing to pan through beyond real history.
function defaultTokenChartView(points) {
  const earliest = points[0]?.timestamp ?? (Date.now() / 1000 - 30);
  const latest = Math.max(Date.now() / 1000, points.at(-1)?.timestamp || 0);
  const minimumSpan = 30;
  return { start: earliest, end: Math.max(latest, earliest + minimumSpan) };
}

function clampTokenChartView(start, end, allPoints) {
  const minimumSpan = 30;
  const earliest = allPoints[0]?.timestamp ?? (Date.now() / 1000 - minimumSpan);
  const latest = Math.max(Date.now() / 1000, allPoints.at(-1)?.timestamp || 0);
  const fullHistorySpan = Math.max(minimumSpan, latest - earliest);
  const maximumSpan = fullHistorySpan;
  let span = Math.min(maximumSpan, Math.max(minimumSpan, end - start));
  if (end > latest) {
    end = latest;
    start = end - span;
  }
  if (start < earliest) {
    start = earliest;
    end = start + span;
  }
  if (end > latest) end = latest;
  return { start, end: start + span };
}

function bindTokenChartInteractions(container, allPoints, metrics) {
  const viewport = container.querySelector('.chart-viewport');
  const svg = container.querySelector('.price-chart-svg');
  const tooltip = container.querySelector('.chart-tooltip');
  const crossX = container.querySelector('[data-chart-cross-x]');
  const crossY = container.querySelector('[data-chart-cross-y]');
  if (!viewport || !svg || !tooltip) return;

  const { width, height, left, right, top, bottom, start, end, points } = metrics;
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;
  const coordinates = event => {
    const rect = svg.getBoundingClientRect();
    return {
      x: (event.clientX - rect.left) * width / Math.max(1, rect.width),
      y: (event.clientY - rect.top) * height / Math.max(1, rect.height),
      rect,
    };
  };
  const hideCrosshair = () => {
    crossX?.setAttribute('visibility', 'hidden');
    crossY?.setAttribute('visibility', 'hidden');
    tooltip.classList.remove('visible');
  };
  const showCrosshair = event => {
    if (!points.length) return;
    const position = coordinates(event);
    if (position.x < left || position.x > width - right || position.y < top || position.y > height - bottom) {
      hideCrosshair();
      return;
    }
    const timestamp = start + (position.x - left) * (end - start) / plotWidth;
    const point = points.reduce((closest, candidate) =>
      Math.abs(candidate.timestamp - timestamp) < Math.abs(closest.timestamp - timestamp) ? candidate : closest,
    points[0]);
    const pointX = left + (point.timestamp - start) * plotWidth / (end - start);
    const pointPrice = point.close ?? point.price;
    const pointY = top + (metrics.high - pointPrice) * plotHeight / (metrics.high - metrics.low);
    crossX?.setAttribute('x1', pointX); crossX?.setAttribute('x2', pointX);
    crossY?.setAttribute('y1', pointY); crossY?.setAttribute('y2', pointY);
    crossX?.setAttribute('visibility', 'visible'); crossY?.setAttribute('visibility', 'visible');
    tooltip.innerHTML = point.close === undefined
      ? `<strong>${escapeHtml(compactPrice(pointPrice))} HLX</strong><br>${escapeHtml(fmtDate(point.timestamp))}${point.block === undefined ? '' : `<br>Block ${escapeHtml(point.block)}`}`
      : `<strong>${escapeHtml(fmtDate(point.timestamp))}</strong><br>O ${escapeHtml(compactPrice(point.open))} &middot; H ${escapeHtml(compactPrice(point.high))}<br>L ${escapeHtml(compactPrice(point.low))} &middot; C ${escapeHtml(compactPrice(point.close))}${point.block === undefined ? '' : `<br>Last block ${escapeHtml(point.block)}`}`;
    const localX = (pointX / width) * position.rect.width;
    const localY = (pointY / height) * position.rect.height;
    tooltip.style.left = `${Math.min(position.rect.width - 166, Math.max(8, localX + 12))}px`;
    tooltip.style.top = `${Math.min(position.rect.height - 70, Math.max(8, localY - 58))}px`;
    tooltip.classList.add('visible');
  };

  viewport.addEventListener('pointermove', showCrosshair);
  viewport.addEventListener('pointerleave', hideCrosshair);
  viewport.addEventListener('dblclick', () => {
    TOKEN_CHART_VIEW = null;
    renderTokenPriceChart(container, TOKEN_CHART_TOKEN, TOKEN_CHART_POINTS);
  });
  viewport.addEventListener('wheel', event => {
    event.preventDefault();
    const position = coordinates(event);
    const ratio = Math.max(0, Math.min(1, (position.x - left) / plotWidth));
    const oldSpan = end - start;
    // Proportional to the actual scroll delta so a light trackpad flick zooms
    // gently and a hard mouse-wheel notch zooms further, the way TradingView
    // and most chart libraries respond to wheel input.
    const zoomFactor = Math.exp(event.deltaY * 0.0018);
    const newSpan = oldSpan * zoomFactor;
    const anchor = start + ratio * oldSpan;
    TOKEN_CHART_VIEW = clampTokenChartView(anchor - ratio * newSpan, anchor + (1 - ratio) * newSpan, allPoints);
    renderTokenPriceChart(container, TOKEN_CHART_TOKEN, TOKEN_CHART_POINTS);
  }, { passive: false });

  viewport.addEventListener('pointerdown', event => {
    if (event.button !== undefined && event.button !== 0) return;
    event.preventDefault();
    const originX = event.clientX;
    const originView = { start, end };
    const dragWidth = Math.max(1, svg.getBoundingClientRect().width);
    const move = moveEvent => {
      const seconds = -(moveEvent.clientX - originX) * (originView.end - originView.start) / dragWidth;
      TOKEN_CHART_VIEW = clampTokenChartView(originView.start + seconds, originView.end + seconds, allPoints);
      renderTokenPriceChart(container, TOKEN_CHART_TOKEN, TOKEN_CHART_POINTS);
    };
    const up = () => {
      document.removeEventListener('pointermove', move);
      document.removeEventListener('pointerup', up);
      document.removeEventListener('pointercancel', up);
    };
    document.addEventListener('pointermove', move);
    document.addEventListener('pointerup', up);
    document.addEventListener('pointercancel', up);
  });

  const resizeHandle = container.querySelector('.chart-resize-handle');
  resizeHandle?.addEventListener('pointerdown', event => {
    event.preventDefault();
    const originY = event.clientY;
    const originX = event.clientX;
    const originHeight = TOKEN_CHART_HEIGHT;
    const originWidth = TOKEN_CHART_WIDTH;
    const move = moveEvent => {
      TOKEN_CHART_HEIGHT = Math.round(Math.min(TOKEN_CHART_MAX_HEIGHT, Math.max(TOKEN_CHART_MIN_HEIGHT, originHeight + moveEvent.clientY - originY)));
      TOKEN_CHART_WIDTH = Math.round(Math.min(TOKEN_CHART_MAX_WIDTH, Math.max(TOKEN_CHART_MIN_WIDTH, originWidth + moveEvent.clientX - originX)));
      viewport.style.height = `${TOKEN_CHART_HEIGHT}px`;
      viewport.style.width = `${TOKEN_CHART_WIDTH}px`;
      const heightSlider = container.querySelector('#token-chart-height');
      const widthSlider = container.querySelector('#token-chart-width');
      if (heightSlider) heightSlider.value = String(TOKEN_CHART_HEIGHT);
      if (widthSlider) widthSlider.value = String(TOKEN_CHART_WIDTH);
    };
    const up = () => {
      document.removeEventListener('pointermove', move);
      document.removeEventListener('pointerup', up);
      document.removeEventListener('pointercancel', up);
      renderTokenPriceChart(container, TOKEN_CHART_TOKEN, TOKEN_CHART_POINTS);
    };
    document.addEventListener('pointermove', move);
    document.addEventListener('pointerup', up);
    document.addEventListener('pointercancel', up);
  });
}

function renderTokenPriceChart(container, token, rawPoints) {
  if (TOKEN_CHART_TOKEN?.mint_address !== token.mint_address) { TOKEN_CHART_VIEW = null; TOKEN_CHART_INTERVAL = null; }
  TOKEN_CHART_TOKEN = token;
  TOKEN_CHART_POINTS = rawPoints;
  const allPoints = rawPoints.map(point => ({ ...point, price: marketPointPrice(point, token.decimals) }))
    .filter(point => point.price !== null)
    .sort((left, right) => left.timestamp - right.timestamp);
  if (!allPoints.length) {
    container.innerHTML = '<div class="empty">Price history starts when an exchange pool is confirmed.</div>';
    return;
  }
  TOKEN_CHART_VIEW = TOKEN_CHART_VIEW || defaultTokenChartView(allPoints);
  TOKEN_CHART_VIEW = clampTokenChartView(TOKEN_CHART_VIEW.start, TOKEN_CHART_VIEW.end, allPoints);
  const { start, end } = TOKEN_CHART_VIEW;
  const points = chartRangePoints(allPoints, start, end);
  if (!points.length) {
    TOKEN_CHART_VIEW = defaultTokenChartView(allPoints);
    return renderTokenPriceChart(container, token, rawPoints);
  }
  const width = TOKEN_CHART_WIDTH, height = TOKEN_CHART_HEIGHT, left = 64, right = 18, top = 18, bottom = 42;
  const plotWidth = width - left - right, plotHeight = height - top - bottom;
  const candles = buildChartCandles(points, start, end);
  let low = Math.min(...candles.map(candle => candle.low));
  let high = Math.max(...candles.map(candle => candle.high));
  if (low === high) {
    const padding = Math.max(low * 0.05, 0.00000001);
    low = Math.max(0, low - padding);
    high += padding;
  } else {
    // Breathing room above/below the actual price extremes so the highest
    // wick and lowest wick don't sit flush against the plot edges.
    const range = high - low;
    const padding = range * 0.12;
    low = Math.max(0, low - padding);
    high += padding;
  }
  const yAt = price => top + (high - price) * plotHeight / (high - low);
  const grid = Array.from({ length: 5 }, (_, index) => {
    const ratio = index / 4;
    const y = top + ratio * plotHeight;
    const value = high - ratio * (high - low);
    return `<line class="chart-grid" x1="${left}" y1="${y}" x2="${width - right}" y2="${y}" />
      <text class="chart-axis-label" x="${left - 8}" y="${y + 4}" text-anchor="end">${escapeHtml(compactPrice(value))}</text>`;
  }).join('');
  const candleStep = plotWidth / candles.length;
  const candleWidth = Math.max(2, Math.min(14, candleStep * 0.68));
  const candleMarkup = candles.map((candle, index) => {
    const x = left + (index + 0.5) * candleStep;
    const direction = candle.close > candle.open ? 'bullish' : candle.close < candle.open ? 'bearish' : 'neutral';
    const bodyTop = Math.min(yAt(candle.open), yAt(candle.close));
    const bodyHeight = Math.max(1.5, Math.abs(yAt(candle.open) - yAt(candle.close)));
    return `<g class="chart-candle ${direction}${candle.carried ? ' carried' : ''}">
      <line class="candle-wick" x1="${x}" y1="${yAt(candle.high)}" x2="${x}" y2="${yAt(candle.low)}" />
      <rect class="candle-body" x="${x - candleWidth / 2}" y="${bodyTop}" width="${candleWidth}" height="${bodyHeight}" rx="1" />
    </g>`;
  }).join('');
  const span = end - start;
  const timeGrid = Array.from({ length: 5 }, (_, index) => {
    const ratio = index / 4;
    const x = left + ratio * plotWidth;
    const timestamp = start + ratio * span;
    return `<line class="chart-grid" x1="${x}" y1="${top}" x2="${x}" y2="${height - bottom}" />
      <text class="chart-axis-label" x="${x}" y="${height - 12}" text-anchor="${index === 0 ? 'start' : index === 4 ? 'end' : 'middle'}">${escapeHtml(chartTimeLabel(timestamp, span))}</text>`;
  }).join('');
  const first = candles[0].open;
  const current = candles.at(-1).close;
  const change = first > 0 ? (current - first) * 100 / first : 0;
  const trend = change > 0 ? 'bullish' : change < 0 ? 'bearish' : 'neutral';
  const realUpdates = points.filter(point => !point.carried).length;
  container.classList.remove('bullish', 'bearish', 'neutral');
  container.classList.add(trend);
  const { earliest: chartEarliest, latest: chartLatest } = tokenChartBounds(allPoints);
  const rangeButtons = TOKEN_CHART_RANGES.map(range =>
    `<button type="button" class="chart-range-btn${TOKEN_CHART_INTERVAL === range.seconds ? ' active' : ''}" data-chart-range="${range.key}">${range.label}</button>`
  ).join('');
  container.innerHTML = `<div class="price-chart-head"><strong>Confirmed price history</strong>
      <span class="price-chart-summary">Current ${escapeHtml(compactPrice(current))} HLX &middot; Low ${escapeHtml(compactPrice(low))} &middot; High ${escapeHtml(compactPrice(high))} &middot; <strong class="chart-trend ${trend}">${change >= 0 ? '+' : ''}${escapeHtml(change.toFixed(2))}%</strong></span></div>
    <div class="price-chart-controls">
      <div class="price-chart-ranges" role="group" aria-label="Candle interval">${rangeButtons}</div>
      <label class="chart-start-control">Start
        <input id="token-chart-start" type="datetime-local" step="1" min="${toLocalDatetimeValue(chartEarliest)}" max="${toLocalDatetimeValue(chartLatest)}" value="${toLocalDatetimeValue(start)}" aria-label="Choose the date and time the chart starts" />
      </label>
      <label class="chart-size-control">Height
        <input id="token-chart-height" type="range" min="${TOKEN_CHART_MIN_HEIGHT}" max="${TOKEN_CHART_MAX_HEIGHT}" step="10" value="${TOKEN_CHART_HEIGHT}" aria-label="Chart height" />
        <span>${TOKEN_CHART_HEIGHT}px</span>
      </label>
      <label class="chart-size-control">Width
        <input id="token-chart-width" type="range" min="${TOKEN_CHART_MIN_WIDTH}" max="${TOKEN_CHART_MAX_WIDTH}" step="20" value="${TOKEN_CHART_WIDTH}" aria-label="Chart width" />
        <span>${TOKEN_CHART_WIDTH}px</span>
      </label>
    </div>
    <div class="chart-scroll"><div class="chart-viewport" style="height:${TOKEN_CHART_HEIGHT}px;width:${TOKEN_CHART_WIDTH}px">
      <svg class="price-chart-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img" aria-label="${escapeHtml(token.symbol)} price in HLX over time">
        ${grid}${timeGrid}${candleMarkup}
        <line class="chart-crosshair" data-chart-cross-x y1="${top}" y2="${height - bottom}" visibility="hidden" />
        <line class="chart-crosshair" data-chart-cross-y x1="${left}" x2="${width - right}" visibility="hidden" />
        <rect class="chart-hit-area" x="${left}" y="${top}" width="${plotWidth}" height="${plotHeight}" />
      </svg>
      <div class="chart-tooltip"></div>
    </div></div>
    <div class="chart-resize-handle" role="separator" aria-label="Drag to resize chart" tabindex="0"></div>
    <div class="chart-help token-address"><span>${realUpdates} confirmed market update${realUpdates === 1 ? '' : 's'} in view</span><span>Drag to pan &middot; scroll to zoom &middot; double-click to reset</span></div>`;
  bindTokenChartInteractions(container, allPoints, { width, height, left, right, top, bottom, start, end, points: candles, low, high });
}

async function loadTokenPriceChart(token) {
  const container = document.getElementById('token-price-chart');
  if (!container) return;
  try {
    const result = await api('GET', `/token/${encodeURIComponent(token.mint_address)}/market/history`);
    if (MARKET_MINT !== token.mint_address) return;
    renderTokenPriceChart(container, token, result.points || []);
  } catch (error) {
    if (MARKET_MINT === token.mint_address) {
      container.innerHTML = `<div class="empty">${escapeHtml(error.message || 'Could not load price history.')}</div>`;
    }
  }
}

let LOADED_TOKEN_METADATA = null;
const TOKEN_METADATA_CACHE = new Map();

function requireHttpsUrl(value, label) {
  let parsed;
  try { parsed = new URL(value); }
  catch (_) { throw new Error(`${label} must be a valid URL.`); }
  if (parsed.protocol !== 'https:') throw new Error(`${label} must use HTTPS.`);
  if (parsed.username || parsed.password) throw new Error(`${label} cannot contain credentials.`);
  return parsed.toString();
}

function normalizeTokenMetadata(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    throw new Error('Metadata must be a JSON object.');
  }
  const name = typeof data.name === 'string' ? data.name.trim() : '';
  const symbol = typeof data.symbol === 'string' ? data.symbol.trim() : '';
  const description = typeof data.description === 'string' ? data.description.trim() : '';
  if (!name || name.length > 64) throw new Error('Metadata name must contain 1 to 64 characters.');
  if (!/^[A-Z][A-Z0-9]{1,11}$/.test(symbol)) throw new Error('Metadata symbol must be 2 to 12 uppercase letters or numbers.');
  if (!description || description.length > 1000) throw new Error('Metadata description must contain 1 to 1000 characters.');
  const image = requireHttpsUrl(typeof data.image === 'string' ? data.image.trim() : '', 'Metadata image');
  return { name, symbol, description, image };
}

async function fetchTokenMetadataDocument(rawUri) {
  const uri = requireHttpsUrl(rawUri, 'Metadata JSON URL');
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10_000);
  let response;
  try {
    response = await fetch(uri, {
      headers: { accept: 'application/json' }, cache: 'no-store', signal: controller.signal,
    });
  } finally {
    clearTimeout(timeout);
  }
  if (!response.ok) throw new Error(`Metadata request returned HTTP ${response.status}.`);
  const declaredLength = Number(response.headers.get('content-length') || 0);
  if (declaredLength > 1_048_576) throw new Error('Metadata JSON is larger than 1 MB.');
  const text = await response.text();
  if (text.length > 1_048_576) throw new Error('Metadata JSON is larger than 1 MB.');
  let data;
  try { data = JSON.parse(text); }
  catch (_) { throw new Error('Metadata URL did not return valid JSON.'); }
  return { uri, ...normalizeTokenMetadata(data) };
}

async function hydrateTokenMetadata(token) {
  token.display_image = token.image || null;
  token.display_description = token.description || null;
  if (token.display_image || !token.uri) return token;
  try {
    let request = TOKEN_METADATA_CACHE.get(token.uri);
    if (!request) {
      request = fetchTokenMetadataDocument(token.uri);
      TOKEN_METADATA_CACHE.set(token.uri, request);
    }
    const metadata = await request;
    // The confirmed mint identity remains authoritative. Remote metadata is
    // used only as a display fallback for pre-snapshot token blocks.
    if (metadata.name !== token.name || metadata.symbol !== token.symbol) return token;
    token.display_image = metadata.image;
    token.display_description = token.description || metadata.description;
  } catch (_) {
    TOKEN_METADATA_CACHE.delete(token.uri);
  }
  return token;
}

async function hydrateTokenCollection(tokens) {
  await Promise.allSettled(tokens.slice(0, 100).map(hydrateTokenMetadata));
}

async function tokenMetadataHash(metadata) {
  const digest = await crypto.subtle.digest(
    'SHA-256', new TextEncoder().encode(canonicalJson(metadata)));
  return _bytesToHex(new Uint8Array(digest));
}

function renderTokenMetadataPreview(metadata) {
  const preview = document.getElementById('token-metadata-preview');
  if (!metadata) {
    preview.className = 'empty';
    preview.textContent = 'Load a JSON document containing name, symbol, description, and image.';
    return;
  }
  preview.className = 'metadata-preview';
  preview.innerHTML = `<img src="${escapeHtml(metadata.image)}" alt="${escapeHtml(metadata.name)} token image">
    <div><strong>${escapeHtml(metadata.name)} (${escapeHtml(metadata.symbol)})</strong>
    <div class="metadata-description">${escapeHtml(metadata.description)}</div></div>`;
}

async function loadTokenMetadata() {
  const rawUri = document.getElementById('token-uri').value.trim();
  const metadata = await fetchTokenMetadataDocument(rawUri);
  LOADED_TOKEN_METADATA = metadata;
  renderTokenMetadataPreview(metadata);
  return LOADED_TOKEN_METADATA;
}

document.getElementById('token-uri').addEventListener('input', () => {
  LOADED_TOKEN_METADATA = null;
  renderTokenMetadataPreview(null);
});
document.getElementById('btn-token-load-metadata').addEventListener('click', async () => {
  const button = document.getElementById('btn-token-load-metadata');
  setAlert('token-create-alert', '');
  button.disabled = true;
  button.innerHTML = '<span class="spinner"></span> Loading&hellip;';
  try {
    const metadata = await loadTokenMetadata();
    setAlert('token-create-alert', `Loaded ${metadata.name} metadata.`, 'ok');
  } catch (error) {
    LOADED_TOKEN_METADATA = null;
    renderTokenMetadataPreview(null);
    setAlert('token-create-alert', error.message || 'Could not load metadata.');
  } finally {
    button.disabled = false;
    button.textContent = 'Load metadata';
  }
});

function tokenBalanceUnits(token) {
  try { return BigInt(token.balance || 0); }
  catch (_) { return 0n; }
}

// Total wallet worth valued in HLX: the raw HLX balance plus each held token's
// balance converted through its pool price. Decimals cancel because both the
// balance and the pool token reserve are in the same base units:
//   value_HLX = balance_units * pool_hlx_reserve / pool_token_reserve
function walletTotalValueHlx() {
  let total = Number(HLX_BALANCE) || 0;
  for (const token of TOKENS) {
    const balance = Number(tokenBalanceUnits(token));
    const hlxReserve = Number(token.pool_hlx_reserve || 0);
    const tokenReserve = Number(token.pool_token_reserve || 0);
    if (balance > 0 && hlxReserve > 0 && tokenReserve > 0) {
      total += balance * hlxReserve / tokenReserve;
    }
  }
  return total;
}

function formatWalletValue(value) {
  if (!Number.isFinite(value)) return '—';
  return value.toLocaleString(undefined, { maximumFractionDigits: 4 });
}

function heldTokens() {
  return TOKENS.filter(token => tokenBalanceUnits(token) > 0n);
}

function manageableTokens() {
  return TOKENS.filter(token =>
    tokenBalanceUnits(token) > 0n || token.dad_address === S.address);
}

function tokenCardMarkup(token) {
  const artwork = token.display_image || token.image;
  const identity = artwork
    ? `<img class="token-avatar" src="${escapeHtml(artwork)}" alt="${escapeHtml(token.name)} token image">`
    : `<span class="token-symbol">${escapeHtml(token.symbol)}</span>`;
  const dadLabel = token.dad_address === S.address
    ? '<span class="token-address">You are DAD authority</span>'
    : '';
  const liquidityLabel = `<span class="token-address">Liquidity: ${escapeHtml(token.pool_hlx_reserve || 0)} HLX</span>`;
  return `<button class="token-card" type="button" data-token-mint="${escapeHtml(token.mint_address)}">
    ${identity}
    <span><strong>${escapeHtml(token.name)} (${escapeHtml(token.symbol)})</strong>
      <span class="token-address">MNT ${escapeHtml(short(token.mint_address))}</span>${liquidityLabel}${dadLabel}</span>
    <span class="token-balance">${formatTokenAmount(token.balance, token.decimals)}</span>
  </button>`;
}

function nativeTokenCardMarkup() {
  return `<button class="token-card" type="button" data-native-asset="HLX">
    <span class="logo-hex token-native-logo" aria-hidden="true">&#11041;</span>
    <span><strong>Helix (HLX)</strong><span class="token-address">Native blockchain asset</span><span class="token-address">Protocol-controlled supply</span></span>
    <span class="token-balance">${escapeHtml(HLX_BALANCE)}</span>
  </button>`;
}

function emptyTokenMarkup(message) {
  return `<div class="empty">${escapeHtml(message)}<br>
    <button class="btn btn-primary btn-sm mt8" type="button" data-open-token-create>Create a Token</button></div>`;
}

function showTokenPane(name) {
  document.querySelectorAll('.token-pane').forEach(pane =>
    pane.classList.toggle('active', pane.id === `token-pane-${name}`));
  document.querySelectorAll('.token-tab').forEach(tab =>
    tab.classList.toggle('active', tab.dataset.tokenPane === name));
}

function renderDashboardTokens() {
  const list = document.getElementById('dash-token-list');
  const held = heldTokens();
  list.innerHTML = nativeTokenCardMarkup() + held.map(tokenCardMarkup).join('');
}

function renderDiscoveryTokens() {
  const list = document.getElementById('token-discovery-list');
  const query = document.getElementById('token-search').value.trim().toLowerCase();
  const discovered = TOKENS.filter(token => !query || [
    token.name, token.symbol, token.mint_address,
  ].some(value => String(value || '').toLowerCase().includes(query))).sort((left, right) => {
    const leftLiquidity = BigInt(left.pool_hlx_reserve || 0);
    const rightLiquidity = BigInt(right.pool_hlx_reserve || 0);
    if (leftLiquidity === rightLiquidity) return left.symbol.localeCompare(right.symbol);
    return leftLiquidity > rightLiquidity ? -1 : 1;
  });
  const showHlx = !query || ['helix', 'hlx', 'native'].some(value => value.includes(query));
  const hlxCard = showHlx ? nativeTokenCardMarkup() : '';
  list.innerHTML = (hlxCard || discovered.length)
    ? hlxCard + discovered.map(tokenCardMarkup).join('')
    : '<div class="empty">No assets match your search.</div>';
  if (MARKET_MINT === 'HLX') {
    renderNativeAsset();
  } else if (MARKET_MINT) {
    const selected = TOKENS.find(token => token.mint_address === MARKET_MINT);
    if (selected) renderMarketToken(selected);
  }
}

function renderNativeAsset() {
  MARKET_MINT = 'HLX';
  const supply = Number(NETWORK_STATS.total_supply ?? HLX_TOTAL_SUPPLY);
  const maximum = Number(NETWORK_STATS.max_supply || 20_000_000);
  const remaining = Math.max(0, maximum - supply);
  const issuedPercent = maximum > 0 ? Math.min(100, supply * 100 / maximum) : 0;
  const nativeDad = NETWORK_STATS.native_dad_address || '9d7c721b209cee99a8158c524fa433ead9236781';
  const nativeDadHeight = Number(NETWORK_STATS.native_dad_activation_height || 300);
  const nativeDadStatus = NETWORK_STATS.native_dad_active
    ? 'Active non-minting governance authority'
    : `Scheduled non-minting authority at block ${nativeDadHeight}`;
  document.getElementById('token-market-detail').innerHTML = `
    <div style="display:flex;gap:16px;align-items:flex-start">
      <div class="logo-hex token-native-logo" aria-hidden="true">&#11041;</div>
      <div><h2>Helix (HLX)</h2><div class="metadata-description">The native currency of the Helix blockchain and the liquidity asset used by token exchange pools.</div></div>
    </div>
    <div class="detail-grid" style="margin-top:16px">
      ${transactionDetailRow('Asset type', 'Native blockchain currency')}
      ${transactionDetailRow('Your balance', `${HLX_BALANCE} HLX`)}
      ${transactionDetailRow('Circulating supply', `${supply.toLocaleString()} HLX`)}
      ${transactionDetailRow('Maximum supply', `${maximum.toLocaleString()} HLX`)}
      ${transactionDetailRow('Remaining mineable', `${remaining.toLocaleString()} HLX`)}
      ${transactionDetailRow('Next block reward', `${NETWORK_STATS.block_reward ?? 2} HLX`)}
      ${transactionDetailRow('Block height', NETWORK_STATS.height ?? '—')}
      ${transactionDetailRow('Next difficulty', NETWORK_STATS.next_difficulty ?? NETWORK_STATS.difficulty ?? '—')}
      ${transactionDetailRow('Target block time', `${NETWORK_STATS.target_block_time_seconds ?? 600} seconds`)}
      ${transactionDetailRow('Cumulative chain work', NETWORK_STATS.chain_work ?? '—')}
      ${transactionDetailRow('Pending transactions', NETWORK_STATS.pending_transactions ?? '—')}
      ${transactionDetailRow('Exchange value', '1 HLX')}
      ${transactionDetailRow('MNT address', 'Not applicable')}
      ${transactionDetailRow('DAD authority', nativeDad)}
      ${transactionDetailRow('DAD status', nativeDadStatus)}
      ${transactionDetailRow('DAD mint power', 'None - new HLX is mining-only')}
    </div>
    <div class="native-supply" aria-label="${escapeHtml(issuedPercent.toFixed(6))}% of maximum HLX supply issued">
      <div class="native-supply-head"><span>Supply issued</span><strong>${escapeHtml(issuedPercent.toFixed(6))}%</strong></div>
      <div class="native-supply-track"><span style="width:${Math.max(0.15, issuedPercent)}%"></span></div>
    </div>
    <div class="alert alert-info" style="margin-top:16px">HLX is the network's pricing currency, so its value in HLX is always 1. A price-against-itself graph would be flat. HLX is used to buy tokens and fund exchange pools.</div>`;
}

function renderMarketToken(token) {
  MARKET_MINT = token.mint_address;
  const detail = document.getElementById('token-market-detail');
  const artwork = token.display_image || token.image;
  const image = artwork
    ? `<img class="token-avatar" style="width:88px;height:88px" src="${escapeHtml(artwork)}" alt="${escapeHtml(token.name)} token image">`
    : `<div class="token-symbol">${escapeHtml(token.symbol)}</div>`;
  const active = tokenPoolActive(token);
  const swapProtocolActive = NETWORK_STATS.token_swap_active !== false;
  const swapTargets = TOKENS.filter(item => item.mint_address !== token.mint_address && tokenPoolActive(item));
  const swapPanel = active && swapTargets.length ? `
    <div class="card" style="margin-top:16px;padding:18px">
      <div class="card-title">Swap tokens</div>
      <div class="token-layout">
        <div class="field"><label>Swap ${escapeHtml(token.symbol)}</label><input id="market-swap-source" inputmode="decimal" placeholder="0" /></div>
        <div class="field"><label>Receive token</label><select id="market-swap-target">${swapTargets.map(item =>
          `<option value="${escapeHtml(item.mint_address)}">${escapeHtml(item.symbol)} — ${escapeHtml(item.name)}</option>`
        ).join('')}</select></div>
      </div>
      <div id="market-swap-quote" class="token-address">Enter an amount for a routed HLX quote.</div>
      <button class="btn btn-primary btn-full mt8" id="btn-market-swap"${swapProtocolActive ? '' : ' disabled'}>Swap ${escapeHtml(token.symbol)}</button>
      ${swapProtocolActive ? '' : `<div class="alert alert-info mt8">Token-to-token swaps activate at block ${escapeHtml(NETWORK_STATS.token_swap_activation_height ?? 200)}. Upgrade every node to protocol 10 before activation.</div>`}
      <div class="token-address mt8">The swap is atomic and routes through both tokens' HLX pools. The displayed quote includes both 0.3% pool fees.</div>
    </div>` : '';
  const distribution = tokenDistributionStats(token);
  const authorityRisk = token.dad_address
    ? `<div class="alert alert-warn" style="margin-top:16px">The DAD authority can mint additional supply. A DAD could sell newly minted tokens into this pool, so review the authority and liquidity before trading.</div>`
    : `<div class="alert alert-info" style="margin-top:16px">DAD authority is revoked; this token's total supply is fixed.</div>`;
  const market = active ? `
    <div class="detail-grid" style="margin:16px 0">
      ${transactionDetailRow('Spot price', formatTokenPrice(token))}
      ${transactionDetailRow('Liquidity', `${token.pool_hlx_reserve} HLX`)}
      ${transactionDetailRow('Token reserve', `${formatTokenAmount(token.pool_token_reserve, token.decimals)} ${token.symbol}`)}
      ${transactionDetailRow('Trading fee', '0.3% retained by pool')}
    </div>
    <div id="token-price-chart" class="price-chart-card"><div class="empty">Loading confirmed price history&hellip;</div></div>
    <div id="market-alert"></div>
    <div class="token-layout">
      <div>
        <div class="field"><label>Buy with whole HLX</label><input id="market-buy-hlx" type="number" min="1" step="1" placeholder="0" /></div>
        <div id="market-buy-quote" class="token-address">Enter an amount for a quote.</div>
        <button class="btn btn-primary btn-full mt8" id="btn-market-buy">Buy ${escapeHtml(token.symbol)}</button>
      </div>
      <div>
        <div class="field"><label>Sell ${escapeHtml(token.symbol)}</label><input id="market-sell-token" inputmode="decimal" placeholder="0" /></div>
        <div id="market-sell-quote" class="token-address">Your balance: ${formatTokenAmount(token.balance, token.decimals)} ${escapeHtml(token.symbol)}</div>
        <button class="btn btn-ghost btn-full mt8" id="btn-market-sell">Sell ${escapeHtml(token.symbol)}</button>
      </div>
    </div>${swapPanel}` : `<div class="alert alert-info" style="margin-top:16px">This token is discoverable, but its DAD has not created an HLX exchange pool yet.</div>`;
  detail.innerHTML = `<div style="display:flex;gap:16px;align-items:flex-start">
      ${image}<div><h2>${escapeHtml(token.name)} (${escapeHtml(token.symbol)})</h2>
      <div class="metadata-description">${escapeHtml(token.display_description || token.description || 'No metadata description available.')}</div></div>
    </div>
    <div class="detail-grid" style="margin-top:16px">
      ${transactionDetailRow('MNT address', token.mint_address)}
      ${transactionDetailRow('DAD authority', token.dad_address || 'revoked')}
      ${transactionDetailRow('Creator', token.creator_address)}
      ${transactionDetailRow('Supply', `${formatTokenAmount(token.supply, token.decimals)} ${token.symbol}`)}
      ${transactionDetailRow('Your balance', `${formatTokenAmount(token.balance, token.decimals)} ${token.symbol}`)}
      ${transactionDetailRow('Metadata URI', token.uri)}
      ${transactionDetailRow('Metadata hash', token.metadata_hash)}
    </div>${authorityRisk}${market}
    <div class="native-supply" aria-label="${escapeHtml(distribution.percent.toFixed(2))}% of ${escapeHtml(token.symbol)} supply distributed outside the exchange pool">
      <div class="native-supply-head"><span>Supply distributed outside pool</span><strong>${escapeHtml(distribution.percent.toFixed(2))}%</strong></div>
      <div class="native-supply-track"><span style="width:${Math.max(distribution.percent > 0 ? 0.15 : 0, distribution.percent)}%"></span></div>
      <div class="token-address">${formatTokenAmount(distribution.distributed, token.decimals)} of ${formatTokenAmount(distribution.supply, token.decimals)} ${escapeHtml(token.symbol)} is held outside the pool.</div>
    </div>`;
  updateMarketQuotes();
  updateTokenSwapQuote();
  if (active) loadTokenPriceChart(token);
}

function updateMarketQuotes() {
  const token = TOKENS.find(item => item.mint_address === MARKET_MINT);
  if (!token || !tokenPoolActive(token)) return;
  const buyInput = document.getElementById('market-buy-hlx');
  const sellInput = document.getElementById('market-sell-token');
  if (buyInput) {
    const amount = /^\d+$/.test(buyInput.value.trim()) ? BigInt(buyInput.value.trim()) : 0n;
    const output = swapQuote(amount, token.pool_hlx_reserve, token.pool_token_reserve);
    document.getElementById('market-buy-quote').textContent = output > 0n
      ? `Estimated receive: ${formatTokenAmount(output, token.decimals)} ${token.symbol}`
      : 'Enter an amount for a quote.';
  }
  if (sellInput) {
    let amount = 0n;
    try { amount = BigInt(parseTokenAmount(sellInput.value, token.decimals)); } catch (_) {}
    const output = swapQuote(amount, token.pool_token_reserve, token.pool_hlx_reserve);
    document.getElementById('market-sell-quote').textContent = output > 0n
      ? `Estimated receive: ${output} HLX`
      : `Your balance: ${formatTokenAmount(token.balance, token.decimals)} ${token.symbol}`;
  }
}

function tokenSwapQuote(source, target, amount) {
  const routedHlx = swapQuote(amount, source.pool_token_reserve, source.pool_hlx_reserve);
  const received = swapQuote(routedHlx, target.pool_hlx_reserve, target.pool_token_reserve);
  return { routedHlx, received };
}

function updateTokenSwapQuote() {
  const source = TOKENS.find(item => item.mint_address === MARKET_MINT);
  const amountInput = document.getElementById('market-swap-source');
  const targetSelect = document.getElementById('market-swap-target');
  const quoteElement = document.getElementById('market-swap-quote');
  if (!source || !amountInput || !targetSelect || !quoteElement) return;
  const target = TOKENS.find(item => item.mint_address === targetSelect.value);
  if (!target) return;
  let amount = 0n;
  try { amount = BigInt(parseTokenAmount(amountInput.value, source.decimals)); } catch (_) {}
  const { routedHlx, received } = tokenSwapQuote(source, target, amount);
  quoteElement.textContent = received > 0n
    ? `Estimated receive: ${formatTokenAmount(received, target.decimals)} ${target.symbol} (routed value: ${routedHlx} HLX)`
    : `Your balance: ${formatTokenAmount(source.balance, source.decimals)} ${source.symbol}`;
}

// ---- Dedicated Swap tab ---------------------------------------------------
function swappableSources() {
  return TOKENS.filter(token => tokenBalanceUnits(token) > 0n && tokenPoolActive(token));
}

function swappableTargets(sourceMint) {
  return TOKENS.filter(token => token.mint_address !== sourceMint && tokenPoolActive(token));
}

function renderSwapPane() {
  const sourceSelect = document.getElementById('swap-source');
  const targetSelect = document.getElementById('swap-target');
  const body = document.getElementById('swap-body');
  const empty = document.getElementById('swap-empty');
  const button = document.getElementById('btn-swap-tokens');
  if (!sourceSelect || !targetSelect || !body || !empty) return;
  const sources = swappableSources();
  if (!sources.length) {
    body.style.display = 'none';
    empty.hidden = false;
    return;
  }
  body.style.display = '';
  empty.hidden = true;
  const previousSource = sourceSelect.value;
  const previousTarget = targetSelect.value;
  sourceSelect.replaceChildren(...sources.map(token =>
    new Option(`${token.name} (${token.symbol}) — balance ${formatTokenAmount(token.balance, token.decimals)}`, token.mint_address)));
  if (sources.some(token => token.mint_address === previousSource)) sourceSelect.value = previousSource;
  const targets = swappableTargets(sourceSelect.value);
  targetSelect.replaceChildren(...targets.map(token =>
    new Option(`${token.name} (${token.symbol})`, token.mint_address)));
  if (targets.some(token => token.mint_address === previousTarget)) targetSelect.value = previousTarget;
  const swapActive = NETWORK_STATS.token_swap_active !== false;
  if (button) {
    button.disabled = !swapActive || !targets.length;
    button.title = swapActive ? '' : `Token-to-token swaps activate at block ${NETWORK_STATS.token_swap_activation_height ?? 200}.`;
  }
  updateStandaloneSwapQuote();
}

function updateStandaloneSwapQuote() {
  const sourceSelect = document.getElementById('swap-source');
  const targetSelect = document.getElementById('swap-target');
  const amountInput = document.getElementById('swap-amount');
  const quote = document.getElementById('swap-quote');
  if (!sourceSelect || !targetSelect || !amountInput || !quote) return;
  const source = TOKENS.find(token => token.mint_address === sourceSelect.value);
  const target = TOKENS.find(token => token.mint_address === targetSelect.value);
  if (!source || !target) {
    quote.textContent = 'Select two tokens that both have active HLX pools.';
    return;
  }
  let amount = 0n;
  try { amount = BigInt(parseTokenAmount(amountInput.value, source.decimals)); } catch (_) {}
  const { routedHlx, received } = tokenSwapQuote(source, target, amount);
  quote.textContent = received > 0n
    ? `Estimated receive: ${formatTokenAmount(received, target.decimals)} ${target.symbol} (routed value: ${routedHlx} HLX)`
    : `Your balance: ${formatTokenAmount(source.balance, source.decimals)} ${source.symbol}`;
}

async function submitStandaloneSwap() {
  if (!hasActiveSession()) return;
  const sourceSelect = document.getElementById('swap-source');
  const targetSelect = document.getElementById('swap-target');
  const button = document.getElementById('btn-swap-tokens');
  setAlert('swap-alert', '');
  const source = TOKENS.find(token => token.mint_address === sourceSelect?.value);
  const target = TOKENS.find(token => token.mint_address === targetSelect?.value);
  if (!source || !target || !button) { setAlert('swap-alert', 'Select two tokens with active pools.'); return; }
  if (!tokenPoolActive(source) || !tokenPoolActive(target)) { setAlert('swap-alert', 'Both tokens need an active HLX pool.'); return; }
  const original = button.textContent;
  try {
    const amount = parseTokenAmount(document.getElementById('swap-amount').value, source.decimals);
    if (BigInt(amount) > tokenBalanceUnits(source)) throw new Error(`Swap exceeds your confirmed ${source.symbol} balance.`);
    const { received } = tokenSwapQuote(source, target, BigInt(amount));
    if (received <= 0n) throw new Error('This swap is too small for the current pool liquidity.');
    const minimum = received > 1n ? received * 99n / 100n : 1n;
    if (minimum > BigInt(Number.MAX_SAFE_INTEGER)) throw new Error('Swap output is above the network limit.');
    const payload = {
      tx_type: 'token_swap', sender: S.address, receiver: S.address,
      amount, mint_address: source.mint_address,
      target_mint_address: target.mint_address,
      nonce: _hexRandom(16), min_receive: Number(minimum),
    };
    button.disabled = true;
    button.innerHTML = '<span class="spinner"></span> Signing&hellip;';
    payload.signature = await signPayload(S.privateKey, payload);
    payload.public_key = await exportPublicKeyPEM(S.publicKey);
    button.innerHTML = '<span class="spinner"></span> Submitting&hellip;';
    const result = await api('POST', '/transaction', payload);
    if (result.message !== 'Transaction added') throw new Error(result.message || 'Token swap was rejected.');
    setAlert('swap-alert', `${source.symbol} → ${target.symbol} swap submitted atomically with 1% slippage protection. Mine a block to confirm it.`, 'ok');
    toast('Token swap submitted', 'ok');
  } catch (error) {
    setAlert('swap-alert', error.message || 'Token swap failed.');
  } finally {
    button.disabled = false;
    button.textContent = original;
  }
}

document.getElementById('btn-swap-tokens').addEventListener('click', submitStandaloneSwap);
document.getElementById('swap-source').addEventListener('change', renderSwapPane);
document.getElementById('swap-target').addEventListener('change', updateStandaloneSwapQuote);
document.getElementById('swap-amount').addEventListener('input', updateStandaloneSwapQuote);

function selectedToken() {
  const mint = document.getElementById('token-select').value;
  return TOKENS.find(token => token.mint_address === mint) || null;
}

function renderSelectedToken() {
  const token = selectedToken();
  const info = document.getElementById('token-selected-info');
  const transferButton = document.getElementById('btn-token-transfer');
  const mintButton = document.getElementById('btn-token-mint');
  const burnButton = document.getElementById('btn-token-burn');
  const burnNote = document.getElementById('token-burn-note');
  const authorityControls = document.getElementById('token-authority-controls');
  const poolControls = document.getElementById('token-pool-controls');
  const poolAddControls = document.getElementById('token-pool-add-controls');
  if (!token) {
    info.className = 'empty';
    info.innerHTML = emptyTokenMarkup('No held or DAD-managed tokens are available.');
    transferButton.style.display = 'none';
    mintButton.style.display = 'none';
    burnButton.style.display = 'none';
    if (burnNote) burnNote.hidden = true;
    authorityControls.style.display = 'none';
    poolControls.style.display = 'none';
    poolAddControls.style.display = 'none';
    return;
  }
  info.className = 'token-selected-info';
  const artwork = token.display_image || token.image;
  info.innerHTML = `${artwork ? `<img class="token-avatar" style="float:right;width:64px;height:64px" src="${escapeHtml(artwork)}" alt="${escapeHtml(token.name)} token image">` : ''}<div><strong>${escapeHtml(token.name)} (${escapeHtml(token.symbol)})</strong></div>
    <div class="token-address">MNT: ${escapeHtml(token.mint_address)}</div>
    <div class="token-address">DAD: ${escapeHtml(token.dad_address || 'revoked (fixed supply)')}</div>
    <div class="token-address">Your associated token account: ${escapeHtml(token.token_account_address || '—')} (${token.token_account_exists ? 'confirmed' : 'not created'})</div>
    <div class="token-balance">Your balance: ${formatTokenAmount(token.balance, token.decimals)} ${escapeHtml(token.symbol)}</div>
    <div class="token-address">Supply: ${formatTokenAmount(token.supply, token.decimals)} ${escapeHtml(token.symbol)}</div>
    <div class="token-address">Market price: ${escapeHtml(formatTokenPrice(token))}</div>
    <div class="token-address">Pool reserves: ${escapeHtml(token.pool_hlx_reserve || 0)} HLX / ${formatTokenAmount(token.pool_token_reserve, token.decimals)} ${escapeHtml(token.symbol)}</div>
    <div class="metadata-description">${escapeHtml(token.display_description || token.description || '')}</div>
    <div class="token-address">Metadata hash: ${escapeHtml(token.metadata_hash || '—')}</div>`;
  const controlsDad = token.dad_address === S.address;
  transferButton.style.display = tokenBalanceUnits(token) > 0n ? '' : 'none';
  mintButton.style.display = controlsDad ? '' : 'none';
  const canBurn = controlsDad && tokenBalanceUnits(token) > 0n;
  burnButton.style.display = canBurn ? '' : 'none';
  if (burnNote) burnNote.hidden = !canBurn;
  authorityControls.style.display = controlsDad ? '' : 'none';
  poolControls.style.display = controlsDad && !tokenPoolActive(token) ? '' : 'none';
  poolAddControls.style.display = controlsDad && tokenPoolActive(token) ? '' : 'none';
}

function renderTokens() {
  const list = document.getElementById('token-list');
  const select = document.getElementById('token-select');
  const held = heldTokens();
  const manageable = manageableTokens();
  const previous = select.value;

  list.innerHTML = nativeTokenCardMarkup() + held.map(tokenCardMarkup).join('');

  select.replaceChildren();
  if (!manageable.length) {
    const option = document.createElement('option');
    option.value = '';
    option.textContent = 'No held or DAD-managed tokens';
    select.appendChild(option);
  } else {
    for (const token of manageable) {
      const option = document.createElement('option');
      option.value = token.mint_address;
      const roles = [
        tokenBalanceUnits(token) > 0n ? 'holder' : '',
        token.dad_address === S.address ? 'DAD' : '',
      ].filter(Boolean).join(', ');
      option.textContent = `${token.symbol} - ${token.name} (${roles})`;
      select.appendChild(option);
    }
    if (manageable.some(token => token.mint_address === previous)) {
      select.value = previous;
    }
  }
  renderSelectedToken();
  renderDashboardTokens();
  renderDiscoveryTokens();
  renderSwapPane();
}

async function loadTokens() {
  if (!hasActiveSession()) return;
  const list = document.getElementById('token-list');
  list.innerHTML = '<div class="empty">Loading&hellip;</div>';
  try {
    const [result, balance, stats] = await Promise.all([
      api('GET', `/tokens?holder=${encodeURIComponent(S.address)}`),
      api('GET', `/balance/${S.address}`),
      api('GET', '/stats'),
    ]);
    TOKENS = result.tokens || [];
    await hydrateTokenCollection(TOKENS);
    HLX_BALANCE = Number(balance.balance || 0);
    HLX_TOTAL_SUPPLY = Number(stats.total_supply || 0);
    NETWORK_STATS = stats;
    renderSendAssets();
    renderTokens();
  } catch (error) {
    list.innerHTML = `<div class="empty">${escapeHtml(error.message || 'Could not load tokens.')}</div>`;
  }
}

document.getElementById('btn-refresh-tokens').addEventListener('click', loadTokens);
document.getElementById('btn-refresh-discover-tokens').addEventListener('click', loadTokens);
document.getElementById('token-select').addEventListener('change', renderSelectedToken);
document.querySelectorAll('.token-tab').forEach(tab =>
  tab.addEventListener('click', () => {
    showTokenPane(tab.dataset.tokenPane);
    if (tab.dataset.tokenPane === 'swap') renderSwapPane();
  }));
document.getElementById('btn-dash-tokens').addEventListener('click', () => {
  showPanel('tokens');
  showTokenPane('wallet');
});
document.addEventListener('click', event => {
  if (!event.target.closest('[data-open-token-create]')) return;
  showPanel('tokens');
  showTokenPane('create');
});

function openTokenManagement(mintAddress) {
  showPanel('tokens');
  const select = document.getElementById('token-select');
  if ([...select.options].some(option => option.value === mintAddress)) {
    select.value = mintAddress;
  }
  renderSelectedToken();
  showTokenPane('manage');
}

function openTokenMarket(mintAddress) {
  const token = TOKENS.find(item => item.mint_address === mintAddress);
  if (!token) return;
  showPanel('tokens');
  showTokenPane('discover');
  renderMarketToken(token);
}

function openNativeMarket() {
  showPanel('tokens');
  showTokenPane('discover');
  renderNativeAsset();
}

document.getElementById('token-list').addEventListener('click', event => {
  if (event.target.closest('[data-native-asset="HLX"]')) {
    openNativeMarket();
    return;
  }
  const card = event.target.closest('[data-token-mint]');
  if (!card) return;
  openTokenMarket(card.dataset.tokenMint);
});
document.getElementById('dash-token-list').addEventListener('click', event => {
  if (event.target.closest('[data-native-asset="HLX"]')) {
    openNativeMarket();
    return;
  }
  const card = event.target.closest('[data-token-mint]');
  if (!card) return;
  openTokenMarket(card.dataset.tokenMint);
});
document.getElementById('token-discovery-list').addEventListener('click', event => {
  if (event.target.closest('[data-native-asset="HLX"]')) {
    renderNativeAsset();
    return;
  }
  const card = event.target.closest('[data-token-mint]');
  if (!card) return;
  const token = TOKENS.find(item => item.mint_address === card.dataset.tokenMint);
  if (token) renderMarketToken(token);
});
document.getElementById('token-search').addEventListener('input', renderDiscoveryTokens);
document.getElementById('token-market-detail').addEventListener('input', event => {
  if (event.target.matches('#market-buy-hlx, #market-sell-token')) updateMarketQuotes();
  if (event.target.matches('#market-swap-source')) updateTokenSwapQuote();
});
document.getElementById('token-market-detail').addEventListener('input', event => {
  if (!event.target.matches('#token-chart-height, #token-chart-width')) return;
  const value = Number(event.target.value);
  if (!Number.isFinite(value)) return;
  const container = document.getElementById('token-price-chart');
  const viewport = container?.querySelector('.chart-viewport');
  if (event.target.matches('#token-chart-height')) {
    TOKEN_CHART_HEIGHT = Math.min(TOKEN_CHART_MAX_HEIGHT, Math.max(TOKEN_CHART_MIN_HEIGHT, value));
    if (viewport) viewport.style.height = `${TOKEN_CHART_HEIGHT}px`;
  } else {
    TOKEN_CHART_WIDTH = Math.min(TOKEN_CHART_MAX_WIDTH, Math.max(TOKEN_CHART_MIN_WIDTH, value));
    if (viewport) viewport.style.width = `${TOKEN_CHART_WIDTH}px`;
  }
  const label = event.target.nextElementSibling;
  if (label) label.textContent = `${value}px`;
});
document.getElementById('token-market-detail').addEventListener('change', event => {
  if (event.target.matches('#market-swap-target')) updateTokenSwapQuote();
  if (event.target.matches('#token-chart-height, #token-chart-width')) {
    const container = document.getElementById('token-price-chart');
    if (container && TOKEN_CHART_TOKEN) renderTokenPriceChart(container, TOKEN_CHART_TOKEN, TOKEN_CHART_POINTS);
  }
});

// Candle interval buttons (Minute / Hour / Day / Month / Auto).
document.getElementById('token-market-detail').addEventListener('click', event => {
  const button = event.target.closest('[data-chart-range]');
  if (!button) return;
  const container = document.getElementById('token-price-chart');
  if (!container || !TOKEN_CHART_TOKEN) return;
  const range = TOKEN_CHART_RANGES.find(item => item.key === button.dataset.chartRange);
  if (!range) return;
  TOKEN_CHART_INTERVAL = range.seconds;
  if (range.seconds) {
    // Frame a sensible window at this granularity: up to ~60 candles ending now.
    const { earliest, latest } = tokenChartBounds(TOKEN_CHART_POINTS);
    const span = Math.min(Math.max(latest - earliest, range.seconds), range.seconds * 60);
    TOKEN_CHART_VIEW = { start: latest - span, end: latest };
  } else {
    TOKEN_CHART_VIEW = null; // Auto refits the whole history.
  }
  renderTokenPriceChart(container, TOKEN_CHART_TOKEN, TOKEN_CHART_POINTS);
});

// Start date/time input: pick exactly when the chart begins. Re-rendering with
// the cropped window lets the Y-axis rescale, so small values stay readable
// once early spikes are excluded.
document.getElementById('token-market-detail').addEventListener('change', event => {
  if (!event.target.matches('#token-chart-start')) return;
  const container = document.getElementById('token-price-chart');
  if (!container || !TOKEN_CHART_TOKEN) return;
  const chosenStart = new Date(event.target.value).getTime() / 1000;
  if (!Number.isFinite(chosenStart)) return;
  const { latest } = tokenChartBounds(TOKEN_CHART_POINTS);
  TOKEN_CHART_VIEW = { start: chosenStart, end: latest };
  renderTokenPriceChart(container, TOKEN_CHART_TOKEN, TOKEN_CHART_POINTS);
});

document.getElementById('btn-token-create').addEventListener('click', async () => {
  if (!hasActiveSession()) return;
  const btn = document.getElementById('btn-token-create');
  const decimals = Number(document.getElementById('token-decimals').value);
  const dadAddress = (document.getElementById('token-dad-address').value.trim() || S.address).toLowerCase();
  setAlert('token-create-alert', '');
  try {
    if (!Number.isInteger(decimals) || decimals < 0 || decimals > 9) throw new Error('Decimals must be an integer from 0 to 9.');
    if (!/^[0-9a-f]{40}$/.test(dadAddress)) throw new Error('DAD must be a 40-character hexadecimal wallet address.');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Loading metadata&hellip;';
    const { uri, name, symbol, description, image } = await loadTokenMetadata();
    const metadata_hash = await tokenMetadataHash({ name, symbol, description, image });
    const nonce = _hexRandom(16);
    const mintAddress = await tokenMintAddress(S.address, nonce);
    const payload = {
      tx_type: 'token_create', sender: S.address, receiver: S.address,
      amount: 0, mint_address: mintAddress, dad_address: dadAddress,
      nonce, name, symbol, description, image, metadata_hash, decimals, uri,
    };
    btn.innerHTML = '<span class="spinner"></span> Signing&hellip;';
    payload.signature = await signPayload(S.privateKey, payload);
    payload.public_key = await exportPublicKeyPEM(S.publicKey);
    btn.innerHTML = '<span class="spinner"></span> Submitting&hellip;';
    const result = await api('POST', '/transaction', payload);
    if (result.message !== 'Transaction added') throw new Error(result.message || 'Token creation was rejected.');
    setAlert('token-create-alert', `Submitted with zero supply. Mine a block to confirm it.\nMNT: ${mintAddress}\nDAD: ${dadAddress}`, 'ok');
    toast(`${symbol} token submitted`, 'ok');
  } catch (error) {
    setAlert('token-create-alert', error.message || 'Could not create token.');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Create Token';
  }
});

async function submitMarketTrade(txType) {
  if (!hasActiveSession()) return;
  const token = TOKENS.find(item => item.mint_address === MARKET_MINT);
  if (!token || !tokenPoolActive(token)) return;
  const button = document.getElementById(txType === 'token_buy' ? 'btn-market-buy' : 'btn-market-sell');
  setAlert('market-alert', '');
  try {
    let amount;
    let estimated;
    if (txType === 'token_buy') {
      const value = document.getElementById('market-buy-hlx').value.trim();
      if (!/^[1-9]\d*$/.test(value)) throw new Error('Buy amount must be a positive whole HLX amount.');
      amount = Number(value);
      if (!Number.isSafeInteger(amount)) throw new Error('Buy amount is above the network limit.');
      estimated = swapQuote(BigInt(amount), token.pool_hlx_reserve, token.pool_token_reserve);
    } else {
      amount = parseTokenAmount(document.getElementById('market-sell-token').value, token.decimals);
      if (BigInt(amount) > tokenBalanceUnits(token)) throw new Error('Sale exceeds your confirmed token balance.');
      estimated = swapQuote(BigInt(amount), token.pool_token_reserve, token.pool_hlx_reserve);
    }
    if (estimated <= 0n) throw new Error('This trade is too small for the current pool reserves.');
    const minimum = estimated > 1n ? estimated * 99n / 100n : 1n;
    if (minimum > BigInt(Number.MAX_SAFE_INTEGER)) throw new Error('Trade output is above the network limit.');
    const payload = {
      tx_type: txType,
      sender: S.address,
      receiver: S.address,
      amount,
      mint_address: token.mint_address,
      nonce: _hexRandom(16),
      min_receive: Number(minimum),
    };
    button.disabled = true;
    const original = button.textContent;
    button.innerHTML = '<span class="spinner"></span> Signing&hellip;';
    try {
      payload.signature = await signPayload(S.privateKey, payload);
      payload.public_key = await exportPublicKeyPEM(S.publicKey);
      const result = await api('POST', '/transaction', payload);
      if (result.message !== 'Transaction added') throw new Error(result.message || 'Trade was rejected.');
      setAlert('market-alert', `${txType === 'token_buy' ? 'Buy' : 'Sell'} submitted with 1% slippage protection. Mine a block to update the pool price.`, 'ok');
      toast('Token trade submitted', 'ok');
    } finally {
      button.disabled = false;
      button.textContent = original;
    }
  } catch (error) {
    setAlert('market-alert', error.message || 'Token trade failed.');
  }
}

async function submitTokenSwap() {
  if (!hasActiveSession()) return;
  const source = TOKENS.find(item => item.mint_address === MARKET_MINT);
  const targetMint = document.getElementById('market-swap-target')?.value;
  const target = TOKENS.find(item => item.mint_address === targetMint);
  const button = document.getElementById('btn-market-swap');
  if (!source || !target || !button || !tokenPoolActive(source) || !tokenPoolActive(target)) return;
  setAlert('market-alert', '');
  const original = button.textContent;
  try {
    const amount = parseTokenAmount(document.getElementById('market-swap-source').value, source.decimals);
    if (BigInt(amount) > tokenBalanceUnits(source)) throw new Error(`Swap exceeds your confirmed ${source.symbol} balance.`);
    const { received } = tokenSwapQuote(source, target, BigInt(amount));
    if (received <= 0n) throw new Error('This swap is too small for the current pool liquidity.');
    const minimum = received > 1n ? received * 99n / 100n : 1n;
    if (minimum > BigInt(Number.MAX_SAFE_INTEGER)) throw new Error('Swap output is above the network limit.');
    const payload = {
      tx_type: 'token_swap', sender: S.address, receiver: S.address,
      amount, mint_address: source.mint_address,
      target_mint_address: target.mint_address,
      nonce: _hexRandom(16), min_receive: Number(minimum),
    };
    button.disabled = true;
    button.innerHTML = '<span class="spinner"></span> Signing&hellip;';
    payload.signature = await signPayload(S.privateKey, payload);
    payload.public_key = await exportPublicKeyPEM(S.publicKey);
    button.innerHTML = '<span class="spinner"></span> Submitting&hellip;';
    const result = await api('POST', '/transaction', payload);
    if (result.message !== 'Transaction added') throw new Error(result.message || 'Token swap was rejected.');
    setAlert('market-alert', `${source.symbol} → ${target.symbol} swap submitted atomically with 1% slippage protection.`, 'ok');
    toast('Token swap submitted', 'ok');
  } catch (error) {
    setAlert('market-alert', error.message || 'Token swap failed.');
  } finally {
    button.disabled = false;
    button.textContent = original;
  }
}

document.getElementById('token-market-detail').addEventListener('click', event => {
  if (event.target.closest('#btn-market-buy')) submitMarketTrade('token_buy');
  if (event.target.closest('#btn-market-sell')) submitMarketTrade('token_sell');
  if (event.target.closest('#btn-market-swap')) submitTokenSwap();
});

document.getElementById('btn-token-create-pool').addEventListener('click', async () => {
  if (!hasActiveSession()) return;
  const token = selectedToken();
  const button = document.getElementById('btn-token-create-pool');
  setAlert('token-pool-alert', '');
  try {
    if (!token || token.dad_address !== S.address) throw new Error('Only the current DAD can create this pool.');
    if (tokenPoolActive(token)) throw new Error('This token already has an exchange pool.');
    const amount = Number(token.balance || 0);
    if (!Number.isSafeInteger(amount) || amount <= 0) throw new Error('Mint tokens to the DAD wallet before creating its pool.');
    const hlxText = document.getElementById('token-pool-hlx-amount').value.trim();
    if (!/^[1-9]\d*$/.test(hlxText)) throw new Error('HLX liquidity must be a positive whole number.');
    const hlx_amount = Number(hlxText);
    if (!Number.isSafeInteger(hlx_amount)) throw new Error('HLX liquidity is above the network limit.');
    const payload = {
      tx_type: 'token_pool_create', sender: S.address, receiver: S.address,
      amount, hlx_amount, mint_address: token.mint_address, nonce: _hexRandom(16),
    };
    button.disabled = true;
    const original = button.textContent;
    button.innerHTML = '<span class="spinner"></span> Signing&hellip;';
    try {
      payload.signature = await signPayload(S.privateKey, payload);
      payload.public_key = await exportPublicKeyPEM(S.publicKey);
      const result = await api('POST', '/transaction', payload);
      if (result.message !== 'Transaction added') throw new Error(result.message || 'Pool creation was rejected.');
      setAlert('token-pool-alert', 'Exchange pool submitted. Mine a block to activate trading.', 'ok');
      toast('Exchange pool submitted', 'ok');
    } finally {
      button.disabled = false;
      button.textContent = original;
    }
  } catch (error) {
    setAlert('token-pool-alert', error.message || 'Could not create exchange pool.');
  }
});

document.getElementById('btn-token-add-pool-liquidity').addEventListener('click', async () => {
  if (!hasActiveSession()) return;
  const token = selectedToken();
  const button = document.getElementById('btn-token-add-pool-liquidity');
  setAlert('token-pool-add-alert', '');
  try {
    if (!token || token.dad_address !== S.address) throw new Error('Only the current DAD can add direct HLX liquidity.');
    if (!tokenPoolActive(token)) throw new Error('Create the exchange pool before adding HLX liquidity.');
    const value = document.getElementById('token-pool-add-hlx-amount').value.trim();
    if (!/^[1-9]\d*$/.test(value)) throw new Error('Liquidity must be a positive whole HLX amount.');
    const amount = Number(value);
    if (!Number.isSafeInteger(amount)) throw new Error('Liquidity is above the network limit.');
    const payload = {
      tx_type: 'token_pool_add_hlx', sender: S.address, receiver: S.address,
      amount, mint_address: token.mint_address, nonce: _hexRandom(16),
    };
    button.disabled = true;
    const original = button.textContent;
    button.innerHTML = '<span class="spinner"></span> Signing&hellip;';
    try {
      payload.signature = await signPayload(S.privateKey, payload);
      payload.public_key = await exportPublicKeyPEM(S.publicKey);
      const result = await api('POST', '/transaction', payload);
      if (result.message !== 'Transaction added') throw new Error(result.message || 'Liquidity addition was rejected.');
      setAlert('token-pool-add-alert', 'HLX liquidity submitted. Mine a block to update the pool.', 'ok');
      toast('HLX liquidity submitted', 'ok');
    } finally {
      button.disabled = false;
      button.textContent = original;
    }
  } catch (error) {
    setAlert('token-pool-add-alert', error.message || 'Could not add HLX liquidity.');
  }
});

async function submitTokenAction(txType) {
  if (!hasActiveSession()) return;
  const token = selectedToken();
  setAlert('token-action-alert', '');
  try {
    if (!token) throw new Error('Select a confirmed token first.');
    if (txType === 'token_mint' && token.dad_address !== S.address) throw new Error('Only the DAD authority can mint this token.');
    const receiver = document.getElementById('token-recipient').value.trim().toLowerCase();
    if (!/^[0-9a-f]{40}$/.test(receiver)) throw new Error('Recipient must be a 40-character hexadecimal address.');
    const amount = parseTokenAmount(document.getElementById('token-amount').value, token.decimals);
    const payload = {
      tx_type: txType, sender: S.address, receiver, amount,
      mint_address: token.mint_address, nonce: _hexRandom(16),
    };
    const button = document.getElementById(txType === 'token_mint' ? 'btn-token-mint' : 'btn-token-transfer');
    button.disabled = true;
    const original = button.textContent;
    button.innerHTML = '<span class="spinner"></span> Signing&hellip;';
    try {
      payload.signature = await signPayload(S.privateKey, payload);
      payload.public_key = await exportPublicKeyPEM(S.publicKey);
      const result = await api('POST', '/transaction', payload);
      if (result.message !== 'Transaction added') throw new Error(result.message || 'Token transaction was rejected.');
      setAlert('token-action-alert', `${txType === 'token_mint' ? 'Mint' : 'Transfer'} submitted. Mine a block to confirm it.`, 'ok');
      toast('Token transaction submitted', 'ok');
    } finally {
      button.disabled = false;
      button.textContent = original;
    }
  } catch (error) {
    setAlert('token-action-alert', error.message || 'Token transaction failed.');
  }
}

document.getElementById('btn-token-transfer').addEventListener('click', () => submitTokenAction('token_transfer'));
document.getElementById('btn-token-mint').addEventListener('click', () => submitTokenAction('token_mint'));

async function submitTokenBurn() {
  if (!hasActiveSession()) return;
  const token = selectedToken();
  setAlert('token-action-alert', '');
  try {
    if (!token) throw new Error('Select a confirmed token first.');
    if (token.dad_address !== S.address) throw new Error('Only the DAD authority can burn this token.');
    const amount = parseTokenAmount(document.getElementById('token-amount').value, token.decimals);
    if (BigInt(amount) > tokenBalanceUnits(token)) throw new Error('You cannot burn more than your DAD balance.');
    // A burn destroys tokens from the DAD's own balance, so it is sent to self.
    const payload = {
      tx_type: 'token_burn', sender: S.address, receiver: S.address, amount,
      mint_address: token.mint_address, nonce: _hexRandom(16),
    };
    const button = document.getElementById('btn-token-burn');
    button.disabled = true;
    const original = button.textContent;
    button.innerHTML = '<span class="spinner"></span> Signing&hellip;';
    try {
      payload.signature = await signPayload(S.privateKey, payload);
      payload.public_key = await exportPublicKeyPEM(S.publicKey);
      const result = await api('POST', '/transaction', payload);
      if (result.message !== 'Transaction added') throw new Error(result.message || 'Burn was rejected.');
      setAlert('token-action-alert', 'Burn submitted. Mine a block to reduce the supply.', 'ok');
      toast('Burn submitted', 'ok');
    } finally {
      button.disabled = false;
      button.textContent = original;
    }
  } catch (error) {
    setAlert('token-action-alert', error.message || 'Burn failed.');
  }
}
document.getElementById('btn-token-burn').addEventListener('click', submitTokenBurn);

async function submitDadChange(revoke = false) {
  if (!hasActiveSession()) return;
  const token = selectedToken();
  setAlert('token-action-alert', '');
  try {
    if (!token || token.dad_address !== S.address) throw new Error('Only the current DAD authority can make this change.');
    const receiver = revoke
      ? '0'.repeat(40)
      : document.getElementById('token-new-dad').value.trim().toLowerCase();
    if (!/^[0-9a-f]{40}$/.test(receiver)) throw new Error('New DAD must be a 40-character hexadecimal address.');
    if (receiver === S.address) throw new Error('The new DAD is already the current authority.');
    if (revoke && !window.confirm('Permanently revoke DAD authority? No one will ever be able to mint more of this token.')) return;
    const button = document.getElementById(revoke ? 'btn-token-revoke-dad' : 'btn-token-set-dad');
    const original = button.textContent;
    button.disabled = true;
    button.innerHTML = '<span class="spinner"></span> Signing&hellip;';
    try {
      const payload = {
        tx_type: 'token_set_authority', sender: S.address, receiver, amount: 0,
        mint_address: token.mint_address, nonce: _hexRandom(16),
      };
      payload.signature = await signPayload(S.privateKey, payload);
      payload.public_key = await exportPublicKeyPEM(S.publicKey);
      const result = await api('POST', '/transaction', payload);
      if (result.message !== 'Transaction added') throw new Error(result.message || 'DAD authority change was rejected.');
      setAlert('token-action-alert', `${revoke ? 'DAD revocation' : 'DAD transfer'} submitted. Mine a block to confirm it.`, 'ok');
      toast('DAD authority change submitted', 'ok');
    } finally {
      button.disabled = false;
      button.textContent = original;
    }
  } catch (error) {
    setAlert('token-action-alert', error.message || 'DAD authority change failed.');
  }
}

document.getElementById('btn-token-set-dad').addEventListener('click', () => submitDadChange(false));
document.getElementById('btn-token-revoke-dad').addEventListener('click', () => submitDadChange(true));

async function loadPending() {
  if (!hasActiveSession()) return;
  const el = document.getElementById('pending-list');
  el.innerHTML = '<div class="empty">Loading…</div>';
  try {
    const r   = await api('GET', '/pending');
    const txs = r.pending || [];
    if (!txs.length) { el.innerHTML = '<div class="empty">No pending transactions</div>'; return; }
    el.innerHTML = `<div class="tx-list">${txs.map(tx => {
      const type = tx.tx_type || 'transfer';
      const label = type === 'token_create' ? `Create ${tx.symbol || 'token'}`
        : type === 'token_mint' ? 'Mint token'
        : type === 'token_set_authority' ? 'Change DAD authority'
        : type === 'token_transfer' ? 'Transfer token'
        : type === 'token_pool_create' ? 'Create exchange pool'
        : type === 'token_pool_add_hlx' ? 'Add HLX liquidity'
        : type === 'token_buy' ? 'Buy token'
        : type === 'token_sell' ? 'Sell token'
        : type === 'token_swap' ? 'Swap tokens' : 'Pending';
      const amount = ['transfer', 'token_buy', 'token_pool_add_hlx'].includes(type)
        ? `${tx.amount} HLX` : `${tx.amount} base units`;
      const cancelButton = tx.sender === S.address && tx.tx_id
        ? `<button class="btn btn-danger btn-sm mt8" type="button" data-cancel-tx-id="${escapeHtml(tx.tx_id)}">Cancel pending</button>`
        : '';
      return `
      <div class="tx-row tx-row-action" role="button" tabindex="0" data-tx-id="${escapeHtml(tx.tx_id || '')}">
        <div class="tx-icon out">→</div>
        <div class="tx-body">
          <div class="tx-label">${escapeHtml(label)}</div>
          <div class="tx-sub">From: ${escapeHtml(short(tx.sender))}</div>
          <div class="tx-sub">To:&nbsp;&nbsp;${escapeHtml(short(tx.receiver))}</div>
        </div>
        <div class="tx-right"><div class="tx-amount out">${escapeHtml(amount)}</div>${cancelButton}</div>
      </div>`;
    }).join('')}</div>`;
  } catch (_) { el.innerHTML = '<div class="empty">Failed to load</div>'; }
}

document.getElementById('btn-refresh-pending').addEventListener('click', loadPending);
document.addEventListener('click', async event => {
  const button = event.target.closest('[data-cancel-tx-id]');
  if (!button || !hasActiveSession()) return;
  event.preventDefault();
  event.stopPropagation();
  const txId = button.dataset.cancelTxId;
  if (!window.confirm('Cancel this pending transaction? Confirmed transactions cannot be cancelled.')) return;
  button.disabled = true;
  button.textContent = 'Cancelling…';
  setAlert('pending-alert', '');
  try {
    const payload = { action: 'cancel_pending', sender: S.address, tx_id: txId };
    const signature = await signPayload(S.privateKey, payload);
    const publicKeyPem = await exportPublicKeyPEM(S.publicKey);
    const result = await api('POST', `/transaction/${txId}/cancel`, {
      sender: S.address,
      signature,
      public_key: publicKeyPem,
    });
    if (!result.cancelled) throw new Error(result.message || 'Cancellation was rejected.');
    toast('Pending transaction cancelled', 'ok');
    await loadPending();
    loadDashboard();
  } catch (error) {
    setAlert('pending-alert', error.message || 'Could not cancel the transaction.');
    button.disabled = false;
    button.textContent = 'Cancel pending';
  }
});

// ============================================================
// SECTION 12 — History
// ============================================================
document.getElementById('btn-refresh-history').addEventListener('click', loadHistory);
async function loadHistory() {
  if (!hasActiveSession()) return;
  const el = document.getElementById('history-list');
  el.innerHTML = '<div class="empty">Loading…</div>';
  try {
    const r   = await api('GET', `/history/${S.address}`);
    const txs = r.transactions || [];
    if (!txs.length) { el.innerHTML = '<div class="empty">No transactions yet</div>'; return; }
    el.innerHTML = `<div class="tx-list">${txs.map(tx => {
      const isSys = tx.sender === 'SYSTEM';
      const type  = tx.tx_type || 'transfer';
      const tokenTx = type !== 'transfer';
      const dir   = isSys ? 'sys' : tx.direction;
      const icon  = isSys ? '★' : dir === 'in' ? '↓' : '↑';
      const label = type === 'token_create' ? `Created ${tx.symbol || 'token'}`
                  : type === 'token_mint' ? 'Token mint'
                  : type === 'token_set_authority' ? 'DAD authority change'
                  : type === 'token_transfer' ? (dir === 'in' ? 'Token received' : 'Token sent')
                  : type === 'token_pool_create' ? 'Exchange pool created'
                  : type === 'token_pool_add_hlx' ? 'HLX liquidity added'
                  : type === 'token_buy' ? 'Token purchased'
                  : type === 'token_sell' ? 'Token sold'
                  : type === 'token_swap' ? 'Tokens swapped'
                  : isSys ? 'Mining Reward' : dir === 'in' ? 'Received' : 'Sent';
      const peer  = isSys ? 'Block reward'
                  : dir === 'in' ? `From: ${short(tx.sender)}` : `To: ${short(tx.receiver)}`;
      const sign  = dir === 'out' ? '−' : '+';
       return `<div class="tx-row tx-row-action" role="button" tabindex="0" data-tx-id="${escapeHtml(tx.tx_id || '')}">
        <div class="tx-icon ${dir}">${icon}</div>
        <div class="tx-body">
          <div class="tx-label">${escapeHtml(label)}</div>
          <div class="tx-sub">${escapeHtml(peer)}</div>
          <div class="tx-sub">Block #${escapeHtml(tx.block)} · ${escapeHtml(fmtDate(tx.timestamp))}</div>
        </div>
        <div class="tx-right">
          <div class="tx-amount ${dir}">${escapeHtml(`${sign}${tx.amount} ${['token_buy', 'token_pool_add_hlx'].includes(type) || !tokenTx ? 'HLX' : 'base units'}`)}</div>
          <div class="tx-meta">${escapeHtml(tx.tx_id ? tx.tx_id.slice(0,10)+'…' : '—')}</div>
        </div>
       </div>`;
    }).join('')}</div>`;
  } catch (_) { el.innerHTML = '<div class="empty">Failed to load history</div>'; }
}

// ============================================================
// SECTION 13 — Nodes panel
// ============================================================
function showSyncPill(text) {
  document.getElementById('hdr-sync-text').textContent = text;
  document.getElementById('hdr-sync-pill').classList.add('visible');
}
function hideSyncPill() {
  document.getElementById('hdr-sync-pill').classList.remove('visible');
}

document.getElementById('btn-refresh-nodes').addEventListener('click', loadNodes);
document.getElementById('btn-refresh-activity').addEventListener('click', () => loadActivity(ACTIVITY_PAGE));
document.getElementById('activity-pagination').addEventListener('click', event => {
  const button = event.target.closest('[data-activity-page]');
  if (!button || button.disabled) return;
  loadActivity(Number(button.dataset.activityPage));
});

document.getElementById('btn-sync-peers').addEventListener('click', async () => {
  const btn = document.getElementById('btn-sync-peers');
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Syncing…';
  showSyncPill('Syncing…');
  try {
    await api('POST', '/nodes/sync_now');
    toast('Sync + audit started in background', 'ok');
    setTimeout(() => { loadNodes(); hideSyncPill(); }, 2000);
  } catch (error) { toast(error.message || 'Sync failed', 'err'); hideSyncPill(); }
  finally { btn.disabled = false; btn.textContent = '⇄ Pull longest chain'; }
});

document.getElementById('btn-add-peer').addEventListener('click', async () => {
  const url = document.getElementById('peer-url').value.trim();
  setAlert('nodes-alert', '');
  if (!url) { setAlert('nodes-alert', 'Enter a peer URL first.'); return; }
  try {
    const payload = { node: url };
    if (!NODE_URL.endsWith('/api')) payload.self_url = window.location.origin;
    const r = await api('POST', '/nodes/register', payload);
    setAlert('nodes-alert', 'Peer added — verifying reachability…', 'ok');
    document.getElementById('peer-url').value = '';
    loadNodes();
    // Best-effort immediate probe so the status updates quickly instead of
    // waiting for the next background sync. Ignored if admin routes are off.
    try { await api('POST', '/nodes/sync_now'); } catch (_) {}
    setTimeout(loadNodes, 2500);
  } catch (error) { setAlert('nodes-alert', error.message || 'Could not reach that peer.'); }
});

document.getElementById('peer-url').addEventListener('keydown', e => {
  if (e.key === 'Enter') document.getElementById('btn-add-peer').click();
});

document.getElementById('btn-discover').addEventListener('click', async () => {
  const btn = document.getElementById('btn-discover');
  const res = document.getElementById('discover-results');
  setAlert('discover-alert', '');
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Scanning…';
  res.innerHTML = '<div class="empty" style="padding:12px">Probing local network…</div>';
  try {
    const r     = await api('GET', '/nodes/discover');
    const found = r.found || [];
    const added = r.newly_added || [];
    if (!found.length) {
      res.innerHTML = '<div class="empty" style="padding:12px">No other Helix nodes found.</div>';
    } else {
      res.innerHTML = found.map(url => {
        const isNew = added.includes(url);
        return `<div class="peer-row"><span>${escapeHtml(url)}</span>
          <span class="peer-status">
            <div class="dot" style="${isNew ? '' : 'background:var(--muted)'}"></div>
            ${isNew ? '<span style="color:var(--green);font-size:12px">Newly added</span>'
                    : '<span style="color:var(--muted);font-size:12px">Already known</span>'}
          </span></div>`;
      }).join('');
      if (added.length) { toast(`Found ${added.length} new node${added.length > 1 ? 's' : ''}`, 'ok'); loadNodes(); }
      else toast('No new nodes — all already known');
    }
  } catch (_) {
    setAlert('discover-alert', 'Discovery failed — node may be unreachable.');
    res.innerHTML = '';
  } finally { btn.disabled = false; btn.innerHTML = '🔍&nbsp; Scan for Nodes Now'; }
});

document.getElementById('btn-run-audit').addEventListener('click', () => runAudit(false));
document.getElementById('btn-load-cached-audit').addEventListener('click', () => runAudit(true));

async function runAudit(cached) {
  const btn = document.getElementById('btn-run-audit');
  const res = document.getElementById('audit-results');
  setAlert('audit-alert', ''); btn.disabled = true; btn.innerHTML = '<span class="spinner"></span>';
  res.innerHTML = '<div class="empty">Running audit…</div>';
  showSyncPill('Auditing…');
  try {
    const r = await api('GET', cached ? '/nodes/audit/cached' : '/nodes/audit');
    if (r.message === 'No audit run yet') {
      res.innerHTML = '<div class="empty">No audit has run yet — click "Run Full Audit".</div>';
      return;
    }
    renderAudit(r);
  } catch (_) { setAlert('audit-alert', 'Audit failed.'); res.innerHTML = ''; }
  finally { btn.disabled = false; btn.textContent = 'Run Full Audit'; hideSyncPill(); }
}

let AUDIT_DATA = null;
let AUDIT_PAGE = 1;
const AUDIT_PAGE_SIZE = 25;

function renderAudit(data) {
  AUDIT_DATA = data;
  AUDIT_PAGE = 1;
  renderAuditView();
}

function renderAuditView() {
  const data = AUDIT_DATA;
  if (!data) return;
  const res       = document.getElementById('audit-results');
  const li        = data.local_integrity || {};
  const blocks    = li.blocks || [];
  const bad       = blocks.filter(b => !b.ok);
  const conflicts = data.conflicts || [];
  const fetched   = data.fetched_blocks || [];
  const allOk     = li.ok && !conflicts.length;
  const summaryHtml = `<div class="audit-summary ${allOk ? 'ok' : 'bad'}">
    <div class="audit-big">${allOk ? '✓' : '✗'}</div>
    <div><strong>${allOk ? 'Chain intact' : 'Issues found'}</strong><br>
      <span style="font-size:12px">${escapeHtml(blocks.length)} blocks · ${escapeHtml(bad.length)} fault(s) · ${escapeHtml(conflicts.length)} conflict(s) · ${escapeHtml(fetched.length)} fetched · ${escapeHtml(data.peers_checked||0)} peers</span>
    </div></div>`;

  // Always surface any faulty blocks in full, even when the list is paginated.
  const faultsHtml = bad.length ? `<div class="card-title" style="margin-bottom:8px">Faulty blocks</div>
    <div class="audit-grid" style="margin-bottom:16px">
      <div class="audit-hdr">#</div><div class="audit-hdr">Hash</div><div class="audit-hdr">Status</div>
      ${bad.map(b => `
        <div>${escapeHtml(b.index)}</div>
        <div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(b.stored_hash ? String(b.stored_hash).slice(0,20)+'…' : '—')}</div>
        <div class="audit-fail">✗ FAIL</div>
        <div class="audit-reason">⚠ ${escapeHtml(b.reason || 'Unknown validation failure')}</div>
      `).join('')}</div>` : '';

  // Paginate the full block list so it does not run on for hundreds of rows.
  const totalPages = Math.max(1, Math.ceil(blocks.length / AUDIT_PAGE_SIZE));
  AUDIT_PAGE = Math.min(Math.max(1, AUDIT_PAGE), totalPages);
  const start = (AUDIT_PAGE - 1) * AUDIT_PAGE_SIZE;
  const pageBlocks = blocks.slice(start, start + AUDIT_PAGE_SIZE);
  const pagerHtml = blocks.length > AUDIT_PAGE_SIZE ? `<div class="audit-pager" style="display:flex;align-items:center;justify-content:center;gap:12px;margin-bottom:12px">
      <button class="btn btn-ghost btn-sm" data-audit-page="prev"${AUDIT_PAGE <= 1 ? ' disabled' : ''}>‹ Prev</button>
      <span style="font-size:12px;color:var(--muted)">Blocks ${start + 1}–${Math.min(start + AUDIT_PAGE_SIZE, blocks.length)} of ${blocks.length} · page ${AUDIT_PAGE}/${totalPages}</span>
      <button class="btn btn-ghost btn-sm" data-audit-page="next"${AUDIT_PAGE >= totalPages ? ' disabled' : ''}>Next ›</button>
    </div>` : '';
  const tableHtml = `${pagerHtml}<div class="audit-grid" style="margin-bottom:16px">
    <div class="audit-hdr">#</div><div class="audit-hdr">Hash</div><div class="audit-hdr">Status</div>
    ${pageBlocks.map(b => `
      <div>${escapeHtml(b.index)}</div>
      <div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(b.stored_hash ? String(b.stored_hash).slice(0,20)+'…' : '—')}</div>
      <div class="${b.ok ? 'audit-ok' : 'audit-fail'}">${b.ok ? '✓ OK' : '✗ FAIL'}</div>
      ${!b.ok ? `<div class="audit-reason">⚠ ${escapeHtml(b.reason || 'Unknown validation failure')}</div>` : ''}
    `).join('')}</div>`;
  const conflictHtml = conflicts.length ? `<div class="card-title" style="margin-bottom:10px">Peer Conflicts</div>
    ${conflicts.map(c => `<div class="peer-row" style="flex-direction:column;align-items:flex-start;gap:4px">
      <div style="color:var(--red);font-weight:600">Block #${escapeHtml(c.index)} — ${escapeHtml(c.reason || 'Conflict')}</div>
      ${c.our_hash  ? `<div>Our hash:&nbsp;<span style="color:var(--muted)">${escapeHtml(String(c.our_hash).slice(0,20))}…</span></div>`  : ''}
      ${c.peer_hash ? `<div>Peer hash:&nbsp;<span style="color:var(--muted)">${escapeHtml(String(c.peer_hash).slice(0,20))}…</span></div>` : ''}
      <div style="font-size:11px;color:var(--muted)">from ${escapeHtml(c.peer || 'unknown peer')}</div>
    </div>`).join('')}` : '';
  const unreachHtml = (data.unreachable||[]).length ? `<div class="card-title" style="margin:16px 0 10px">Unreachable</div>
    ${data.unreachable.map(u=>`<div class="peer-row"><span>${escapeHtml(u.peer || 'unknown peer')}</span><span style="color:var(--red);font-size:12px">${escapeHtml(u.error || 'unreachable')}</span></div>`).join('')}` : '';
  res.innerHTML = summaryHtml + faultsHtml + tableHtml + conflictHtml + unreachHtml;
}

document.getElementById('audit-results').addEventListener('click', event => {
  const button = event.target.closest('[data-audit-page]');
  if (!button) return;
  AUDIT_PAGE += button.dataset.auditPage === 'prev' ? -1 : 1;
  renderAuditView();
});

const ACTIVITY_PAGE_SIZE = 25;
let ACTIVITY_PAGE = 1;

function renderActivityTransactions(result) {
  const list = document.getElementById('activity-list');
  const transactions = result.transactions || [];
  if (!transactions.length) {
    list.innerHTML = '<div class="empty">No confirmed transactions yet.</div>';
    return;
  }
  list.innerHTML = `<div class="tx-list">${transactions.map(tx => {
    const type = tx.tx_type || (tx.sender === 'SYSTEM' ? 'reward' : 'transfer');
    const label = type === 'token_create' ? `Created ${tx.symbol || 'token'}`
      : type === 'token_mint' ? 'Minted token'
      : type === 'token_transfer' ? 'Transferred token'
      : type === 'token_set_authority' ? 'Changed DAD authority'
      : type === 'token_pool_create' ? 'Created exchange pool'
      : type === 'token_pool_add_hlx' ? 'Added HLX liquidity'
      : type === 'token_buy' ? 'Bought token'
      : type === 'token_sell' ? 'Sold token'
      : type === 'token_swap' ? 'Swapped tokens'
      : type === 'reward' ? 'Mining reward'
      : 'HLX transfer';
    const amount = type.startsWith('token_') && !['token_buy', 'token_pool_add_hlx'].includes(type)
      ? `${tx.amount} token base units` : `${tx.amount} HLX`;
    return `<div class="tx-row tx-row-action" role="button" tabindex="0" data-tx-id="${escapeHtml(tx.tx_id || '')}">
      <div class="tx-icon ${tx.sender === 'SYSTEM' ? 'in' : 'out'}">${tx.sender === 'SYSTEM' ? '+' : 'â†’'}</div>
      <div class="tx-body">
        <div class="tx-label">${escapeHtml(label)}</div>
        <div class="tx-sub">Block #${escapeHtml(tx.block)} Â· ${escapeHtml(short(tx.sender))} to ${escapeHtml(short(tx.receiver))}</div>
      </div>
      <div class="tx-amount">${escapeHtml(amount)}</div>
    </div>`;
  }).join('')}</div>`;
}

function activityPageNumbers(current, total) {
  if (total <= 7) return Array.from({length: total}, (_, index) => index + 1);
  const pages = new Set([1, total]);
  for (let page = Math.max(2, current - 2); page <= Math.min(total - 1, current + 2); page++) pages.add(page);
  const sorted = [...pages].sort((left, right) => left - right);
  const items = [];
  sorted.forEach((page, index) => {
    if (index && page - sorted[index - 1] > 1) items.push(null);
    items.push(page);
  });
  return items;
}

function renderActivityPagination(result) {
  const pagination = document.getElementById('activity-pagination');
  const current = Number(result.page || 1);
  const total = Number(result.pages || 1);
  if (Number(result.total || 0) === 0) {
    pagination.innerHTML = '';
    return;
  }
  const pageButtons = activityPageNumbers(current, total).map(page => page === null
    ? '<button class="page-btn" type="button" disabled aria-hidden="true">&hellip;</button>'
    : `<button class="page-btn${page === current ? ' active' : ''}" type="button" data-activity-page="${page}"${page === current ? ' aria-current="page"' : ''}>${page}</button>`
  ).join('');
  pagination.innerHTML = `<button class="page-btn" type="button" data-activity-page="${Math.max(1, current - 1)}"${current <= 1 ? ' disabled' : ''} aria-label="Previous page">&lsaquo;</button>${pageButtons}<button class="page-btn" type="button" data-activity-page="${Math.min(total, current + 1)}"${current >= total ? ' disabled' : ''} aria-label="Next page">&rsaquo;</button>`;
}

async function loadActivity(page = 1) {
  ACTIVITY_PAGE = Math.max(1, Number(page) || 1);
  const list = document.getElementById('activity-list');
  list.innerHTML = '<div class="empty">Loading&hellip;</div>';
  try {
    const offset = (ACTIVITY_PAGE - 1) * ACTIVITY_PAGE_SIZE;
    const result = await api('GET', `/transactions/recent?limit=${ACTIVITY_PAGE_SIZE}&offset=${offset}`);
    ACTIVITY_PAGE = Number(result.page || ACTIVITY_PAGE);
    renderActivityTransactions(result);
    renderActivityPagination(result);
  } catch (error) {
    list.innerHTML = `<div class="empty">${escapeHtml(error.message || 'Could not load blockchain activity.')}</div>`;
    document.getElementById('activity-pagination').innerHTML = '';
  }
}

function agoLabel(seconds) {
  if (!isFinite(seconds)) return 'never';
  seconds = Math.max(0, Math.round(seconds));
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  return `${Math.floor(seconds / 3600)}h ago`;
}

// A peer counts as connected only if the node has probed it successfully
// recently (fresh last_seen, no recent failures). The node's background worker
// probes peers every sync interval, so this reflects real reachability.
function peerStatus(record) {
  const seenAt = typeof record.last_seen === 'number' ? record.last_seen : null;
  const failures = Number(record.failures || 0);
  const age = seenAt === null ? Infinity : (Date.now() / 1000) - seenAt;
  if (seenAt !== null && age < 90 && failures === 0) {
    const parts = [
      record.latency_ms != null ? `${Math.round(record.latency_ms)} ms` : null,
      record.height != null ? `height ${record.height}` : null,
    ].filter(Boolean);
    return { label: 'connected', color: 'var(--green)', detail: parts.join(' · ') };
  }
  if (seenAt !== null) {
    const failNote = failures ? ` · ${failures} failed check${failures > 1 ? 's' : ''}` : '';
    return { label: 'disconnected', color: 'var(--red)', detail: `last seen ${agoLabel(age)}${failNote}` };
  }
  return {
    label: 'not responding', color: 'var(--red)',
    detail: failures ? `${failures} failed check${failures > 1 ? 's' : ''}` : 'not verified yet',
  };
}

async function loadNodes() {
  try {
    const [nodes, stats] = await Promise.all([
      api('GET', '/nodes'),
      api('GET', '/stats'),
    ]);
    const self  = nodes.node?.port ? `http://localhost:${nodes.node.port}` : window.location.origin;
    document.getElementById('node-self').textContent = `This node: ${self}`;
    const peers = nodes.peers || [];
    document.getElementById('peer-list').innerHTML = peers.length
      ? peers.map(p => {
          const record = typeof p === 'string' ? { url: p } : (p || {});
          const url = record.url || 'unknown peer';
          const status = peerStatus(record);
          const detail = status.detail
            ? ` <span style="color:var(--muted);font-size:11px">(${escapeHtml(status.detail)})</span>` : '';
          return `<div class="peer-row"><span>${escapeHtml(url)}${detail}</span>
          <span class="peer-status"><div class="dot" style="background:${status.color}"></div><span style="font-size:12px;color:${status.color}">${status.label}</span></span></div>`;
        }).join('')
      : '<div style="font-size:13px;color:var(--muted);padding:8px 0">No peers connected yet.</div>';
    document.getElementById('chain-stats').innerHTML = `
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px">
        <div><div style="color:var(--muted);font-size:12px;margin-bottom:4px">Chain length</div><div style="font-size:26px;font-weight:800">${escapeHtml(Number(stats.height) + 1)}</div></div>
        <div><div style="color:var(--muted);font-size:12px;margin-bottom:4px">Peers (connected)</div><div style="font-size:26px;font-weight:800">${escapeHtml(peers.filter(p => peerStatus(typeof p === 'string' ? { url: p } : (p || {})).label === 'connected').length)} / ${escapeHtml(peers.length)}</div></div>
        <div><div style="color:var(--muted);font-size:12px;margin-bottom:4px">Difficulty</div><div style="font-size:26px;font-weight:800">${escapeHtml(stats.difficulty)}</div></div>
      </div>`;
  } catch (_) {
    document.getElementById('chain-stats').textContent = 'Failed to load node info.';
  }
}

// ============================================================
// SECTION 13b — Mining pools directory
// ============================================================
async function loadPools() {
  const list = document.getElementById('pool-list');
  list.innerHTML = '<div class="empty">Loading&hellip;</div>';
  let pools = [];
  try {
    const result = await api('GET', '/pools');
    pools = result.pools || [];
  } catch (_) {
    list.innerHTML = '<div class="empty">Could not load the pool directory.</div>';
    return;
  }
  if (!pools.length) {
    list.innerHTML = '<div class="empty">No pools listed yet. Be the first — list your pool above.</div>';
    return;
  }
  list.innerHTML = pools.map(url => `<div class="peer-row" data-pool>
      <div style="min-width:0;flex:1">
        <div style="font-weight:600;overflow-wrap:anywhere">${escapeHtml(url)}</div>
        <div class="token-address" data-pool-detail>Checking&hellip;</div>
      </div>
      <span class="peer-status"><div class="dot" style="background:var(--muted)"></div><span style="font-size:12px;color:var(--muted)" data-pool-status>checking&hellip;</span></span>
    </div>`).join('');
  const rows = list.querySelectorAll('[data-pool]');
  pools.forEach((url, index) => enrichPool(rows[index], url));
}

// The pool servers allow cross-origin reads, so the browser fetches each pool's
// live info directly — that also doubles as the up/down check.
async function enrichPool(row, url) {
  if (!row) return;
  const statusEl = row.querySelector('[data-pool-status]');
  const dot = row.querySelector('.dot');
  const detailEl = row.querySelector('[data-pool-detail]');
  const base = url.replace(/\/$/, '');
  try {
    const [info, stats] = await Promise.all([
      fetch(base + '/pool/info', { signal: AbortSignal.timeout(6000) }).then(r => r.json()),
      fetch(base + '/pool/stats', { signal: AbortSignal.timeout(6000) }).then(r => r.json()).catch(() => ({})),
    ]);
    const fee = info.fee_percent != null ? `${info.fee_percent}% fee` : 'fee unknown';
    const miners = Array.isArray(stats.miners) ? stats.miners.length : 0;
    const blocks = stats.blocks_found != null ? stats.blocks_found : (info.blocks_found ?? '—');
    const netDiff = info.network_difficulty ?? '—';
    dot.style.background = 'var(--green)';
    statusEl.textContent = 'online';
    statusEl.style.color = 'var(--green)';
    const payoutNote = info.payouts_enabled === false ? ' &middot; <span style="color:var(--orange)">payouts off</span>' : '';
    detailEl.innerHTML = `${escapeHtml(fee)} &middot; ${escapeHtml(String(miners))} mining now &middot; ${escapeHtml(String(blocks))} blocks found &middot; net difficulty ${escapeHtml(String(netDiff))}${payoutNote}`;
  } catch (_) {
    dot.style.background = 'var(--red)';
    statusEl.textContent = 'offline';
    statusEl.style.color = 'var(--red)';
    detailEl.textContent = 'Not responding — the pool may be down or unreachable.';
  }
}

document.getElementById('btn-refresh-pools').addEventListener('click', loadPools);
document.getElementById('btn-add-pool').addEventListener('click', async () => {
  const input = document.getElementById('pool-url');
  const url = input.value.trim();
  setAlert('pools-alert', '');
  if (!/^https?:\/\//.test(url)) {
    setAlert('pools-alert', 'Enter the full pool URL, e.g. https://your-pool.trycloudflare.com');
    return;
  }
  try {
    const result = await api('POST', '/pools/register', { url });
    setAlert('pools-alert', result.message || 'Pool listed.', 'ok');
    input.value = '';
    loadPools();
  } catch (error) {
    setAlert('pools-alert', error.message || 'Could not list that pool.');
  }
});
document.getElementById('pool-url').addEventListener('keydown', event => {
  if (event.key === 'Enter') document.getElementById('btn-add-pool').click();
});

// ============================================================
// SECTION 14 — Startup
// ============================================================
(async () => {
  document.getElementById('node-banner').style.display = 'flex';
  prepareWalletNameInput();

  const restored = await restoreSession();
  if (!restored) {
    // Preserve the typed wallet name when upgrading from the old name-only session.
    const legacy = sessionStorage.getItem('hlx_session');
    if (legacy) {
      try {
        const { name } = JSON.parse(legacy);
        if (name && walletExists(name)) document.getElementById('login-name').value = name;
      } catch (_) {}
      sessionStorage.removeItem('hlx_session');
    }
  }

  await connectToNode();
})();

// Background audit poll
setInterval(async () => {
  if (!hasActiveSession()) return;
  try {
    const r = await api('GET', '/nodes/audit/cached');
    if (!r || r.message) return;
    const conflicts = (r.conflicts || []).length;
    if (!r.local_integrity?.ok || conflicts > 0)
      showSyncPill(`⚠ ${conflicts} conflict${conflicts !== 1 ? 's' : ''}`);
  } catch (_) {}
}, 35000);