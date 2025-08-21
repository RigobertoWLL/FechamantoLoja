from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ResultadoFechamento:
    sucesso: bool
    mensagem: str
    detalhes: Optional[Dict[str, Any]] = None