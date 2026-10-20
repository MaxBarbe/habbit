from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path


DATABASE_PATH = (
    Path(__file__).resolve().parent
    / "wardrobe.db"
)


# ============================================================
# CONNEXION
# ============================================================

def _connect():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = (
        sqlite3.Row
    )

    return connection


# ============================================================
# INITIALISATION
# ============================================================

def init_database():

    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with _connect() as connection:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS clothes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                image_hash TEXT NOT NULL UNIQUE,

                original_path TEXT NOT NULL,
                cutout_path TEXT NOT NULL,

                type TEXT,
                categorie TEXT,
                confidence REAL,

                couleur TEXT,
                couleur_secondaire TEXT,
                multicolore INTEGER,

                matiere TEXT,
                matiere_detectee TEXT,
                matiere_confidence REAL,
                matiere_statut TEXT,

                saisons TEXT,

                style_principal TEXT,
                style_soiree REAL,
                style_sport REAL,
                style_elegant REAL,
                style_casual REAL,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ----------------------------------------------------
        # MIGRATION DES ANCIENNES BASES
        #
        # Ta base existe déjà avec 13 vêtements.
        # On ajoute donc les colonnes sans supprimer
        # les données existantes.
        # ----------------------------------------------------

        existing_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(clothes)"
            ).fetchall()
        }

        new_columns = {
            "style_principal":
                "TEXT",

            "style_soiree":
                "REAL",

            "style_sport":
                "REAL",

            "style_elegant":
                "REAL",

            "style_casual":
                "REAL",
        }

        for (
            column_name,
            column_type,
        ) in new_columns.items():

            if (
                column_name
                not in existing_columns
            ):

                connection.execute(
                    f"""
                    ALTER TABLE clothes
                    ADD COLUMN {column_name}
                    {column_type}
                    """
                )

        connection.commit()


# ============================================================
# HASH
# ============================================================

def calculate_file_hash(
    file_path: str | Path,
) -> str:

    file_path = Path(
        file_path
    )

    sha256 = hashlib.sha256()

    with open(
        file_path,
        "rb",
    ) as file:

        while True:

            chunk = file.read(
                1024 * 1024
            )

            if not chunk:
                break

            sha256.update(
                chunk
            )

    return sha256.hexdigest()


# ============================================================
# CONVERSION SQLITE -> DICT
# ============================================================

def _row_to_dict(
    row,
):

    if row is None:
        return None

    result = dict(
        row
    )

    if (
        result.get("saisons")
        is not None
    ):

        try:

            result["saisons"] = (
                json.loads(
                    result["saisons"]
                )
            )

        except Exception:

            result["saisons"] = []

    else:

        result["saisons"] = []

    result["multicolore"] = bool(
        result.get(
            "multicolore",
            0,
        )
    )

    return result


# ============================================================
# RECHERCHE PAR HASH
# ============================================================

def get_by_hash(
    image_hash: str,
):

    init_database()

    with _connect() as connection:

        row = connection.execute(
            """
            SELECT *
            FROM clothes
            WHERE image_hash = ?
            """,
            (
                image_hash,
            ),
        ).fetchone()

    return _row_to_dict(
        row
    )


# ============================================================
# RECHERCHE PAR FICHIER
# ============================================================

def get_by_file(
    file_path: str | Path,
):

    image_hash = (
        calculate_file_hash(
            file_path
        )
    )

    return get_by_hash(
        image_hash
    )


# ============================================================
# SAUVEGARDE VETEMENT
# ============================================================

def save_clothing(
    data: dict,
):

    init_database()

    saisons = data.get(
        "saisons",
        [],
    )

    if not isinstance(
        saisons,
        str,
    ):

        saisons = json.dumps(
            saisons,
            ensure_ascii=False,
        )

    with _connect() as connection:

        connection.execute(
            """
            INSERT INTO clothes (
                image_hash,
                original_path,
                cutout_path,

                type,
                categorie,
                confidence,

                couleur,
                couleur_secondaire,
                multicolore,

                matiere,
                matiere_detectee,
                matiere_confidence,
                matiere_statut,

                saisons,

                style_principal,
                style_soiree,
                style_sport,
                style_elegant,
                style_casual,
                created_at
            )
            VALUES (
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?,
                ?, ?, ?, ?, ?,
                CURRENT_TIMESTAMP
            )

            ON CONFLICT(image_hash)
            DO UPDATE SET

                original_path =
                    excluded.original_path,

                cutout_path =
                    excluded.cutout_path,

                type =
                    excluded.type,

                categorie =
                    excluded.categorie,

                confidence =
                    excluded.confidence,

                couleur =
                    excluded.couleur,

                couleur_secondaire =
                    excluded.couleur_secondaire,

                multicolore =
                    excluded.multicolore,

                matiere =
                    excluded.matiere,

                matiere_detectee =
                    excluded.matiere_detectee,

                matiere_confidence =
                    excluded.matiere_confidence,

                matiere_statut =
                    excluded.matiere_statut,

                saisons =
                    excluded.saisons,

                style_principal =
                    COALESCE(
                        excluded.style_principal,
                        clothes.style_principal
                    ),

                style_soiree =
                    COALESCE(
                        excluded.style_soiree,
                        clothes.style_soiree
                    ),

                style_sport =
                    COALESCE(
                        excluded.style_sport,
                        clothes.style_sport
                    ),

                style_elegant =
                    COALESCE(
                        excluded.style_elegant,
                        clothes.style_elegant
                    ),

                style_casual =
                    COALESCE(
                        excluded.style_casual,
                        clothes.style_casual
                    )
            """,
            (
                data.get(
                    "image_hash"
                ),

                data.get(
                    "original_path"
                ),

                data.get(
                    "cutout_path"
                ),

                data.get(
                    "type"
                ),

                data.get(
                    "categorie"
                ),

                data.get(
                    "confidence"
                ),

                data.get(
                    "couleur"
                ),

                data.get(
                    "couleur_secondaire"
                ),

                int(
                    bool(
                        data.get(
                            "multicolore",
                            False,
                        )
                    )
                ),

                data.get(
                    "matiere"
                ),

                data.get(
                    "matiere_detectee"
                ),

                data.get(
                    "matiere_confidence"
                ),

                data.get(
                    "matiere_statut"
                ),

                saisons,

                data.get(
                    "style_principal"
                ),

                data.get(
                    "style_soiree"
                ),

                data.get(
                    "style_sport"
                ),

                data.get(
                    "style_elegant"
                ),

                data.get(
                    "style_casual"
                ),
            ),
        )

        connection.commit()

    return get_by_hash(
        data["image_hash"]
    )


# ============================================================
# MISE A JOUR STYLE UNIQUEMENT
# ============================================================

def update_clothing_style(
    clothing_id: int,
    style: dict,
):

    init_database()

    with _connect() as connection:

        connection.execute(
            """
            UPDATE clothes

            SET
                style_principal = ?,
                style_soiree = ?,
                style_sport = ?,
                style_elegant = ?,
                style_casual = ?

            WHERE id = ?
            """,
            (
                style.get(
                    "style_principal"
                ),

                style.get(
                    "soiree"
                ),

                style.get(
                    "sport"
                ),

                style.get(
                    "elegant"
                ),

                style.get(
                    "casual"
                ),

                clothing_id,
            ),
        )

        connection.commit()

    return get_by_id(
        clothing_id
    )


# ============================================================
# RECHERCHE PAR ID
# ============================================================

def get_by_id(
    clothing_id: int,
):

    init_database()

    with _connect() as connection:

        row = connection.execute(
            """
            SELECT *
            FROM clothes
            WHERE id = ?
            """,
            (
                clothing_id,
            ),
        ).fetchone()

    return _row_to_dict(
        row
    )


# ============================================================
# TOUS LES VETEMENTS
# ============================================================

def get_all_clothes():

    init_database()

    with _connect() as connection:

        rows = connection.execute(
            """
            SELECT *
            FROM clothes
            ORDER BY id ASC
            """
        ).fetchall()

    return [
        _row_to_dict(row)
        for row in rows
    ]


# ============================================================
# NOMBRE
# ============================================================

def count_clothes():

    init_database()

    with _connect() as connection:

        result = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM clothes
            """
        ).fetchone()

    return int(
        result["total"]
    )