from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

# --- ENUMS para las Respuestas ---
class Frequency(str, Enum):
    NEVER = "nunca"
    SOMETIMES = "a_veces"
    OFTEN = "a_menudo"
    ALWAYS = "sempre" # Typo intention check? No, standardizing to spanish: siempre
    ALWAYS_CORRECTED = "siempre"

class YesNo(str, Enum):
    YES = "si"
    NO = "no"

# --- Schema del Formulario (Input) ---
class SurveyInput(BaseModel):
    # A. Sintomatología Psicosomática (Padres)
    headache_stomach: Optional[Frequency] = Field(None, description="Dolores de cabeza o estómago antes de ir al colegio")
    
    # B. Cambios Conductuales / Emocionales (Padres)
    mood_changes: Optional[Frequency] = Field(None, description="Cambios bruscos de humor o irritabilidad")
    sleep_problems: Optional[Frequency] = Field(None, description="Dificultades para dormir o pesadillas")
    school_resistance: Optional[Frequency] = Field(None, description="Resistencia o ansiedad al ir al colegio")
    
    # C. Indicadores Directos (Padres)
    damaged_items: Optional[YesNo] = Field(None, description="Material roto o perdido")
    # --- PARENT SURVEY FIELDS (New Version) ---
    # Block A: Direct & Material (0-4)
    p_item_1: Optional[int] = None # Ropa rota / material
    p_item_2: Optional[int] = None # Heridas
    p_item_3: Optional[int] = None # Insultos
    p_item_4: Optional[int] = None # Exclusión
    p_item_5: Optional[int] = None # Coacción
    
    # Block B: Psychosomatic & Emotional (0-4)
    p_item_6: Optional[int] = None # Ansiedad mañana
    p_item_7: Optional[int] = None # Dolores físicos
    p_item_8: Optional[int] = None # Sueño/Alimentación
    p_item_9: Optional[int] = None # Humor
    p_item_10: Optional[int] = None # Evitación

    # Block C: Cyber (0-4)
    p_item_11: Optional[int] = None # Nerviosismo móvil
    p_item_12: Optional[int] = None # Ocultar pantalla
    p_item_13: Optional[int] = None # Ciberacoso

    p_observations: Optional[str] = None

    # --- TEACHER SURVEY FIELDS ---
    # Block A: Victimization (0-4)
    t_vic_insults: Optional[int] = None
    t_vic_exclusion: Optional[int] = None
    t_vic_physical: Optional[int] = None
    t_vic_theft: Optional[int] = None
    t_vic_rumors: Optional[int] = None
    t_vic_threats: Optional[int] = None
    
    # Block B: Aggression (0-4)
    t_agg_insults: Optional[int] = None
    t_agg_exclusion: Optional[int] = None
    t_agg_physical: Optional[int] = None
    t_agg_theft: Optional[int] = None
    t_agg_rumors: Optional[int] = None

    # Block C: Cyber
    t_cyber_messages: Optional[int] = None
    t_cyber_anxiety: Optional[int] = None

    t_observations: Optional[str] = None

# --- Schema del Resultado (Output del Agente) ---
class RiskAnalysisResult(BaseModel):
    total_score: int
    risk_level: str # Low, Medium, High, Critical
    flags: List[str] # Lista de alertas específicas (ej: "Daño material detectado")
    recommendation: str

# --- Schemas de Usuario ---
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: str

class StudentCreate(BaseModel):
    name: str # En modelo real es 'internal_code' pero usaremos esto como display
    age: int
    grade: str # Clase/Curso
    school_name: str # Nombre del colegio (lo buscaremos u crearemos)
