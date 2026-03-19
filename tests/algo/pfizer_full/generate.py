"""Generate all CSV data and per-column SQL files for pfizer_full test case."""
import csv, os, textwrap

BASE = os.path.dirname(os.path.abspath(__file__))

# ── Study data (3 rows) ──────────────────────────────────────────────
# Values that are the SAME between dsopi(in0) and srt(in1) for COALESCE columns
STUDIES = [
    {"id": "STD001", "adj": "Y", "dmc": "Y", "eu": "Y", "ib": "2023-06-01 00:00:00",
     "paper": "N", "patdb": "Rave", "subj_type": "Patient", "target_comp": 200,
     "dsopi_planned": 240, "srt_planned": 250,
     "bsc": "Y", "contact": "Pfizer", "cpoc": 85.5, "iqmp": "Y", "global": "Global",
     "pmv_max": 30, "pims": "Y", "rap": "N", "rcpms": "Y", "country": "US",
     "design_type": "Adaptive", "design_ver": "V2", "method": "Direct",
     "recruit_date": "2023-01-15", "rfssmi": "N", "tmf": "Y", "del_dsopi": "N", "del_srt": "N",
     "primary_dc": "Electronic", "secondary_dc": "Paper", "data_return": "Y",
     "withheld": "N", "eligible": "Y",
     "rationale": "Regulatory", "med_resp": "Oncology", "plan_type": "Full",
     "sap_end": "2024-12-31 00:00:00", "sap_pct": 75, "sap_start": "2023-01-01 00:00:00",
     "cpm": "John Smith", "exec_state": "Active", "site": "New York",
     "plan_name": "PAXLOVID-P3", "template": "Phase3Template", "status_plan": "On Track",
     "biz_group": "Pfizer Innovative Health", "ccs": "Internal",
     "eu_bool": "true", "paper_bool": "false"},
    {"id": "STD002", "adj": "N", "dmc": "Y", "eu": "N", "ib": "2023-09-15 00:00:00",
     "paper": "N", "patdb": "Medidata", "subj_type": "Healthy", "target_comp": 150,
     "dsopi_planned": 180, "srt_planned": 175,
     "bsc": "N", "contact": "CRO-Alpha", "cpoc": 42.0, "iqmp": "N", "global": "Regional",
     "pmv_max": 45, "pims": "N", "rap": "Y", "rcpms": "N", "country": "DE",
     "design_type": "Fixed", "design_ver": "V1", "method": "Referral",
     "recruit_date": "2023-04-01", "rfssmi": "N", "tmf": "Y", "del_dsopi": "N", "del_srt": "N",
     "primary_dc": "Electronic", "secondary_dc": "None", "data_return": "N",
     "withheld": "Y", "eligible": "Y",
     "rationale": "Commercial", "med_resp": "Cardiology", "plan_type": "Partial",
     "sap_end": "2025-06-30 00:00:00", "sap_pct": 30, "sap_start": "2023-06-01 00:00:00",
     "cpm": "Jane Doe", "exec_state": "Recruiting", "site": "Berlin",
     "plan_name": "ELREXFIO-P2", "template": "Phase2Template", "status_plan": "Behind",
     "biz_group": "Pfizer Biopharma", "ccs": "External",
     "eu_bool": "false", "paper_bool": "false"},
    {"id": "STD003", "adj": "Y", "dmc": "N", "eu": "Y", "ib": "2022-12-01 00:00:00",
     "paper": "Y", "patdb": "Rave", "subj_type": "Patient", "target_comp": 280,
     "dsopi_planned": 320, "srt_planned": 310,
     "bsc": "Y", "contact": "Pfizer", "cpoc": 100.0, "iqmp": "Y", "global": "Global",
     "pmv_max": 30, "pims": "Y", "rap": "N", "rcpms": "Y", "country": "JP",
     "design_type": "Adaptive", "design_ver": "V3", "method": "Direct",
     "recruit_date": "2022-06-01", "rfssmi": "Y", "tmf": "Y", "del_dsopi": "N", "del_srt": "N",
     "primary_dc": "Paper", "secondary_dc": "Electronic", "data_return": "Y",
     "withheld": "N", "eligible": "Y",
     "rationale": "Regulatory", "med_resp": "Neurology", "plan_type": "Full",
     "sap_end": "2024-03-31 00:00:00", "sap_pct": 100, "sap_start": "2022-01-01 00:00:00",
     "cpm": "Yuki Tanaka", "exec_state": "Completed", "site": "Tokyo",
     "plan_name": "ABRYSVO-P3", "template": "Phase3Template", "status_plan": "Complete",
     "biz_group": "Pfizer Innovative Health", "ccs": "Internal",
     "eu_bool": "true", "paper_bool": "true"},
]


def write_csv(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


# ── Column definitions ───────────────────────────────────────────────
# Each column: name, past expression (in study_portfolio_overview), expected expression
# MUST be defined before memory.yaml generation which references COLUMNS

COLUMNS = [
    {"name": "STUDY_ID",
     "past_expr": "COALESCE(in0.STUDY_ID, in1.STUDY_ID, in2.STUDY_ID, in3.STUDY_ID)",
     "expected_expr": "TRIM(om.STUDY_NUMBER)",
     "past_sources": "[dsopi_st_cln_study_operational.STUDY_ID, srt_study.STUDY_ID, cv_study_data.STUDY_ID, dsopi_st_cln_study_portfolio.STUDY_ID]"},
    {"name": "BSC_CRITICALPATH_STUDY",
     "past_expr": "in0.BSC_CRITICALPATH_STUDY",
     "expected_expr": "TRIM(CRITICAL_PATH_IND)",
     "past_sources": "[dsopi_st_cln_study_operational.BSC_CRITICAL_PATH_STUDY_FLG]"},
    {"name": "CONTACT_CARD_PROVIDER",
     "past_expr": "in0.CONTACT_CARD_PROVIDER",
     "expected_expr": "TRIM(CONTACT_PROVIDER)",
     "past_sources": "[dsopi_st_cln_study_operational.CONTACT_CARD_PROVIDER]"},
    {"name": "CPOC_COMPLETION_PERCENTAGE",
     "past_expr": "in0.CPOC_COMPLETION_PERCENTAGE",
     "expected_expr": "CAST(CPOC_PERCENT_COMPLETE AS DOUBLE)",
     "past_sources": "[dsopi_st_cln_study_operational.CPOC_COMPLETION_PERCNTG]"},
    {"name": "FULL_IQMP_REQUIRED",
     "past_expr": "in0.FULL_IQMP_REQUIRED",
     "expected_expr": "TRIM(IQMP_FULL_FLAG)",
     "past_sources": "[dsopi_st_cln_study_operational.IQMP_REQUIREMENT_FLAG]"},
    {"name": "GLOBAL_TRIAL_PLACEMENT",
     "past_expr": "in0.GLOBAL_TRIAL_PLACEMENT",
     "expected_expr": "TRIM(GLOBAL_PLACEMENT)",
     "past_sources": "[dsopi_st_cln_study_operational.GLOBAL_TRIAL_PLACEMENT]"},
    {"name": "MONITOR_VISIT_PLAN_INTERVAL_MAX",
     "past_expr": "in0.MONITOR_VISIT_PLAN_INTERVAL_MAX",
     "expected_expr": "CAST(MONITOR_INTERVAL_MAX AS BIGINT)",
     "past_sources": "[dsopi_st_cln_study_operational.PMV_MAX_INTERVAL]"},
    {"name": "PIMS_FLG",
     "past_expr": "in0.PIMS_FLG",
     "expected_expr": "TRIM(PIMS_INDICATOR)",
     "past_sources": "[dsopi_st_cln_study_operational.PIMS_FLG]"},
    {"name": "RAP_RCPMS_FLAG",
     "past_expr": "in0.RAP_RCPMS_FLAG",
     "expected_expr": "TRIM(RAP_RCPMS_IND)",
     "past_sources": "[dsopi_st_cln_study_operational.RAP_RCPMS_FLG]"},
    {"name": "RCPMS_FLAG",
     "past_expr": "in0.RCPMS_FLAG",
     "expected_expr": "TRIM(RCPMS_INDICATOR)",
     "past_sources": "[dsopi_st_cln_study_operational.RCPMS_FLAG]"},
    {"name": "RECRUITMENT_COUNTRY",
     "past_expr": "in0.RECRUITMENT_COUNTRY",
     "expected_expr": "TRIM(RECRUITMENT_COUNTRY_LIST)",
     "past_sources": "[dsopi_st_cln_study_operational.RECRUITMENT_COUNTRY]"},
    {"name": "RECRUITMENT_DESIGN_TYPE",
     "past_expr": "in0.RECRUITMENT_DESIGN_TYPE",
     "expected_expr": "TRIM(RECRUITMENT_DESIGN)",
     "past_sources": "[dsopi_st_cln_study_operational.RECRUITMENT_DESIGN_TYPE]"},
    {"name": "RECRUITMENT_DESIGN_VERSION",
     "past_expr": "in0.RECRUITMENT_DESIGN_VERSION",
     "expected_expr": "TRIM(RECRUITMENT_VERSION)",
     "past_sources": "[dsopi_st_cln_study_operational.RECRUITMENT_DESIGN_VERSION]"},
    {"name": "RECRUITMENT_METHOD",
     "past_expr": "in0.RECRUITMENT_METHOD",
     "expected_expr": "TRIM(RECRUITMENT_APPROACH)",
     "past_sources": "[dsopi_st_cln_study_operational.RECRUITMENT_METHOD]"},
    {"name": "RECRUITMENT_START_DATE",
     "past_expr": "in0.RECRUITMENT_START_DATE",
     "expected_expr": "CAST(RECRUITMENT_BEGIN_DATE AS DATE)",
     "past_sources": "[dsopi_st_cln_study_operational.RECRUITMENT_START_DATE]"},
    {"name": "RFSSMI_FLAG",
     "past_expr": "in0.RFSSMI_FLAG",
     "expected_expr": "TRIM(RFSSMI_INDICATOR)",
     "past_sources": "[dsopi_st_cln_study_operational.RFSSMI_FLAG]"},
    {"name": "TMF_REQUIREMENT_FLAG",
     "past_expr": "in0.TMF_REQUIREMENT_FLAG",
     "expected_expr": "TRIM(TMF_REQUIRED)",
     "past_sources": "[dsopi_st_cln_study_operational.TMF_REQUIREMENT_FLG]"},
    {"name": "COMMITTEE_ADJUDICATION_USED",
     "past_expr": "COALESCE(in1.COMMITTEE_ADJUDICATION_USED, in0.COMMITTEE_ADJUDICATION_USED)",
     "expected_expr": "TRIM(ADJUDICATION_COMMITTEE)",
     "past_sources": "[srt_study.COMMITTEE_ADJUDICATION_USED, dsopi_st_cln_study_operational.COMMI_ADJUDICATION_USED]"},
    {"name": "COMMITTEE_DMC_USED",
     "past_expr": "COALESCE(in1.COMMITTEE_DMC_USED, in0.COMMITTEE_DMC_USED)",
     "expected_expr": "TRIM(DMC_FLAG)",
     "past_sources": "[srt_study.COMMITTEE_DMC_USED, dsopi_st_cln_study_operational.COMMI_DMC_USED]"},
    {"name": "COMMITTEE_NONE_USED",
     "past_expr": "COALESCE(in1.COMMITTEE_NONE_USED, in0.COMMITTEE_NONE_USED)",
     "expected_expr": "CAST(NULL AS VARCHAR)",
     "past_sources": "[srt_study.COMMITTEE_NONE_USED, dsopi_st_cln_study_operational.COMMI_NONE_USED]"},
    {"name": "EU_APPROVED_PRODUCT",
     "past_expr": "COALESCE(in1.EU_APPROVED_PRODUCT, in0.EU_APPROVED_PRODUCT)",
     "expected_expr": "CASE\\n      WHEN APPROVED_PRODUCT_EU = TRUE THEN 'Y'\\n      WHEN APPROVED_PRODUCT_EU = FALSE THEN 'N'\\n      ELSE NULL\\n    END",
     "past_sources": "[srt_study.EU_APPROVED_PRODUCT, dsopi_st_cln_study_operational.EU_APPROVED_PRODUCT]"},
    {"name": "IB_VERSION_DT",
     "past_expr": "COALESCE(in1.IB_VERSION_DT, in0.IB_VERSION_DT)",
     "expected_expr": "CAST(IB_REVISION_DATE AS TIMESTAMP)",
     "past_sources": "[srt_study.IB_VERSION_DT, dsopi_st_cln_study_operational.IB_VERSION_DATE]"},
    {"name": "PAPER_STUDY",
     "past_expr": "COALESCE(in1.PAPER_STUDY, in0.PAPER_STUDY)",
     "expected_expr": "CASE\\n      WHEN PAPER_CRF_USED = TRUE THEN 'Y'\\n      WHEN PAPER_CRF_USED = FALSE THEN 'N'\\n      ELSE NULL\\n    END",
     "past_sources": "[srt_study.PAPER_STUDY, dsopi_st_cln_study_operational.PAPER_STUDY_FLG]"},
    {"name": "PATIENT_DATABASE",
     "past_expr": "COALESCE(in1.PATIENT_DATABASE, in0.PATIENT_DATABASE)",
     "expected_expr": "TRIM(EDC_SYSTEM)",
     "past_sources": "[srt_study.PATIENT_DATABASE, dsopi_st_cln_study_operational.PATIENT_DATABASE]"},
    {"name": "SUBJECTS_RECRUITED_TYPE",
     "past_expr": "COALESCE(in1.SUBJECTS_RECRUITED_TYPE, in0.SUBJECTS_RECRUITED_TYPE)",
     "expected_expr": "TRIM(SUBJECT_TYPE)",
     "past_sources": "[srt_study.SUBJECTS_RECRUITED_TYPE, dsopi_st_cln_study_operational.SUBJECTS_RECRUITED_TYPE]"},
    {"name": "TARGET_COMPLETE_NUMBER",
     "past_expr": "COALESCE(in1.TARGET_COMPLETE_NUMBER, in0.TARGET_COMPLETE_NUMBER)",
     "expected_expr": "CAST(COMPLETION_TARGET AS BIGINT)",
     "past_sources": "[srt_study.SUBJ_TARGET_COMPLETERS_NUM, dsopi_st_cln_study_operational.SUBJ_TARGET_COMPLETERS_NUM]"},
    {"name": "PLANNED_PATIENTS",
     "past_expr": "CASE\\n      WHEN in1.PLANNED_PATIENTS_SRT IS NOT NULL THEN in1.PLANNED_PATIENTS_SRT\\n      WHEN in0.PLANNED_PATIENTS_DSOPI IS NOT NULL THEN in0.PLANNED_PATIENTS_DSOPI\\n      ELSE NULL\\n    END",
     "expected_expr": "CAST(ENROLLMENT_TARGET AS BIGINT)",
     "past_sources": "[srt_study.TOT_SUBJ_PLANNED_STUDY, dsopi_st_cln_study_operational.TOT_SUBJ_PLANNED_STUDY]"},
    {"name": "PLANNED_PATIENTS_SOURCE",
     "past_expr": "CASE\\n      WHEN in1.PLANNED_PATIENTS_SRT IS NOT NULL THEN 'SRT'\\n      WHEN in0.PLANNED_PATIENTS_DSOPI IS NOT NULL THEN 'DSOPI'\\n      ELSE NULL\\n    END",
     "expected_expr": "CAST(NULL AS VARCHAR)",
     "past_sources": "[srt_study.TOT_SUBJ_PLANNED_STUDY, dsopi_st_cln_study_operational.TOT_SUBJ_PLANNED_STUDY]"},
    {"name": "PRIMARY_DATA_COLLECTION",
     "past_expr": "in1.PRIMARY_DATA_COLLECTION",
     "expected_expr": "TRIM(DATA_COLLECTION_PRIMARY)",
     "past_sources": "[srt_study.PRIMARY_DATA_COLLECTION]"},
    {"name": "SECONDARY_DATA_COLLECTION",
     "past_expr": "in1.SECONDARY_DATA_COLLECTION",
     "expected_expr": "TRIM(DATA_COLLECTION_SECONDARY)",
     "past_sources": "[srt_study.SECONDARY_DATA_COLLECTION]"},
    {"name": "DATA_RETURN_PLAN_COMPLETE_FLAG",
     "past_expr": "in1.DATA_RETURN_PLAN_COMPLETE_FLAG",
     "expected_expr": "TRIM(DATA_RETURN_COMPLETE)",
     "past_sources": "[srt_study.DATA_RETURN_PLAN_COMPLETE_FLAG]"},
    {"name": "PARTICIPANT_DATA_WITHHELD_UNTIL_LSLV_FLAG",
     "past_expr": "in1.PARTICIPANT_DATA_WITHHELD_UNTIL_LSLV_FLAG",
     "expected_expr": "TRIM(DATA_WITHHELD_FLAG)",
     "past_sources": "[srt_study.PARTICIPANT_DATA_WITHHELD_UNTIL_LSLV_FLAG]"},
    {"name": "PARTICIPANT_ELIGIBLE_TO_RETURN_FLAG",
     "past_expr": "in1.PARTICIPANT_ELIGIBLE_TO_RETURN_FLAG",
     "expected_expr": "TRIM(PARTICIPANT_RETURN_ELIGIBLE)",
     "past_sources": "[srt_study.PARTICIPANT_ELIGIBLE_TO_RETURN_FLAG]"},
    {"name": "BUSINESS_RATIONALE",
     "past_expr": "in2.BUSINESS_RATIONALE",
     "expected_expr": "TRIM(STUDY_RATIONALE)",
     "past_sources": "[cv_study_data.STUDY_BUSINESS_RATIONALE_CATEGORY]"},
    {"name": "MEDICAL_RESPONSIBILITY",
     "past_expr": "in2.MEDICAL_RESPONSIBILITY",
     "expected_expr": "TRIM(MEDICAL_OWNER)",
     "past_sources": "[cv_study_data.STUDY_MED_RESPONSIBILTY]"},
    {"name": "PROJECT_PLAN_TYPE",
     "past_expr": "in2.PROJECT_PLAN_TYPE",
     "expected_expr": "TRIM(PROJECT_TYPE)",
     "past_sources": "[cv_study_data.STUDY_PROJECT_PLAN_FINANCE_TYP]"},
    {"name": "SAP_FINISH_DATE",
     "past_expr": "in2.SAP_FINISH_DATE",
     "expected_expr": "CAST(SAP_END AS TIMESTAMP)",
     "past_sources": "[cv_study_data.STUDY_SAP_FINISH_DATE]"},
    {"name": "SAP_PCT_COMPLETED",
     "past_expr": "TRY_CAST(in2.SAP_PCT_COMPLETED AS BIGINT)",
     "expected_expr": "CAST(SAP_COMPLETION_PCT AS BIGINT)",
     "past_sources": "[cv_study_data.STUDY_PCNT_COMP_SAP]"},
    {"name": "SAP_START_DATE",
     "past_expr": "in2.SAP_START_DATE",
     "expected_expr": "CAST(SAP_START AS TIMESTAMP)",
     "past_sources": "[cv_study_data.STUDY_SAP_START_DATE]"},
    {"name": "STUDY_CPM",
     "past_expr": "in2.STUDY_CPM",
     "expected_expr": "TRIM(CLINICAL_PM)",
     "past_sources": "[cv_study_data.STUDY_CPM]"},
    {"name": "STUDY_EXECUTION_STATE",
     "past_expr": "in2.STUDY_EXECUTION_STATE",
     "expected_expr": "TRIM(EXECUTION_STATUS)",
     "past_sources": "[cv_study_data.STUDY_EXECUTION_STATE]"},
    {"name": "STUDY_PERFORMING_SITE",
     "past_expr": "in2.STUDY_PERFORMING_SITE",
     "expected_expr": "TRIM(PERFORMING_SITE)",
     "past_sources": "[cv_study_data.STUDY_PERFORMING_SITE]"},
    {"name": "STUDY_PROJECT_PLAN_NAME",
     "past_expr": "in2.STUDY_PROJECT_PLAN_NAME",
     "expected_expr": "TRIM(PROJECT_NAME)",
     "past_sources": "[cv_study_data.STUDY_PROJECT_PLAN_NAME]"},
    {"name": "STUDY_PROJECT_PLAN_TEMPLATE_NAME",
     "past_expr": "in2.STUDY_PROJECT_PLAN_TEMPLATE_NAME",
     "expected_expr": "TRIM(PROJECT_TEMPLATE)",
     "past_sources": "[cv_study_data.STUDY_PROJECT_PLAN_TEMPLATE_NAME]"},
    {"name": "STUDY_STATUS_PLAN",
     "past_expr": "in2.STUDY_STATUS_PLAN",
     "expected_expr": "TRIM(PLAN_STATUS)",
     "past_sources": "[cv_study_data.STUDY_STATUS_PLAN]"},
    {"name": "BUSINESS_GROUP",
     "past_expr": "in3.BUSINESS_GROUP",
     "expected_expr": "TRIM(PORTFOLIO_GROUP)",
     "past_sources": "[dsopi_st_cln_study_portfolio.BUSINESS_GROUP]"},
    {"name": "CCS_CLINICAL_PLACEMENT",
     "past_expr": "in3.CCS_CLINICAL_PLACEMENT",
     "expected_expr": "TRIM(CLINICAL_PLACEMENT)",
     "past_sources": "[dsopi_st_cln_study_portfolio.CCS_CLINICAL_PLACEMENT]"},
    {"name": "DELETE_FLAG",
     "past_expr": "COALESCE(in1.DELETE_FLAG_SRT, in0.DELETE_FLAG_DSOPI, 'N')",
     "expected_expr": "CAST('N' AS VARCHAR)",
     "past_sources": "[srt_study.DELETE_FLAG, dsopi_st_cln_study_operational.DELETE_FLAG]"},
    {"name": "START_DT",
     "past_expr": "TIMESTAMP '2024-06-15 10:00:00'",
     "expected_expr": "CAST(CREATE_TIMESTAMP AS TIMESTAMP)",
     "past_sources": "[]"},
    {"name": "END_DT",
     "past_expr": "TIMESTAMP '2024-06-15 10:00:00'",
     "expected_expr": "CAST(UPDATE_TIMESTAMP AS TIMESTAMP)",
     "past_sources": "[]"},
    {"name": "LOAD_DATE",
     "past_expr": "TIMESTAMP '2024-06-15 10:00:00'",
     "expected_expr": "CAST(LAST_MODIFIED AS TIMESTAMP)",
     "past_sources": "[]"},
]


# ── Past source CSVs ─────────────────────────────────────────────────

# dsopi_st_cln_study_operational
write_csv(
    os.path.join(BASE, "memory/star_schema_pipeline/pastdata/dsopi_st_cln_study_operational.csv"),
    ["STUDY_ID","BSC_CRITICAL_PATH_STUDY_FLG","COMMI_ADJUDICATION_USED","COMMI_DMC_USED",
     "COMMI_NONE_USED","CONTACT_CARD_PROVIDER","CPOC_COMPLETION_PERCNTG","EU_APPROVED_PRODUCT",
     "IQMP_REQUIREMENT_FLAG","GLOBAL_TRIAL_PLACEMENT","IB_VERSION_DATE","PMV_MAX_INTERVAL",
     "PAPER_STUDY_FLG","PATIENT_DATABASE","PIMS_FLG","TOT_SUBJ_PLANNED_STUDY",
     "RAP_RCPMS_FLG","RCPMS_FLAG","RECRUITMENT_COUNTRY","RECRUITMENT_DESIGN_TYPE",
     "RECRUITMENT_DESIGN_VERSION","RECRUITMENT_METHOD","RECRUITMENT_START_DATE",
     "RFSSMI_FLAG","SUBJECTS_RECRUITED_TYPE","SUBJ_TARGET_COMPLETERS_NUM",
     "TMF_REQUIREMENT_FLG","DELETE_FLAG"],
    [[s["id"], s["bsc"], s["adj"], s["dmc"], "", s["contact"], s["cpoc"],
      s["eu"], s["iqmp"], s["global"], s["ib"], s["pmv_max"], s["paper"],
      s["patdb"], s["pims"], s["dsopi_planned"], s["rap"], s["rcpms"],
      s["country"], s["design_type"], s["design_ver"], s["method"],
      s["recruit_date"], s["rfssmi"], s["subj_type"], s["target_comp"],
      s["tmf"], s["del_dsopi"]] for s in STUDIES]
)

# srt_study
write_csv(
    os.path.join(BASE, "memory/star_schema_pipeline/pastdata/srt_study.csv"),
    ["STUDY_ID","COMMITTEE_ADJUDICATION_USED","COMMITTEE_DMC_USED","COMMITTEE_NONE_USED",
     "EU_APPROVED_PRODUCT","IB_VERSION_DT","PAPER_STUDY","PATIENT_DATABASE",
     "TOT_SUBJ_PLANNED_STUDY","PRIMARY_DATA_COLLECTION","SECONDARY_DATA_COLLECTION",
     "SUBJECTS_RECRUITED_TYPE","SUBJ_TARGET_COMPLETERS_NUM",
     "DATA_RETURN_PLAN_COMPLETE_FLAG","PARTICIPANT_DATA_WITHHELD_UNTIL_LSLV_FLAG",
     "PARTICIPANT_ELIGIBLE_TO_RETURN_FLAG","DELETE_FLAG"],
    [[s["id"], s["adj"], s["dmc"], "", s["eu"], s["ib"], s["paper"],
      s["patdb"], s["srt_planned"], s["primary_dc"], s["secondary_dc"],
      s["subj_type"], s["target_comp"], s["data_return"], s["withheld"],
      s["eligible"], s["del_srt"]] for s in STUDIES]
)

# cv_study_data
write_csv(
    os.path.join(BASE, "memory/star_schema_pipeline/pastdata/cv_study_data.csv"),
    ["STUDY_ID","STUDY_BUSINESS_RATIONALE_CATEGORY","STUDY_MED_RESPONSIBILTY",
     "STUDY_PROJECT_PLAN_FINANCE_TYP","STUDY_SAP_FINISH_DATE","STUDY_PCNT_COMP_SAP",
     "STUDY_SAP_START_DATE","STUDY_CPM","STUDY_EXECUTION_STATE","STUDY_PERFORMING_SITE",
     "STUDY_PROJECT_PLAN_NAME","STUDY_PROJECT_PLAN_TEMPLATE_NAME","STUDY_STATUS_PLAN"],
    [[s["id"], s["rationale"], s["med_resp"], s["plan_type"], s["sap_end"],
      s["sap_pct"], s["sap_start"], s["cpm"], s["exec_state"], s["site"],
      s["plan_name"], s["template"], s["status_plan"]] for s in STUDIES]
)

# dsopi_st_cln_study_portfolio
write_csv(
    os.path.join(BASE, "memory/star_schema_pipeline/pastdata/dsopi_st_cln_study_portfolio.csv"),
    ["STUDY_ID","BUSINESS_GROUP","CCS_CLINICAL_PLACEMENT"],
    [[s["id"], s["biz_group"], s["ccs"]] for s in STUDIES]
)


# ── Current source CSVs ──────────────────────────────────────────────
os.makedirs(os.path.join(BASE, "sourcedata"), exist_ok=True)

# operational_metrics
write_csv(
    os.path.join(BASE, "sourcedata/operational_metrics.csv"),
    ["STUDY_NUMBER","CRITICAL_PATH_IND","CONTACT_PROVIDER","CPOC_PERCENT_COMPLETE",
     "IQMP_FULL_FLAG","GLOBAL_PLACEMENT","MONITOR_INTERVAL_MAX","PIMS_INDICATOR",
     "RAP_RCPMS_IND","RCPMS_INDICATOR","RECRUITMENT_COUNTRY_LIST","RECRUITMENT_DESIGN",
     "RECRUITMENT_VERSION","RECRUITMENT_APPROACH","RECRUITMENT_BEGIN_DATE","RFSSMI_INDICATOR",
     "TMF_REQUIRED","ADJUDICATION_COMMITTEE","DMC_FLAG","APPROVED_PRODUCT_EU",
     "IB_REVISION_DATE","PAPER_CRF_USED","EDC_SYSTEM","SUBJECT_TYPE","COMPLETION_TARGET",
     "ENROLLMENT_TARGET","DATA_COLLECTION_PRIMARY","DATA_COLLECTION_SECONDARY",
     "DATA_RETURN_COMPLETE","DATA_WITHHELD_FLAG","PARTICIPANT_RETURN_ELIGIBLE",
     "STUDY_RATIONALE","MEDICAL_OWNER","PROJECT_TYPE","SAP_END","SAP_COMPLETION_PCT",
     "SAP_START","CLINICAL_PM","EXECUTION_STATUS","PERFORMING_SITE","PROJECT_NAME",
     "PROJECT_TEMPLATE","PLAN_STATUS","PORTFOLIO_GROUP","CLINICAL_PLACEMENT",
     "CREATE_TIMESTAMP","UPDATE_TIMESTAMP","LAST_MODIFIED"],
    [[s["id"], s["bsc"], s["contact"], s["cpoc"], s["iqmp"], s["global"],
      s["pmv_max"], s["pims"], s["rap"], s["rcpms"], s["country"],
      s["design_type"], s["design_ver"], s["method"], s["recruit_date"],
      s["rfssmi"], s["tmf"], s["adj"], s["dmc"], s["eu_bool"], s["ib"],
      s["paper_bool"], s["patdb"], s["subj_type"], s["target_comp"],
      s["srt_planned"],  # ENROLLMENT_TARGET = SRT planned (pre-merged)
      s["primary_dc"], s["secondary_dc"], s["data_return"], s["withheld"],
      s["eligible"], s["rationale"], s["med_resp"], s["plan_type"],
      s["sap_end"], s["sap_pct"], s["sap_start"], s["cpm"], s["exec_state"],
      s["site"], s["plan_name"], s["template"], s["status_plan"],
      s["biz_group"], s["ccs"],
      "2024-06-15 10:00:00", "2024-06-15 10:00:00", "2024-06-15 10:00:00"]
     for s in STUDIES]
)

# trial_master
write_csv(
    os.path.join(BASE, "sourcedata/trial_master.csv"),
    ["TRIAL_NUMBER","TRIAL_TITLE","SPONSOR"],
    [[s["id"], f"Study {s['id']} Title", "Pfizer"] for s in STUDIES]
)


# ── memory.yaml ──────────────────────────────────────────────────────

os.makedirs(os.path.join(BASE, "memory/star_schema_pipeline"), exist_ok=True)
with open(os.path.join(BASE, "memory/star_schema_pipeline/memory.yaml"), "w") as f:
    f.write(textwrap.dedent("""\
    description: >
      Star schema with 4 source tables joined on STUDY_ID. dsopi and srt tables
      provide overlapping operational columns merged via COALESCE (srt priority).
      cv_study_data provides project plan metrics. Portfolio provides business group.
      Four CTEs transform each source, then a final CTE INNER JOINs all four.

    sources:
      - name: dsopi_st_cln_study_operational
        schema:
          - { name: STUDY_ID, type: VARCHAR }
          - { name: BSC_CRITICAL_PATH_STUDY_FLG, type: VARCHAR }
          - { name: COMMI_ADJUDICATION_USED, type: VARCHAR }
          - { name: COMMI_DMC_USED, type: VARCHAR }
          - { name: COMMI_NONE_USED, type: VARCHAR }
          - { name: CONTACT_CARD_PROVIDER, type: VARCHAR }
          - { name: CPOC_COMPLETION_PERCNTG, type: DOUBLE }
          - { name: EU_APPROVED_PRODUCT, type: VARCHAR }
          - { name: IQMP_REQUIREMENT_FLAG, type: VARCHAR }
          - { name: GLOBAL_TRIAL_PLACEMENT, type: VARCHAR }
          - { name: IB_VERSION_DATE, type: TIMESTAMP }
          - { name: PMV_MAX_INTERVAL, type: BIGINT }
          - { name: PAPER_STUDY_FLG, type: VARCHAR }
          - { name: PATIENT_DATABASE, type: VARCHAR }
          - { name: PIMS_FLG, type: VARCHAR }
          - { name: TOT_SUBJ_PLANNED_STUDY, type: BIGINT }
          - { name: RAP_RCPMS_FLG, type: VARCHAR }
          - { name: RCPMS_FLAG, type: VARCHAR }
          - { name: RECRUITMENT_COUNTRY, type: VARCHAR }
          - { name: RECRUITMENT_DESIGN_TYPE, type: VARCHAR }
          - { name: RECRUITMENT_DESIGN_VERSION, type: VARCHAR }
          - { name: RECRUITMENT_METHOD, type: VARCHAR }
          - { name: RECRUITMENT_START_DATE, type: DATE }
          - { name: RFSSMI_FLAG, type: VARCHAR }
          - { name: SUBJECTS_RECRUITED_TYPE, type: VARCHAR }
          - { name: SUBJ_TARGET_COMPLETERS_NUM, type: BIGINT }
          - { name: TMF_REQUIREMENT_FLG, type: VARCHAR }
          - { name: DELETE_FLAG, type: VARCHAR }
      - name: srt_study
        schema:
          - { name: STUDY_ID, type: VARCHAR }
          - { name: COMMITTEE_ADJUDICATION_USED, type: VARCHAR }
          - { name: COMMITTEE_DMC_USED, type: VARCHAR }
          - { name: COMMITTEE_NONE_USED, type: VARCHAR }
          - { name: EU_APPROVED_PRODUCT, type: VARCHAR }
          - { name: IB_VERSION_DT, type: TIMESTAMP }
          - { name: PAPER_STUDY, type: VARCHAR }
          - { name: PATIENT_DATABASE, type: VARCHAR }
          - { name: TOT_SUBJ_PLANNED_STUDY, type: BIGINT }
          - { name: PRIMARY_DATA_COLLECTION, type: VARCHAR }
          - { name: SECONDARY_DATA_COLLECTION, type: VARCHAR }
          - { name: SUBJECTS_RECRUITED_TYPE, type: VARCHAR }
          - { name: SUBJ_TARGET_COMPLETERS_NUM, type: BIGINT }
          - { name: DATA_RETURN_PLAN_COMPLETE_FLAG, type: VARCHAR }
          - { name: PARTICIPANT_DATA_WITHHELD_UNTIL_LSLV_FLAG, type: VARCHAR }
          - { name: PARTICIPANT_ELIGIBLE_TO_RETURN_FLAG, type: VARCHAR }
          - { name: DELETE_FLAG, type: VARCHAR }
      - name: cv_study_data
        schema:
          - { name: STUDY_ID, type: VARCHAR }
          - { name: STUDY_BUSINESS_RATIONALE_CATEGORY, type: VARCHAR }
          - { name: STUDY_MED_RESPONSIBILTY, type: VARCHAR }
          - { name: STUDY_PROJECT_PLAN_FINANCE_TYP, type: VARCHAR }
          - { name: STUDY_SAP_FINISH_DATE, type: TIMESTAMP }
          - { name: STUDY_PCNT_COMP_SAP, type: BIGINT }
          - { name: STUDY_SAP_START_DATE, type: TIMESTAMP }
          - { name: STUDY_CPM, type: VARCHAR }
          - { name: STUDY_EXECUTION_STATE, type: VARCHAR }
          - { name: STUDY_PERFORMING_SITE, type: VARCHAR }
          - { name: STUDY_PROJECT_PLAN_NAME, type: VARCHAR }
          - { name: STUDY_PROJECT_PLAN_TEMPLATE_NAME, type: VARCHAR }
          - { name: STUDY_STATUS_PLAN, type: VARCHAR }
      - name: dsopi_st_cln_study_portfolio
        schema:
          - { name: STUDY_ID, type: VARCHAR }
          - { name: BUSINESS_GROUP, type: VARCHAR }
          - { name: CCS_CLINICAL_PLACEMENT, type: VARCHAR }

    target_columns:
    """))
    # We'll add target_columns entries for each column
    for col in COLUMNS:
        f.write(f"  {col['name']}:\n")
        f.write(f"    source_columns: {col['past_sources']}\n")
        f.write(f"    sql_file: sql/{col['name'].lower()}.sql\n")


# ── Read the full.sql CTEs for the past pipeline ─────────────────────

PAST_FULL = open(os.path.join(BASE, "memory/star_schema_pipeline/full.sql")).read()
# Extract the 4 transform CTEs (everything before study_portfolio_overview)
cte_block_end = PAST_FULL.index("study_portfolio_overview AS (")
PAST_CTES = PAST_FULL[len("WITH\n"):cte_block_end]

PAST_JOIN = """\
  FROM dsopi_transformed AS in0
  INNER JOIN srt_transformed AS in1 ON in0.STUDY_ID = in1.STUDY_ID
  INNER JOIN cv_transformed AS in2 ON COALESCE(in0.STUDY_ID, in1.STUDY_ID) = in2.STUDY_ID
  JOIN portfolio_details AS in3 ON COALESCE(in0.STUDY_ID, in1.STUDY_ID) = in3.STUDY_ID"""


# ── Generate past per-column SQL ─────────────────────────────────────

past_sql_dir = os.path.join(BASE, "memory/star_schema_pipeline/sql")
os.makedirs(past_sql_dir, exist_ok=True)
for col in COLUMNS:
    fname = os.path.join(past_sql_dir, f"{col['name'].lower()}.sql")
    expr = col["past_expr"].replace("\\n", "\n")
    sql = f"""WITH\n{PAST_CTES}study_portfolio_overview AS (
  SELECT
    {expr} AS {col['name']}
{PAST_JOIN}
)
SELECT {col['name']} FROM study_portfolio_overview
"""
    with open(fname, "w") as f:
        f.write(sql)


# ── Generate expected per-column SQL ─────────────────────────────────

expected_sql_dir = os.path.join(BASE, "expected/sql")
os.makedirs(expected_sql_dir, exist_ok=True)
for col in COLUMNS:
    fname = os.path.join(expected_sql_dir, f"{col['name'].lower()}.sql")
    expr = col["expected_expr"].replace("\\n", "\n")
    sql = f"""-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    {expr} AS {col['name']}
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT {col['name']} FROM metrics_joined
"""
    with open(fname, "w") as f:
        f.write(sql)

print(f"Generated {len(COLUMNS)} past per-column SQL files")
print(f"Generated {len(COLUMNS)} expected per-column SQL files")
print(f"Generated 4 past CSV files + 2 current CSV files")
print(f"Generated memory.yaml")
print("Done!")
