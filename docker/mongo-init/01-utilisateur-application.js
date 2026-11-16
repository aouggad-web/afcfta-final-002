// Utilisateur de l'application (audit INFO-5) : lecture et écriture sur la
// seule base de l'application. Le compte root de MongoDB ne sert qu'à
// l'administration ; le backend ne le reçoit plus.
//
// L'image officielle exécute ce script une seule fois, à la création du
// volume. Sur un volume existant, créer l'utilisateur à la main avec la même
// commande (connecté en root avec mongosh).
const nomBase = process.env.MONGO_DB || "afcfta";

db.getSiblingDB(nomBase).createUser({
  user: process.env.MONGO_APP_USER,
  pwd: process.env.MONGO_APP_PASSWORD,
  roles: [{ role: "readWrite", db: nomBase }],
});
