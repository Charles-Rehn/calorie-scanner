# Calorie Scanner

A free calorie tracker that installs on iPhone and iPad from a website, with no App Store and no Apple developer account.

- Scan barcodes with the live camera, or search foods (common foods built in, plus the Open Food Facts database of packaged products)
- Log by weight in grams or by servings
- Daily calorie limit, with a red warning when you go over and a 7-day strip showing which days were over
- Dishes: add every ingredient of something you cooked (say a spaghetti bolognese) once, then log your portion by grams or portions
- Accounts: sign in with email and password and your diary is on every phone and iPad you use; you stay signed in until you sign out
- Family: share dishes and foods, so everyone logs their own portion of the same meal and sees how much is left in the pot

## 1. Put it online (free, GitHub Pages)

The camera only works on a secure (https) website, so the app needs proper hosting. GitHub Pages is free.

1. Make a free account at github.com.
2. Create a new **public** repository, for example `calorie-scanner`.
3. Upload every file in this folder (`index.html`, `config.js`, `sw.js`, `manifest.webmanifest`, the three `icon-*.png` files). Easiest from a computer: on the repository page, choose **Add file › Upload files** and drag them in.
4. In the repository, open **Settings › Pages**. Under *Build and deployment*, set Source to **Deploy from a branch**, branch **main**, folder **/ (root)**, and save.
5. After a minute your app is live at `https://YOUR-USERNAME.github.io/calorie-scanner/`.

Netlify and Cloudflare Pages also host it for free if you prefer them.

## 2. Install it on iPhone and iPad

1. Open the link in **Safari**.
2. Tap the **Share** button, then **Add to Home Screen**.
3. Open it from the Home Screen. It runs full-screen like a normal app, works offline, and asks for camera access the first time you scan.

Everyone in the family does this on their own device.

## 3. Turn on accounts and family sharing (free Firebase, about 10 minutes)

Without this step the app still works, but each device keeps its own diary, foods and dishes, with no accounts. Accounts and family sharing need a small free database. Firebase's free plan is far more than a family needs.

1. Go to console.firebase.google.com, sign in with a Google account and **Create a project** (Google Analytics can be turned off).
2. **Firestore database:** in the left menu, open **Build › Firestore Database › Create database**. Pick a location near you (for Spain, `eur3` or `europe-southwest1`) and start in **production mode**.
3. **Rules:** in Firestore, open the **Rules** tab, replace everything with the contents of `firestore.rules` from this folder, and **Publish**.
4. **Accounts:** open **Build › Authentication › Get started**, choose **Email/Password**, switch the first toggle on and save. While you're there, open **Settings › Authorized domains** and add `YOUR-USERNAME.github.io`, so sign-in works from your website.
5. **Web app settings:** open **Project settings** (the gear icon) › **Your apps** › the **</>** (Web) button. Give it any name and register it. Firebase shows a `firebaseConfig = { ... }` block.
6. In your GitHub repository, edit `config.js`. Replace `window.FIREBASE_CONFIG = null;` with
   `window.FIREBASE_CONFIG = { ...the values Firebase showed you... };` and commit.

The values in that block are safe to publish; they identify the project but don't grant access by themselves.

Then, in the app:

- Everyone creates an account the first time they open the app (name, email, password). After that it stays signed in. Signing in on another phone or iPad brings the same diary.
- One person taps **Family** and creates the family.
- In the Family screen, **Copy invite link** and send it to everyone else. They open it, add it to the Home Screen, create their account and tap **Join**. Anyone who installed the app first can join by typing the family code instead.
- Forgot a password? Tap **Forgot your password?** on the sign-in screen and Firebase emails a reset link.

## How dishes work

1. Tap **Create a dish**, name it, and add each ingredient with its raw weight (500 g beef mince, 500 g dry spaghetti, a 400 g can of tomatoes, and so on).
2. Enter how many portions it makes. For logging by grams, also weigh the finished food: weigh the pot full, subtract the empty pot's weight, and enter the difference as **Cooked weight**.
3. Each person opens the dish and logs what they ate, for example 450 g or 1.5 portions. The dish shows who has had some and roughly how much is left.

## Good to know

- Everything is stored in your own Firebase project, not on anyone else's server. Each person's diary and limit are private to their account. Family foods, dishes and who-ate-how-much are visible to anyone signed in with the family code, so only share it with family.
- Anything logged on a device before signing in moves into the account the first time someone signs in on it.
- Open Food Facts is a free community database. Most supermarket products are there, but some values can be missing or wrong. Unknown barcodes can be typed in once from the pack, and are then saved for the whole family.
- Open Food Facts allows about 10 searches a minute, so the app searches it when you tap the search button instead of while you type.
- The built-in common foods use typical values per 100 g. Edit them to match your pack when you have it.
