"""
Project Aegis-Voice: Comprehensive Adversarial Benchmark & Stress Validation Test Suite (R2)
Validates all 5 core edge-case scenarios required by R2 and Section 3 of the Sovereign PSAP specification:

1. Stoic Victim / Shock Paralysis:
   Flat pitch variance (sigma_F0 < 8Hz) + low arousal (A < 0.35) + high-value cybercrime intent
   -> Priority-1 promotion (U >= 0.85, badge PRIORITY-1 [SHOCK / DISSOCIATION TRIAGE], State S4).

2. Performative Screaming / Yelling:
   High loudness (>80dB, A > 0.75) + normal jitter (<2.2%) + zero fraud intent
   -> Strictly capped at Routine (U <= 0.45, badge AGITATED - NON-CRITICAL (ROUTINE)).

3. Synthetic Deepfake Spoof:
   AASIST-L phase entropy anomaly (P_spoof > 0.70)
   -> Immediately suppressed to U = 0.15, badge SYNTHETIC SPOOF - BLOCKED, queue escalation blocked.

4. Frontier 1 Scammer-in-the-Background Coercion:
   Secondary laptop transducer roll-off (<280Hz) + bimodal coaching turn-taking micro-pauses (1.1s - 2.4s)
   -> Coercion detected flag active, transducer ratio > 10.0.

5. Silent Shadow Mode Statistical Gates:
   Multi-call cohort evaluation verifying:
   - Golden-Hour fraud recall >= 94.0%
   - False Positive Rate <= 8.5%
   - Mean Early Lead-Time Advantage >= 110s
   -> Production readiness status GRADUATION_APPROVED_READY_FOR_INDICATIVE_UI.

Also verifies the CLI runner functions and benchmark_results.json artifact integrity.
"""

import os
import sys
import json
import pytest
import numpy as np

# Ensure all microservice directories are discoverable
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.abspath(os.path.join(TEST_DIR, ".."))
SCRIPTS_DIR = os.path.join(CORE_DIR, "scripts")
FUSION_DIR = os.path.join(CORE_DIR, "neuro-symbolic-triage")
ACOUSTIC_DIR = os.path.join(CORE_DIR, "acoustic-ser-worker")
SEMANTIC_DIR = os.path.join(CORE_DIR, "semantic-asr-worker")
INGEST_DIR = os.path.join(CORE_DIR, "ingestion-gateway")

for d in [CORE_DIR, SCRIPTS_DIR, FUSION_DIR, ACOUSTIC_DIR, SEMANTIC_DIR, INGEST_DIR]:
    if d not in sys.path:
        sys.path.insert(0, d)

from late_fusion_engine import compute_multimodal_triage, RAIL_DECAY_CONSTANTS
from cfcfrms_jsonld_builder import build_cfcfrms_jsonld
from pii_redaction_fst import extract_semantic_threat_score, scrub_pii_in_memory
from aasist_spoof_guard import AASISTSpoofGuard
from frontier_coercion_calibration import detect_secondary_transducer_coercion
from shadow_evaluator import SilentShadowEvaluator, ShadowCallRecord
from run_adversarial_benchmark import (
    evaluate_stoic_shock_victim,
    evaluate_performative_screaming,
    evaluate_synthetic_deepfake_spoof,
    evaluate_frontier1_coercion,
    evaluate_silent_shadow_mode_statistical_gates,
    run_all_benchmarks
)


# ==============================================================================
# SCENARIO 1: Stoic Victim / Shock Paralysis
# ==============================================================================

def test_scenario_1_stoic_victim_shock_paralysis_baseline():
    """Verify that flat pitch variance (<8Hz) and low arousal (<0.35) under cybercrime intent escalates to Priority-1."""
    res = evaluate_stoic_shock_victim(verbose=False)

    assert res["passed"] is True
    assert res["status"] == "PASSED"
    assert res["measured_urgency"] >= 0.85
    assert res["shock_paralysis_flag"] is True
    assert "SHOCK / DISSOCIATION" in res["badge"]
    assert res["state"] == "S4_LIEN_PAYLOAD_STAGED"
    assert res["cfcfrms_lien_staged"] is True
    assert res["execution_time_ms"] < 25.0  # Fast execution


@pytest.mark.parametrize("sigma_f0,arousal", [
    (3.2, 0.15),
    (4.2, 0.19),
    (5.5, 0.25),
    (7.4, 0.32),
])
def test_scenario_1_stoic_victim_parameter_sweep(sigma_f0, arousal):
    """Verify shock paralysis triggers across parametric variations within dissociative shock region."""
    triage = compute_multimodal_triage(
        valence=0.20,
        arousal=arousal,
        dominance=0.18,
        jitter_pct=1.4,
        sigma_f0_hz=sigma_f0,
        spoof_prob=0.04,
        epistemic_uncertainty=0.08,
        s_semantic=0.95,
        override_active=True,
        matched_keywords=["DIGITAL ARREST", "RTGS"],
        elapsed_txn_minutes=8.0,
        detected_rail="RTGS",
        call_uuid=f"sweep-stoic-{sigma_f0}-{arousal}"
    )

    assert triage["shock_paralysis_flag"] is True
    assert triage["urgency_score"] >= 0.85
    assert "SHOCK / DISSOCIATION" in triage["badge"]
    assert triage["state"] == "S4_LIEN_PAYLOAD_STAGED"
    assert triage["cfcfrms_lien_draft"] is not None
    assert triage["cfcfrms_lien_draft"]["victim_psychological_state"] == "SHOCK_PARALYSIS"


def test_scenario_1_stoic_victim_negative_controls():
    """Verify that if pitch variance or arousal is not depressed, or override is false, shock flag does not trigger."""
    # 1. Normal pitch variance (25Hz) with cybercrime
    normal_pitch = compute_multimodal_triage(
        valence=0.20, arousal=0.20, dominance=0.20, jitter_pct=1.4,
        sigma_f0_hz=25.0,  # >= 8Hz
        spoof_prob=0.04, epistemic_uncertainty=0.08,
        s_semantic=0.95, override_active=True, matched_keywords=["DIGITAL ARREST"]
    )
    assert normal_pitch["shock_paralysis_flag"] is False

    # 2. Elevated arousal (0.50) with flat pitch
    high_arousal = compute_multimodal_triage(
        valence=0.20, arousal=0.50, dominance=0.20, jitter_pct=1.4,
        sigma_f0_hz=4.0,  # < 8Hz, but arousal >= 0.35
        spoof_prob=0.04, epistemic_uncertainty=0.08,
        s_semantic=0.95, override_active=True, matched_keywords=["DIGITAL ARREST"]
    )
    assert high_arousal["shock_paralysis_flag"] is False

    # 3. Flat pitch and low arousal without cybercrime override
    no_override = compute_multimodal_triage(
        valence=0.20, arousal=0.20, dominance=0.20, jitter_pct=1.4,
        sigma_f0_hz=4.0, spoof_prob=0.04, epistemic_uncertainty=0.08,
        s_semantic=0.0, override_active=False, matched_keywords=[]
    )
    assert no_override["shock_paralysis_flag"] is False


# ==============================================================================
# SCENARIO 2: Performative Screaming / Yelling
# ==============================================================================

def test_scenario_2_performative_screaming_routine_capping():
    """Verify that performative yelling with normal jitter and zero fraud intent is capped at Routine (<=0.45)."""
    res = evaluate_performative_screaming(verbose=False)

    assert res["passed"] is True
    assert res["status"] == "PASSED"
    assert res["measured_urgency"] <= 0.45
    assert res["measured_urgency"] == 0.41
    assert res["performative_flag"] is True
    assert "ROUTINE" in res["badge"] or "AGITATED" in res["badge"]
    assert res["state"] == "S2_ACOUSTIC_LEXICAL_SURVEILLANCE"
    assert res["cfcfrms_lien_blocked"] is True
    assert res["p_freeze"] == 0.0


@pytest.mark.parametrize("arousal,jitter", [
    (0.76, 0.8),
    (0.82, 1.1),
    (0.88, 1.4),
    (0.95, 2.0),
])
def test_scenario_2_performative_screaming_parameter_sweep(arousal, jitter):
    """Verify capping holds across screaming volume variations as long as jitter < 2.2% and s_sem == 0."""
    triage = compute_multimodal_triage(
        valence=0.35,
        arousal=arousal,
        dominance=0.80,
        jitter_pct=jitter,
        sigma_f0_hz=26.0,
        spoof_prob=0.04,
        epistemic_uncertainty=0.05,
        s_semantic=0.0,
        override_active=False,
        matched_keywords=[],
        call_uuid=f"sweep-yell-{arousal}-{jitter}"
    )

    assert triage["performative_flag"] is True
    assert triage["urgency_score"] <= 0.45
    assert triage["urgency_score"] == 0.41
    assert "AGITATED" in triage["badge"] or "ROUTINE" in triage["badge"]
    assert triage["p_freeze"] == 0.0
    assert triage["cfcfrms_lien_draft"] is None


def test_scenario_2_performative_negative_controls():
    """Verify that performative cap is bypassed when true autonomic trauma tremor (jitter >= 2.2%) or cybercrime is present."""
    # 1. Genuine autonomic trauma tremor: high arousal (0.85) AND pathologically high jitter (3.1% >= 2.2%)
    trauma_panic = compute_multimodal_triage(
        valence=0.20,
        arousal=0.85,
        dominance=0.30,
        jitter_pct=3.1,  # Tremor indicates genuine shock / physiological distress
        sigma_f0_hz=32.0,
        spoof_prob=0.04,
        epistemic_uncertainty=0.05,
        s_semantic=0.0,
        override_active=False,
        matched_keywords=[]
    )
    assert trauma_panic["performative_flag"] is False
    assert "AGITATED - NON-CRITICAL" not in trauma_panic["badge"]

    # 2. Screaming with cybercrime keywords: high arousal (0.85) AND cybercrime intent
    screaming_fraud = compute_multimodal_triage(
        valence=0.20,
        arousal=0.85,
        dominance=0.70,
        jitter_pct=1.2,
        sigma_f0_hz=25.0,
        spoof_prob=0.04,
        epistemic_uncertainty=0.05,
        s_semantic=0.95,  # Fraud detected
        override_active=True,
        matched_keywords=["ACCOUNT EMPTIED", "UPI"]
    )
    assert screaming_fraud["performative_flag"] is False
    assert screaming_fraud["urgency_score"] >= 0.72  # Escalates to Golden-Hour Critical


# ==============================================================================
# SCENARIO 3: Synthetic Deepfake Spoof
# ==============================================================================

def test_scenario_3_synthetic_deepfake_acoustic_discrimination():
    """Verify AASIST-L acoustic detector discriminates synthetic neural vocoder from natural voice."""
    guard = AASISTSpoofGuard(threshold=0.70)

    # 1. High-confidence synthetic impulse train (phase entropy < 1.1, high-freq energy < 0.001)
    synth_audio = np.zeros(8000, dtype=np.float32)
    synth_audio[::80] = 0.001
    prob_synth, is_spoof = guard.detect_synthetic_voice(synth_audio)
    assert prob_synth == 0.94
    assert is_spoof is True

    # 2. Natural voice: chaotic phase entropy and breathy high harmonics
    t = np.linspace(0, 0.5, 8000, endpoint=False)
    natural_voice = (
        0.3 * np.sin(2 * np.pi * 180 * t)
        + 0.15 * np.sin(2 * np.pi * 360 * t)
        + 0.08 * np.sin(2 * np.pi * 4200 * t)
        + 0.04 * np.random.randn(8000)
    ).astype(np.float32)
    prob_nat, is_spoof_nat = guard.detect_synthetic_voice(natural_voice)
    assert prob_nat <= 0.70
    assert is_spoof_nat is False


def test_scenario_3_synthetic_deepfake_suppression_late_fusion():
    """Verify deepfake probability >0.70 suppresses urgency to U=0.15 and blocks queue escalation even under max threat claims."""
    res = evaluate_synthetic_deepfake_spoof(verbose=False)

    assert res["passed"] is True
    assert res["status"] == "PASSED"
    assert res["measured_urgency"] == 0.15
    assert res["badge"] == "SYNTHETIC SPOOF - BLOCKED"
    assert res["state"] == "S2_ACOUSTIC_LEXICAL_SURVEILLANCE"
    assert res["spoof_flag"] is True
    assert res["queue_escalation_blocked"] is True


@pytest.mark.parametrize("spoof_prob", [0.71, 0.76, 0.94, 0.99])
def test_scenario_3_synthetic_deepfake_varying_spoof_probs(spoof_prob):
    """Verify suppression holds for all spoof probabilities above 0.70 threshold."""
    triage = compute_multimodal_triage(
        valence=0.10,
        arousal=0.95,
        dominance=0.90,
        jitter_pct=0.2,
        sigma_f0_hz=1.0,
        spoof_prob=spoof_prob,
        epistemic_uncertainty=0.04,
        s_semantic=1.00,  # "SUICIDE" / "CBI"
        override_active=True,
        matched_keywords=["SUICIDE", "DIGITAL ARREST"],
        call_uuid=f"sweep-spoof-{spoof_prob}"
    )

    assert triage["spoof_flag"] is True
    assert triage["urgency_score"] == 0.15
    assert triage["badge"] == "SYNTHETIC SPOOF - BLOCKED"
    assert triage["cfcfrms_lien_draft"] is None
    assert triage["p_freeze"] == 0.0


# ==============================================================================
# SCENARIO 4: Frontier 1 Scammer-in-the-Background Coercion
# ==============================================================================

def test_scenario_4_frontier1_scammer_background_coercion():
    """Verify detection of background coaching via secondary laptop speakerphone roll-off and bimodal pauses."""
    res = evaluate_frontier1_coercion(verbose=False)

    assert res["passed"] is True
    assert res["status"] == "PASSED"
    assert res["coercion_detected"] is True
    assert res["is_coached_pause"] is True
    assert res["is_tinny_secondary_source"] is True
    assert res["transducer_ratio"] > 10.0  # Observed 14.1
    assert res["negative_control_passed"] is True


@pytest.mark.parametrize("pause_ms,expected_coached", [
    (1100.0, True),   # Lower boundary
    (1350.0, True),
    (1650.0, True),   # Midpoint
    (2100.0, True),
    (2400.0, True),   # Upper boundary
    (350.0, False),   # Normal human turn-taking
    (800.0, False),   # Short pause
    (2700.0, False),  # Long hesitation
])
def test_scenario_4_coaching_pause_window(pause_ms, expected_coached):
    """Verify coaching turn-taking pause window [1,100ms - 2,400ms] boundary behavior."""
    t = np.linspace(0, 1.5, 24000)
    audio_coerced = (0.01 * np.sin(2 * np.pi * 150 * t) + 0.35 * np.sin(2 * np.pi * 2400 * t)).astype(np.float32)

    flag, meta = detect_secondary_transducer_coercion(
        raw_audio_16k=audio_coerced,
        pre_utterance_pause_ms=pause_ms,
        primary_hnr_db=11.0
    )

    assert meta["is_coached_pause"] is expected_coached
    if expected_coached:
        assert flag is True
    else:
        assert flag is False


def test_scenario_4_transducer_acoustic_controls():
    """Verify negative controls: natural audio without roll-off or clean carrier HNR do not trigger coercion."""
    # 1. Natural audio with balanced low and mid harmonics
    t = np.linspace(0, 1.5, 24000)
    audio_natural = (0.30 * np.sin(2 * np.pi * 150 * t) + 0.30 * np.sin(2 * np.pi * 2400 * t)).astype(np.float32)

    flag_nat, meta_nat = detect_secondary_transducer_coercion(
        raw_audio_16k=audio_natural,
        pre_utterance_pause_ms=1650.0,
        primary_hnr_db=11.0
    )
    assert meta_nat["is_tinny_secondary_source"] is False
    assert flag_nat is False

    # 2. Clean carrier HNR >= 14dB (close-talking handset mic)
    audio_coerced = (0.01 * np.sin(2 * np.pi * 150 * t) + 0.35 * np.sin(2 * np.pi * 2400 * t)).astype(np.float32)
    flag_clean_hnr, _ = detect_secondary_transducer_coercion(
        raw_audio_16k=audio_coerced,
        pre_utterance_pause_ms=1650.0,
        primary_hnr_db=18.0  # Clean HNR >= 14.0dB
    )
    assert flag_clean_hnr is False


# ==============================================================================
# SCENARIO 5: Silent Shadow Mode Statistical Gates
# ==============================================================================

def test_scenario_5_silent_shadow_mode_statistical_gates():
    """Verify that multi-call cohort satisfies Recall >= 94%, FPR <= 8.5%, Lead-Time >= 110s and earns graduation."""
    res = evaluate_silent_shadow_mode_statistical_gates(cohort_size=200, seed=42, verbose=False)

    assert res["passed"] is True
    assert res["status"] == "PASSED"
    metrics = res["metrics"]
    assert metrics["golden_hour_fraud_recall_pct"] >= 94.0
    assert metrics["golden_hour_gate_passed"] is True
    assert metrics["false_positive_rate_pct"] <= 8.5
    assert metrics["fpr_gate_passed"] is True
    assert metrics["mean_lead_time_advantage_sec"] >= 110.0
    assert metrics["lead_time_gate_passed"] is True
    assert metrics["production_readiness_status"] == "GRADUATION_APPROVED_READY_FOR_INDICATIVE_UI"
    assert res["baseline_reference_passed"] is True


def test_scenario_5_shadow_evaluator_baseline_reference():
    """Verify default SilentShadowEvaluator calculation over statutory 14,200-call baseline reference."""
    evaluator = SilentShadowEvaluator()
    gates = evaluator.calculate_statistical_gates()

    assert gates["total_calls_evaluated"] == 14200
    assert gates["golden_hour_fraud_recall_pct"] == 95.8
    assert gates["golden_hour_gate_passed"] is True
    assert gates["false_positive_rate_pct"] == 6.9
    assert gates["fpr_gate_passed"] is True
    assert gates["mean_lead_time_advantage_sec"] == 124.6
    assert gates["lead_time_gate_passed"] is True
    assert gates["production_readiness_status"] == "GRADUATION_APPROVED_READY_FOR_INDICATIVE_UI"


def test_scenario_5_shadow_evaluator_gate_failure_reversion():
    """Verify that if recall drops below 94.0% or FPR exceeds 8.5%, status reverts to SHADOW_VALIDATION_IN_PROGRESS."""
    evaluator = SilentShadowEvaluator(urgency_threshold=0.72)

    # Log 85 True Positives and 15 False Negatives (Recall = 85.0% < 94.0%)
    now = 50000.0
    for i in range(85):
        evaluator.log_call_evaluation(ShadowCallRecord(
            call_uuid=f"tp-{i}", start_timestamp=now, ai_alert_timestamp=now + 10.0,
            ai_max_urgency=0.85, human_ticket_timestamp=now + 130.0,
            human_lien_executed=True, verified_loss_inr=100000.0,
            officer_escalation_tag=True, primary_threat_category="FRAUD"
        ))
    for i in range(15):
        evaluator.log_call_evaluation(ShadowCallRecord(
            call_uuid=f"fn-{i}", start_timestamp=now, ai_alert_timestamp=None,
            ai_max_urgency=0.40, human_ticket_timestamp=now + 160.0,
            human_lien_executed=True, verified_loss_inr=80000.0,
            officer_escalation_tag=True, primary_threat_category="FRAUD"
        ))

    gates = evaluator.calculate_statistical_gates()
    assert gates["golden_hour_fraud_recall_pct"] == 85.0
    assert gates["golden_hour_gate_passed"] is False
    assert gates["production_readiness_status"] == "SHADOW_VALIDATION_IN_PROGRESS"


# ==============================================================================
# BENCHMARK RUNNER & RESULTS ARTIFACT VERIFICATION
# ==============================================================================

def test_run_adversarial_benchmark_programmatic_execution():
    """Verify programmatic execution of run_all_benchmarks produces complete valid schema."""
    data = run_all_benchmarks(cohort_size=100, seed=123, verbose=False)

    meta = data["benchmark_metadata"]
    assert meta["overall_status"] == "ALL_GATES_PASSED"
    assert meta["production_graduation_status"] == "GRADUATION_APPROVED_READY_FOR_INDICATIVE_UI"
    assert meta["total_scenarios"] == 5
    assert meta["scenarios_passed"] == 5
    assert meta["scenarios_failed"] == 0

    scenarios = data["scenarios"]
    assert len(scenarios) == 5
    for key, sc in scenarios.items():
        assert sc["status"] == "PASSED"
        assert sc["passed"] is True


def test_benchmark_results_json_disk_artifact_compliance():
    """Verify that aegis-voice-core/benchmark_results.json exists, is valid JSON, and certifies all 5 gates."""
    artifact_path = os.path.join(CORE_DIR, "benchmark_results.json")
    assert os.path.exists(artifact_path), f"Missing artifact at {artifact_path}"

    with open(artifact_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "benchmark_metadata" in data
    assert "scenarios" in data

    meta = data["benchmark_metadata"]
    assert meta["overall_status"] == "ALL_GATES_PASSED"
    assert meta["production_graduation_status"] == "GRADUATION_APPROVED_READY_FOR_INDICATIVE_UI"
    assert meta["scenarios_passed"] == 5
    assert meta["scenarios_failed"] == 0

    scenarios = data["scenarios"]
    expected_scenarios = [
        "scenario_1_stoic_victim_shock_paralysis",
        "scenario_2_performative_screaming_yelling",
        "scenario_3_synthetic_deepfake_spoof",
        "scenario_4_frontier1_scammer_coercion",
        "scenario_5_silent_shadow_mode_statistical_gates"
    ]

    for esc in expected_scenarios:
        assert esc in scenarios, f"Missing scenario {esc} in JSON artifact"
        assert scenarios[esc]["status"] == "PASSED"
        assert scenarios[esc]["passed"] is True
