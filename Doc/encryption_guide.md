# Guide du chiffrement LocalNetMessage

Ce guide décrit le chiffrement léger côté navigateur utilisé dans LocalNetMessage, son fonctionnement et son usage.

## Principe
- Chiffrement symétrique **XOR + double Base64** réalisé dans `encryptions/encryption.js`.
- La clé est générée/gérée dans le navigateur et stockée en **localStorage**.
- Les messages chiffrés portent le préfixe `[ENCRYPTED]` et sont déchiffrés automatiquement si les deux pairs partagent la même clé.
- Le chiffrement est conçu pour un usage LAN.

## Génération et partage de clé
1. Ouvrir le panneau 🔒 dans l'UI.
2. Activer le toggle de chiffrement sur **les deux côtés**.
3. Côté émetteur : cliquer sur «🔄 Nouvelle Clé», puis «📋 Copier».
4. Côté destinataire : coller la clé dans «Importer une Clé», cliquer sur «📥 Importer».

Notes :
- La clé reste dans le localStorage du navigateur. Si vous videz le stockage ou changez de navigateur, réimportez la clé.
- Les fichiers ne sont pas chiffrés : seuls les messages texte passent par le XOR.

## Fonctionnement interne (résumé)
- `encrypt(message)` : encode UTF-8 → Base64, applique XOR avec la clé répétée, re-encode en Base64, préfixe `[ENCRYPTED]`.
- `decrypt(encryptedMessage)` : supprime le préfixe, Base64 decode, XOR inverse avec la clé, Base64 decode pour retrouver le texte.
- La clé est une chaîne hexadécimale de 32+ caractères (16+ octets) générée par `crypto.getRandomValues`.

## Dépannage
- Message illisible : vérifier que la clé est identique des deux côtés et que le toggle est activé.
- Pas de préfixe `[ENCRYPTED]` : le chiffrement n’était pas activé au moment de l’envoi.
- Après nettoyage du navigateur : réimporter la clé copiée auparavant ou régénérer et repartager.
