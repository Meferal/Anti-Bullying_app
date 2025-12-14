from ..schemas import SurveyInput, RiskAnalysisResult, Frequency, YesNo
from ..models import AlertLevel

class HeuristicPredictor:
    """
    Motor de análisis basado en reglas (Adaptación TEBAE).
    Calcula el riesgo basándose en pesos predefinidos ante la falta de datos históricos.
    """
    
    # Pesos de configuración
    SCORE_MAP = {
        Frequency.NEVER: 0,
        Frequency.SOMETIMES: 1,
        Frequency.OFTEN: 2,
        Frequency.ALWAYS_CORRECTED: 3
    }

    # Umbrales
    THRESHOLD_CRITICAL = 12 # Puntuación muy alta
    THRESHOLD_HIGH = 8
    THRESHOLD_MEDIUM = 4

    def analyze(self, data: SurveyInput) -> RiskAnalysisResult:
        score = 0
        flags = []
        
        # --- Lógica Profesor (Si hay datos de profesor) ---
        if data.t_vic_insults is not None:
             # Scoring simple: Suma directa de valores 0-4
             # A. Victimización
             vic_score = sum([
                 data.t_vic_insults or 0, data.t_vic_exclusion or 0, 
                 data.t_vic_physical or 0, data.t_vic_theft or 0, 
                 data.t_vic_rumors or 0, data.t_vic_threats or 0
             ])
             
             # B. Agresión
             agg_score = sum([
                 data.t_agg_insults or 0, data.t_agg_exclusion or 0,
                 data.t_agg_physical or 0, data.t_agg_theft or 0,
                 data.t_agg_rumors or 0
             ])
             
             # C. Cyber
             cyber_score = sum([data.t_cyber_messages or 0, data.t_cyber_anxiety or 0])
             
             score = vic_score + agg_score + cyber_score
             
             if vic_score > 10: flags.append("Alta Victimización detectada")
             if agg_score > 10: flags.append("Comportamiento Agresor detectado")
             if cyber_score > 4: flags.append("Indicios de Ciberacoso")

             # Umbrales Profesor (Max 52)
             if score > 25: risk_level = AlertLevel.CRITICAL
             elif score > 15: risk_level = AlertLevel.HIGH
             elif score > 8: risk_level = AlertLevel.MEDIUM
             else: risk_level = AlertLevel.LOW
             
        # --- Lógica Padres (Default: Items p_item_1...13) ---
        else:
            # Block A: Directos y Materiales (Items 1-5)
            score_a = sum([
                data.p_item_1 or 0, data.p_item_2 or 0, data.p_item_3 or 0, 
                data.p_item_4 or 0, data.p_item_5 or 0
            ])
            
            # Block B: Psicosomáticos (Items 6-10)
            score_b = sum([
                data.p_item_6 or 0, data.p_item_7 or 0, data.p_item_8 or 0,
                data.p_item_9 or 0, data.p_item_10 or 0
            ])
            
            # Block C: Ciberacoso (Items 11-13)
            score_c = sum([
                data.p_item_11 or 0, data.p_item_12 or 0, data.p_item_13 or 0
            ])
            
            score = score_a + score_b + score_c
            
            # Flags específicos
            if score_a > 8: flags.append("Indicadores Directos/Físicos Altos")
            if score_b > 10: flags.append("Alto Malestar Psicosomático")
            if score_c > 5: flags.append("Indicios de Ciberacoso")
            
            # Alerta inmediata si items críticos tienen valor alto (ej: Heridas=4)
            if (data.p_item_2 or 0) >= 3 or (data.p_item_5 or 0) >= 3:
                flags.append("Marcador Crítico Detectado (Heridas/Coacción)")
                risk_level = AlertLevel.CRITICAL
            
            # Umbrales (Max 52)
            elif score > 25: risk_level = AlertLevel.CRITICAL
            elif score > 15: risk_level = AlertLevel.HIGH
            elif score > 8: risk_level = AlertLevel.MEDIUM
            else: risk_level = AlertLevel.LOW

        # Recomendación básica (será enriquecida luego por el RAG)
        recommendation = self._get_recommendation(risk_level)

        return RiskAnalysisResult(
            total_score=score,
            risk_level=risk_level.value,
            flags=flags,
            recommendation=recommendation
        )

    def _get_recommendation(self, level: AlertLevel) -> str:
        if level == AlertLevel.CRITICAL:
            return "ALERTA: Se detectan indicadores graves. Se requiere intervención inmediata del centro."
        elif level == AlertLevel.HIGH:
            return "Riesgo Alto: Se observan patrones preocupantes consistentes. Recomendamos solicitar tutoría."
        elif level == AlertLevel.MEDIUM:
            return "Precaución: Mantener observación. Hay indicadores de malestar."
        else:
            return "Sin riesgo apreciable actualmente. Continuar monitorización normal."

heuristic_engine = HeuristicPredictor()
