# Design — Attachement de fichier (bouton trombone)

Date : 2026-08-02
Projet : AXIOM v4.0 (`C:\Users\hp\Desktop\hakimagent`)
Statut : Approuvé par l'utilisateur

## Contexte

Le bouton trombone (📎 Paperclip) de la barre de saisie de la page d'accueil
(`frontend/app/page.tsx`) affiche actuellement un toast « Fonctionnalité de
fichier bientôt disponible ». L'objectif est de rendre ce bouton fonctionnel :
joindre un fichier texte/code au message envoyé à l'orchestrateur, afin que
l'agent sélectionné dispose du contenu du fichier comme contexte.

## Approche retenue

Lecture du fichier côté client (navigateur) + injection du contenu dans le
message envoyé à l'endpoint `/api/v1/chat` existant. **Aucun changement
backend** : `lib/api.ts`, `routes.py`, `schemas.py` restent intacts.

Le backend `/chat` reçoit un `ChatMessage { role, content }` ; la seule
modification est le contenu du `content`, qui préfixe la question avec le
contexte du fichier joint.

## Comportement UX

1. Clic sur le trombone → ouvre le sélecteur de fichier natif, filtré sur les
   extensions texte/code supportées.
2. Fichier sélectionné → affiché en « chip » au-dessus de la barre de saisie :
   icône 📎, nom du fichier, taille (Ko), bouton ✕ pour le retirer.
3. Un seul fichier joint à la fois : en joindre un nouveau remplace le
   précédent.
4. Au clic sur Envoyer :
   - Le contenu du fichier est lu en UTF-8 (`FileReader.readAsText`).
   - Le message envoyé à `/chat` est construit ainsi :

     ```
     Fichier joint "main.py" (2.1 Ko) :
     ```python
     <contenu du fichier>
     ```

     Question : <texte de l'utilisateur>
     ```

   - Le langage du bloc de code est déduit de l'extension via une map
     `extension → lang` (ex. `py`→python, `js`→javascript, `ts`→typescript,
     `json`→json, `md`→markdown, `html`→html, `css`→css, `sql`→sql,
     `yml`/`yaml`→yaml, `sh`→bash, `bat`/`ps1`→powershell, défaut : pas de
     langage).
5. Affichage dans le chat : le message utilisateur affiché est le texte seul,
   avec un badge discret `📎 main.py` sous le texte si un fichier était joint.
   Le contenu du fichier n'apparaît pas dans le fil pour ne pas l'encombrer.
6. Après envoi, la chip disparaît ; le trombone est désactivé pendant le
   `loading` (état déjà géré par `disabled={loading}` sur le bouton).

## Types de fichiers supportés

Extensions acceptées : `.txt`, `.md`, `.markdown`, `.py`, `.js`, `.mjs`,
`.ts`, `.tsx`, `.jsx`, `.json`, `.csv`, `.html`, `.css`, `.scss`, `.sql`,
`.yaml`, `.yml`, `.xml`, `.sh`, `.bat`, `.cmd`, `.ps1`, `.ini`, `.cfg`,
`.toml`, `.env`, `.log`.

## Limites et gestion d'erreurs

- Taille maximale : **100 Ko**. Au-delà → toast d'erreur « Fichier trop
  volumineux (max 100 Ko) », fichier refusé (chip non ajoutée).
- Fichier vide → toast « Fichier vide », refusé.
- Type non supporté (extension hors liste ou fichier binaire détecté à la
  lecture) → toast « Type de fichier non supporté », refusé.
- Échec de lecture (`FileReader.onerror`) → toast « Impossible de lire le
  fichier », refusé.
- Les toasts existants (système `pushToast` / `ToastStack` déjà en place dans
  `page.tsx`) sont réutilisés, aucune nouvelle infra UI.

## Fichiers modifiés

- `frontend/app/page.tsx` — seul fichier modifié :
  - État local `attachedFile: { name: string; size: number } | null` (le
    contenu n'est lu qu'au moment de l'envoi, via un `File` conservé en
    référence — pas de stockage du contenu en mémoire plus tôt que nécessaire).
  - `<input type="file" accept="...">` masqué (réf `fileInputRef`),
    déclenché par le clic sur le trombone.
  - Rendu de la chip au-dessus de la barre de saisie.
  - `handleSend` : construit le message avec contexte du fichier si présent.
  - Map `EXT_TO_LANG` et liste `ACCEPTED_EXTENSIONS` en constantes.
  - L'ancien handler `pushToast('info', 'Fonctionnalité de fichier bientôt
    disponible')` est remplacé par l'ouverture du sélecteur.

## Tests

1. `npx tsc --noEmit` — doit passer.
2. `npm run lint` — doit passer.
3. Test manuel navigateur (http://localhost:3000) :
   - Joindre un fichier `.py` → la chip apparaît avec nom/taille ; envoyer →
     badge `📎 fichier` sous le message utilisateur ; réponse de l'agent
     (nécessite le backend actif + clé OpenRouter).
   - Retirer la chip avec ✕ avant envoi → aucun fichier dans le message.
   - Joindre deux fichiers à la suite → le second remplace le premier.
   - Fichier > 100 Ko → toast d'erreur, pas de chip.
   - Fichier `.exe`/`.zip` → toast « Type de fichier non supporté ».
   - Trombone désactivé pendant `loading`.

## Hors périmètre (volontairement)

- PDF, images et autres fichiers binaires.
- Plusieurs fichiers joints simultanément.
- Upload/persistance du fichier côté serveur.
- Export de conversation (fonctionnalité distincte, non traitée ici).
