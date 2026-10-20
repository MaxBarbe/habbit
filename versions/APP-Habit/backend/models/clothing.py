from dataclasses import dataclass, field

@dataclass
class ClothingItem:
    id: str
    image_path: str
    type: str
    categorie: str
    couleur: str | None = None
    matiere: str | None = None
    saisons: list[str] = field(default_factory=list)
    analysed: bool = True
