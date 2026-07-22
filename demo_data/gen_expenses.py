"""Generate a demo expense CSV with a few anomalies planted in it."""

import csv
import random
from datetime import date, timedelta

random.seed(42)

EMPLOYEES = [
    "Martin, Sophie",
    "Dubois, Julien",
    "Leroy, Camille",
    "Moreau, Thomas",
    "Petit, Anaïs",
    "Bernard, Marc",
    "Laurent, Claire",
    "Simon, Antoine",
]

COST_CENTERS = ["DAF", "Commercial", "RH", "IT", "Direction", "Marketing"]

SUPPLIERS = {
    "Fournitures bureau": [
        ("Bureau Vallée", 40, 350),
        ("Staples France", 60, 500),
        ("Amazon Business", 30, 800),
        ("Bruneau", 50, 400),
    ],
    "Restauration": [
        ("L'Ardoise - Paris 8", 25, 120),
        ("Brasserie du Marché", 30, 150),
        ("Sodexo Pass", 10, 80),
        ("Uber Eats Pro", 15, 90),
        ("Deliveroo Business", 15, 85),
        ("Noura - Neuilly", 40, 200),
    ],
    "Transport": [
        ("SNCF Voyages", 45, 380),
        ("Air France", 180, 950),
        ("Eurostar", 90, 320),
        ("Uber Business", 15, 80),
        ("Hertz France", 80, 450),
        ("Avis Location", 90, 500),
    ],
    "Hébergement": [
        ("Ibis Paris Opéra", 90, 180),
        ("Novotel Lyon Part-Dieu", 100, 210),
        ("Marriott Paris", 180, 380),
        ("B&B Hôtels", 60, 110),
    ],
    "Télécom": [
        ("Orange Pro", 30, 150),
        ("SFR Business", 30, 140),
        ("Bouygues Entreprises", 25, 130),
    ],
    "Logiciels & SaaS": [
        ("Microsoft 365", 120, 800),
        ("Salesforce", 200, 2500),
        ("Slack Technologies", 80, 600),
        ("Adobe Creative Cloud", 60, 400),
        ("Zoom Communications", 50, 300),
        ("GitHub Enterprise", 80, 500),
    ],
    "Carburant": [
        ("Total Energies", 60, 200),
        ("BP France", 55, 190),
        ("Esso Card", 50, 180),
    ],
    "Assurances": [
        ("AXA Entreprises", 300, 1200),
        ("Allianz Pro", 280, 1100),
        ("MMA Pro", 250, 900),
    ],
    "Formation": [
        ("OpenClassrooms Business", 500, 2000),
        ("Cegos Formation", 800, 3500),
        ("ORSYS", 700, 3000),
    ],
    "Fournitures IT": [
        ("Dell Technologies", 400, 2500),
        ("Apple Business", 800, 3500),
        ("Lenovo Pro", 500, 2000),
        ("Cdiscount Pro", 100, 1500),
    ],
}

DESCRIPTIONS = {
    "Fournitures bureau": [
        "Ramettes papier A4 - {n} boîtes",
        "Stylos et marqueurs équipe",
        "Cartouches imprimante HP LaserJet",
        "Fournitures bureau Q{q}",
        "Mobilier bureau - chaise ergonomique",
        "Post-it et classeurs",
    ],
    "Restauration": [
        "Déjeuner client {c}",
        "Repas équipe commerciale",
        "Dîner prospect - signature contrat",
        "Déjeuner de travail - {dept}",
        "Repas séminaire annuel",
        "Déjeuner formation interne",
    ],
    "Transport": [
        "Paris-Lyon A/R - réunion siège",
        "Paris-Bordeaux - visite client",
        "Paris-Bruxelles - conf. européenne",
        "Taxi aéroport CDG",
        "Location véhicule - déplacement client {c}",
        "Train Paris-Strasbourg - salon {n}",
    ],
    "Hébergement": [
        "Nuit hôtel - déplacement client {c}",
        "2 nuits - formation {dept}",
        "Hébergement séminaire {n} personnes",
        "Nuit Paris - réunion investisseurs",
    ],
    "Télécom": [
        "Abonnement mobile pro - {name}",
        "Forfait data international",
        "Ligne fixe bureaux Q{q}",
        "Extension réseau - site {n}",
    ],
    "Logiciels & SaaS": [
        "Licences annuelles - {n} postes",
        "Abonnement mensuel {dept}",
        "Renouvellement contrat enterprise",
        "Extension licences Q{q}",
    ],
    "Carburant": [
        "Carburant véhicule commercial {n}",
        "Plein véhicule - déplacement client",
        "Carburant flotte - {name}",
    ],
    "Assurances": [
        "Prime RC Professionnelle Q{q}",
        "Assurance flotte véhicules",
        "Multirisque locaux professionnels",
    ],
    "Formation": [
        "Formation management - {name}",
        "Certification {dept} - {n} personnes",
        "Cursus développement commercial",
        "Formation RGPD équipe {dept}",
    ],
    "Fournitures IT": [
        'MacBook Pro 14" - {name}',
        "PC portable Dell XPS - {name}",
        'Écran 27" + dock USB-C',
        "Serveur NAS - IT {n}",
        "Switch réseau 24 ports",
    ],
}


def pick_description(cat: str, **kwargs: object) -> str:
    templates = DESCRIPTIONS.get(cat, ["Achat {cat}"])
    tpl = random.choice(templates)
    return tpl.format(
        cat=cat.lower(),
        n=random.randint(2, 20),
        q=random.randint(1, 4),
        c=random.choice(
            ["Renault", "TotalEnergies", "Société Générale", "BNP Paribas", "Airbus"]
        ),
        dept=random.choice(["Commercial", "RH", "IT", "Direction", "Marketing"]),
        name=random.choice([e.split(",")[0] for e in EMPLOYEES]),
    )


rows = []
start = date(2025, 1, 1)

for _ in range(350):
    d = start + timedelta(days=random.randint(0, 364))
    while d.weekday() >= 5:
        d += timedelta(days=1)

    cat = random.choice(list(SUPPLIERS.keys()))
    supplier, low, high = random.choice(SUPPLIERS[cat])
    amount = round(random.uniform(low, high), 2)
    employee = random.choice(EMPLOYEES)
    cost_center = random.choice(COST_CENTERS)

    rows.append(
        {
            "date": d.isoformat(),
            "montant": amount,
            "fournisseur": supplier,
            "categorie": cat,
            "description": pick_description(cat),
            "employe": employee,
            "centre_cout": cost_center,
            "statut": random.choices(["validé", "en attente"], weights=[85, 15])[0],
        }
    )

# --- ANOMALIES RÉALISTES ---

# 1. Prestation conseil externe — montant anormalement élevé, fournisseur inconnu
rows.append(
    {
        "date": "2025-06-15",
        "montant": 48500.00,
        "fournisseur": "Delta Consult SARL",
        "categorie": "Logiciels & SaaS",
        "description": "Prestation conseil transformation digitale - phase 1",
        "employe": "Bernard, Marc",
        "centre_cout": "Direction",
        "statut": "validé",
    }
)

# 2. Doublon exact — même fournisseur, même montant, 3 jours d'écart
rows.append(
    {
        "date": "2025-03-10",
        "montant": 1247.80,
        "fournisseur": "Dell Technologies",
        "categorie": "Fournitures IT",
        "description": 'Écran 27" + dock USB-C',
        "employe": "Dubois, Julien",
        "centre_cout": "IT",
        "statut": "validé",
    }
)
rows.append(
    {
        "date": "2025-03-13",
        "montant": 1247.80,
        "fournisseur": "Dell Technologies",
        "categorie": "Fournitures IT",
        "description": 'Écran 27" + dock USB-C',
        "employe": "Dubois, Julien",
        "centre_cout": "IT",
        "statut": "validé",
    }
)

# 3. Transaction un dimanche — restaurant + montant élevé
rows.append(
    {
        "date": "2025-09-07",  # dimanche
        "montant": 4800.00,
        "fournisseur": "Noura - Neuilly",
        "categorie": "Restauration",
        "description": "Dîner de gala - direction et partenaires",
        "employe": "Martin, Sophie",
        "centre_cout": "Direction",
        "statut": "validé",
    }
)

# 4. Montant rond suspect — description vague
rows.append(
    {
        "date": "2025-11-03",
        "montant": 15000.00,
        "fournisseur": "Total Energies",
        "categorie": "Carburant",
        "description": "Divers carburant",
        "employe": "Simon, Antoine",
        "centre_cout": "Commercial",
        "statut": "validé",
    }
)

# 5. Pic transport Q4 — même employé, 6 billets avion en 3 semaines
for i, day in enumerate([3, 7, 10, 14, 17, 21]):
    rows.append(
        {
            "date": f"2025-10-{day:02d}",
            "montant": round(random.uniform(650, 920), 2),
            "fournisseur": "Air France",
            "categorie": "Transport",
            "description": f"Paris-{'New York' if i % 2 == 0 else 'Londres'} - déplacement commercial",
            "employe": "Moreau, Thomas",
            "centre_cout": "Commercial",
            "statut": "validé",
        }
    )

# 6. Abonnement SaaS dupliqué — deux outils identiques payés
rows.append(
    {
        "date": "2025-01-15",
        "montant": 1890.00,
        "fournisseur": "Zoom Communications",
        "categorie": "Logiciels & SaaS",
        "description": "Abonnement annuel Zoom - 50 licences",
        "employe": "Leroy, Camille",
        "centre_cout": "IT",
        "statut": "validé",
    }
)
rows.append(
    {
        "date": "2025-02-01",
        "montant": 2100.00,
        "fournisseur": "Microsoft 365",
        "categorie": "Logiciels & SaaS",
        "description": "Abonnement Teams + Visio - 50 licences",
        "employe": "Leroy, Camille",
        "centre_cout": "IT",
        "statut": "validé",
    }
)

random.shuffle(rows)

fieldnames = [
    "date",
    "montant",
    "fournisseur",
    "categorie",
    "description",
    "employe",
    "centre_cout",
    "statut",
]
with open("demo_data/expenses.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} rows with 7 injected anomalies -> demo_data/expenses.csv")
