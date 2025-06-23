"""
SentinelOps Detection Agent - Threat Intelligence Enhanced Queries
Integrates free threat intel feeds with detection rules for real-time enrichment
"""

import logging
import re
from typing import Dict

logger = logging.getLogger(__name__)


class ThreatIntelQueries:
    """Enhanced detection queries with threat intelligence integration"""

    def __init__(self, project_id: str, threat_intel_dataset: str = "threat_intel"):
        self.project_id = self._validate_bigquery_identifier(project_id, "project_id")
        self.threat_intel_dataset = self._validate_bigquery_identifier(threat_intel_dataset, "dataset")

    def _validate_bigquery_identifier(self, identifier: str, identifier_type: str) -> str:
        """Validate BigQuery identifiers to prevent SQL injection"""
        # BigQuery identifier rules: letters, numbers, underscores, max 1024 chars
        if not identifier:
            raise ValueError(f"{identifier_type} cannot be empty")
        if len(identifier) > 1024:
            raise ValueError(f"{identifier_type} exceeds maximum length of 1024 characters")
        # Check for valid BigQuery identifier pattern
        if not re.match(r'^[a-zA-Z0-9_-]+$', identifier):
            raise ValueError(f"Invalid {identifier_type}: contains illegal characters")
        return identifier

    def get_malicious_ip_connections(self, hours_back: int = 24) -> str:
        """
        Detect connections to known malicious IPs from threat intel feeds
        """
        # Validate hours_back parameter
        if not isinstance(hours_back, int) or hours_back <= 0 or hours_back > 8760:  # Max 1 year
            raise ValueError("hours_back must be a positive integer between 1 and 8760")

        # Build query using string concatenation to avoid f-string SQL construction
        query_parts = []

        # Recent connections CTE
        query_parts.append("WITH recent_connections AS (")
        query_parts.append("  SELECT")
        query_parts.append("    jsonPayload.connection.src_ip,")
        query_parts.append("    jsonPayload.connection.dest_ip,")
        query_parts.append("    jsonPayload.connection.dest_port,")
        query_parts.append("    jsonPayload.connection.protocol,")
        query_parts.append("    timestamp,")
        query_parts.append("    jsonPayload.src_vpc.vpc_name,")
        query_parts.append("    jsonPayload.src_vpc.subnetwork_name")
        query_parts.append("  FROM `" + self.project_id + ".sentinelops_logs.vpc_flow_logs`")
        query_parts.append("  WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL " + str(hours_back) + " HOUR)")
        query_parts.append("    AND jsonPayload.connection IS NOT NULL")
        query_parts.append("),")
        query_parts.append("")

        # Threat matches CTE
        query_parts.append("threat_matches AS (")
        query_parts.append("  SELECT")
        query_parts.append("    rc.*,")
        query_parts.append("    ti.source as threat_source,")
        query_parts.append("    ti.severity as threat_severity,")
        query_parts.append("    ti.confidence as threat_confidence,")
        query_parts.append("    'outbound_malicious_connection' as detection_type")
        query_parts.append("  FROM recent_connections rc")
        query_parts.append("  LEFT JOIN `" + self.project_id + "." + self.threat_intel_dataset + ".threat_indicators` ti")
        query_parts.append("    ON rc.dest_ip = ti.indicator")
        query_parts.append("  WHERE ti.indicator IS NOT NULL")
        query_parts.append("    AND ti.confidence >= 0.7")
        query_parts.append("")
        query_parts.append("  UNION ALL")
        query_parts.append("")
        query_parts.append("  SELECT")
        query_parts.append("    rc.*,")
        query_parts.append("    ti.source as threat_source,")
        query_parts.append("    ti.severity as threat_severity,")
        query_parts.append("    ti.confidence as threat_confidence,")
        query_parts.append("    'inbound_malicious_connection' as detection_type")
        query_parts.append("  FROM recent_connections rc")
        query_parts.append("  LEFT JOIN `" + self.project_id + "." + self.threat_intel_dataset + ".threat_indicators` ti")
        query_parts.append("    ON rc.src_ip = ti.indicator")
        query_parts.append("  WHERE ti.indicator IS NOT NULL")
        query_parts.append("    AND ti.confidence >= 0.7")
        query_parts.append(")")
        query_parts.append("")

        # Main query
        query_parts.append("SELECT")
        query_parts.append("  detection_type,")
        query_parts.append("  src_ip,")
        query_parts.append("  dest_ip,")
        query_parts.append("  dest_port,")
        query_parts.append("  protocol,")
        query_parts.append("  threat_source,")
        query_parts.append("  threat_severity,")
        query_parts.append("  threat_confidence,")
        query_parts.append("  vpc_name,")
        query_parts.append("  subnetwork_name,")
        query_parts.append("  COUNT(*) as connection_count,")
        query_parts.append("  MIN(timestamp) as first_seen,")
        query_parts.append("  MAX(timestamp) as last_seen,")
        query_parts.append("  CURRENT_TIMESTAMP() as detection_timestamp")
        query_parts.append("FROM threat_matches")
        query_parts.append("GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10")
        query_parts.append("HAVING connection_count >= 3  -- Reduce noise")
        query_parts.append("ORDER BY threat_confidence DESC, connection_count DESC")

        return "\n".join(query_parts)

    def get_vulnerable_asset_exploitation_attempts(self, hours_back: int = 24) -> str:
        """
        Cross-reference web application logs with CISA KEV for exploitation attempts
        """
        # Validate hours_back parameter
        if not isinstance(hours_back, int) or hours_back <= 0 or hours_back > 8760:  # Max 1 year
            raise ValueError("hours_back must be a positive integer between 1 and 8760")

        # Build query using string concatenation to avoid f-string SQL construction
        query_parts = []

        # Recent web requests CTE
        query_parts.append("WITH recent_web_requests AS (")
        query_parts.append("  SELECT")
        query_parts.append("    httpRequest.remoteIp as src_ip,")
        query_parts.append("    httpRequest.requestUrl as request_url,")
        query_parts.append("    httpRequest.requestMethod as method,")
        query_parts.append("    httpRequest.status as response_code,")
        query_parts.append("    httpRequest.userAgent as user_agent,")
        query_parts.append("    timestamp,")
        query_parts.append("    resource.labels.service_name")
        query_parts.append("  FROM `" + self.project_id + ".sentinelops_logs.application_logs`")
        query_parts.append("  WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL " + str(hours_back) + " HOUR)")
        query_parts.append("    AND httpRequest IS NOT NULL")
        query_parts.append("    AND httpRequest.status BETWEEN 200 AND 299  -- Successful requests")
        query_parts.append("),")
        query_parts.append("")

        # Exploitation patterns CTE
        query_parts.append("exploitation_patterns AS (")
        query_parts.append("  SELECT")
        query_parts.append("    wr.*,")
        query_parts.append("    kev.cveID,")
        query_parts.append("    kev.vulnerabilityName,")
        query_parts.append("    kev.shortDescription,")
        query_parts.append("    kev.knownRansomwareCampaignUse,")
        query_parts.append("    'cve_exploitation_attempt' as detection_type,")
        query_parts.append("    CASE")
        query_parts.append("      WHEN kev.knownRansomwareCampaignUse = 'Known' THEN 'CRITICAL'")
        query_parts.append("      WHEN DATE_DIFF(CURRENT_DATE(), kev.dueDate) > 0 THEN 'HIGH'")
        query_parts.append("      ELSE 'MEDIUM'")
        query_parts.append("    END as calculated_severity")
        query_parts.append("  FROM recent_web_requests wr")
        query_parts.append("  CROSS JOIN `" + self.project_id + "." + self.threat_intel_dataset + ".cisa_kev` kev")
        query_parts.append("  WHERE (")
        query_parts.append("    -- Check for CVE patterns in URL or User-Agent")
        query_parts.append("    REGEXP_CONTAINS(")
        query_parts.append("      wr.request_url,")
        query_parts.append("      CONCAT('(?i)', REGEXP_REPLACE(kev.product, r'[^a-zA-Z0-9]', '.*'))")
        query_parts.append("    )")
        query_parts.append("    OR REGEXP_CONTAINS(wr.user_agent, CONCAT('(?i)', REGEXP_REPLACE(kev.product, r'[^a-zA-Z0-9]', '.*')))")
        query_parts.append("    OR REGEXP_CONTAINS(wr.request_url, r'(?i)(exploit|poc|cve-[0-9]{4}-[0-9]{4,})')")
        query_parts.append("  )")
        query_parts.append("),")
        query_parts.append("")

        # Enriched with threat intel CTE
        query_parts.append("enriched_with_threat_intel AS (")
        query_parts.append("  SELECT")
        query_parts.append("    ep.*,")
        query_parts.append("    ti.source as threat_intel_source,")
        query_parts.append("    ti.confidence as ip_reputation_confidence")
        query_parts.append("  FROM exploitation_patterns ep")
        query_parts.append("  LEFT JOIN `" + self.project_id + "." + self.threat_intel_dataset + ".threat_indicators` ti")
        query_parts.append("    ON ep.src_ip = ti.indicator")
        query_parts.append(")")
        query_parts.append("")

        # Main query
        query_parts.append("SELECT")
        query_parts.append("  detection_type,")
        query_parts.append("  src_ip,")
        query_parts.append("  cveID,")
        query_parts.append("  vulnerabilityName,")
        query_parts.append("  calculated_severity,")
        query_parts.append("  threat_intel_source,")
        query_parts.append("  ip_reputation_confidence,")
        query_parts.append("  service_name,")
        query_parts.append("  COUNT(*) as attempt_count,")
        query_parts.append("  COUNT(DISTINCT request_url) as unique_urls,")
        query_parts.append("  STRING_AGG(DISTINCT SUBSTR(request_url, 1, 100), '; ' LIMIT 5) as sample_urls,")
        query_parts.append("  MIN(timestamp) as first_attempt,")
        query_parts.append("  MAX(timestamp) as last_attempt,")
        query_parts.append("  CURRENT_TIMESTAMP() as detection_timestamp")
        query_parts.append("FROM enriched_with_threat_intel")
        query_parts.append("GROUP BY 1, 2, 3, 4, 5, 6, 7, 8")
        query_parts.append("ORDER BY calculated_severity DESC, attempt_count DESC")

        return "\n".join(query_parts)

    def get_suspicious_dns_activity(self, hours_back: int = 24) -> str:
        """
        Detect DNS queries to suspicious domains using threat intel
        """
        # Validate hours_back parameter
        if not isinstance(hours_back, int) or hours_back <= 0 or hours_back > 8760:  # Max 1 year
            raise ValueError("hours_back must be a positive integer between 1 and 8760")

        # Build query using string concatenation to avoid f-string SQL construction
        query_parts = []

        # Recent DNS queries CTE
        query_parts.append("WITH recent_dns_queries AS (")
        query_parts.append("  SELECT")
        query_parts.append("    jsonPayload.sourceIP as src_ip,")
        query_parts.append("    jsonPayload.queryName as domain,")
        query_parts.append("    jsonPayload.queryType as query_type,")
        query_parts.append("    jsonPayload.responseCode as response_code,")
        query_parts.append("    timestamp,")
        query_parts.append("    jsonPayload.location")
        query_parts.append("  FROM `" + self.project_id + ".sentinelops_logs.dns_logs`")
        query_parts.append("  WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL " + str(hours_back) + " HOUR)")
        query_parts.append("    AND jsonPayload.queryName IS NOT NULL")
        query_parts.append("),")
        query_parts.append("")

        # Suspicious domains CTE
        query_parts.append("suspicious_domains AS (")
        query_parts.append("  SELECT DISTINCT")
        query_parts.append("    dq.*,")
        query_parts.append("    'domain_reputation' as detection_type,")
        query_parts.append("    'HIGH' as severity,")
        query_parts.append("    0.8 as confidence")
        query_parts.append("  FROM recent_dns_queries dq")
        query_parts.append("  WHERE (")
        query_parts.append("    -- DGA-like domains (high entropy)")
        query_parts.append("    LENGTH(REGEXP_EXTRACT(dq.domain, r'^([^.]+)')) >= 12")
        query_parts.append("    AND REGEXP_CONTAINS(dq.domain, r'^[a-z0-9]{12,}\\.')")
        query_parts.append("")
        query_parts.append("    -- Suspicious TLDs")
        query_parts.append("    OR REGEXP_CONTAINS(dq.domain, r'\\.(tk|ml|ga|cf|bit|onion)$')")
        query_parts.append("")
        query_parts.append("    -- IP addresses as domains")
        query_parts.append("    OR REGEXP_CONTAINS(dq.domain, r'^[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}$')")
        query_parts.append("")
        query_parts.append("    -- Known bad patterns")
        query_parts.append("    OR REGEXP_CONTAINS(dq.domain, r'(?i)(dyndns|no-ip|ddns|ngrok|localtunnel)')")
        query_parts.append("  )")
        query_parts.append("),")
        query_parts.append("")

        # DNS tunneling candidates CTE
        query_parts.append("dns_tunneling_candidates AS (")
        query_parts.append("  SELECT")
        query_parts.append("    src_ip,")
        query_parts.append("    domain,")
        query_parts.append("    COUNT(*) as query_count,")
        query_parts.append("    COUNT(DISTINCT query_type) as query_type_variety,")
        query_parts.append("    AVG(LENGTH(domain)) as avg_domain_length,")
        query_parts.append("    'dns_tunneling' as detection_type,")
        query_parts.append("    'MEDIUM' as severity,")
        query_parts.append("    0.7 as confidence")
        query_parts.append("  FROM recent_dns_queries")
        query_parts.append("  GROUP BY src_ip, domain")
        query_parts.append("  HAVING query_count >= 50  -- High query volume")
        query_parts.append("    AND avg_domain_length >= 20  -- Long domain names")
        query_parts.append("    AND query_type_variety >= 2  -- Multiple query types")
        query_parts.append("),")
        query_parts.append("")

        # Enriched suspicious activity CTE
        query_parts.append("enriched_suspicious_activity AS (")
        query_parts.append("  SELECT")
        query_parts.append("    sd.src_ip,")
        query_parts.append("    sd.domain,")
        query_parts.append("    sd.detection_type,")
        query_parts.append("    sd.severity,")
        query_parts.append("    sd.confidence,")
        query_parts.append("    ti.source as threat_intel_source,")
        query_parts.append("    ti.confidence as ip_reputation_confidence,")
        query_parts.append("    COUNT(*) as query_count,")
        query_parts.append("    MIN(sd.timestamp) as first_seen,")
        query_parts.append("    MAX(sd.timestamp) as last_seen")
        query_parts.append("  FROM suspicious_domains sd")
        query_parts.append("  LEFT JOIN `" + self.project_id + "." + self.threat_intel_dataset + ".threat_indicators` ti")
        query_parts.append("    ON sd.src_ip = ti.indicator")
        query_parts.append("  GROUP BY 1, 2, 3, 4, 5, 6, 7")
        query_parts.append("")
        query_parts.append("  UNION ALL")
        query_parts.append("")
        query_parts.append("  SELECT")
        query_parts.append("    dtc.src_ip,")
        query_parts.append("    dtc.domain,")
        query_parts.append("    dtc.detection_type,")
        query_parts.append("    dtc.severity,")
        query_parts.append("    dtc.confidence,")
        query_parts.append("    ti.source as threat_intel_source,")
        query_parts.append("    ti.confidence as ip_reputation_confidence,")
        query_parts.append("    dtc.query_count,")
        query_parts.append("    TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR) as first_seen,")
        query_parts.append("    CURRENT_TIMESTAMP() as last_seen")
        query_parts.append("  FROM dns_tunneling_candidates dtc")
        query_parts.append("  LEFT JOIN `" + self.project_id + "." + self.threat_intel_dataset + ".threat_indicators` ti")
        query_parts.append("    ON dtc.src_ip = ti.indicator")
        query_parts.append(")")
        query_parts.append("")

        # Main query
        query_parts.append("SELECT")
        query_parts.append("  *,")
        query_parts.append("  CURRENT_TIMESTAMP() as detection_timestamp")
        query_parts.append("FROM enriched_suspicious_activity")
        query_parts.append("ORDER BY")
        query_parts.append("  CASE")
        query_parts.append("    WHEN severity = 'CRITICAL' THEN 1")
        query_parts.append("    WHEN severity = 'HIGH' THEN 2")
        query_parts.append("    WHEN severity = 'MEDIUM' THEN 3")
        query_parts.append("    ELSE 4")
        query_parts.append("  END,")
        query_parts.append("  query_count DESC")

        return "\n".join(query_parts)

    def get_mitre_attack_correlation(self, hours_back: int = 24) -> str:
        """
        Correlate detected activities with MITRE ATT&CK techniques
        """
        # Validate hours_back parameter
        if not isinstance(hours_back, int) or hours_back <= 0 or hours_back > 8760:  # Max 1 year
            raise ValueError("hours_back must be a positive integer between 1 and 8760")

        # Build query using string concatenation to avoid f-string SQL construction
        query_parts = []

        # Recent security events CTE
        query_parts.append("WITH recent_security_events AS (")
        query_parts.append("  -- Combine various detection types")
        query_parts.append("  SELECT")
        query_parts.append("    'malicious_ip_connection' as event_type,")
        query_parts.append("    src_ip,")
        query_parts.append("    dest_ip as target,")
        query_parts.append("    threat_severity as severity,")
        query_parts.append("    detection_timestamp,")
        query_parts.append("    'T1071' as suspected_technique  -- Application Layer Protocol")
        query_parts.append("  FROM `" + self.project_id + ".sentinelops_detections.malicious_ip_connections`")
        query_parts.append("  WHERE detection_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL " + str(hours_back) + " HOUR)")
        query_parts.append("")
        query_parts.append("  UNION ALL")
        query_parts.append("")
        query_parts.append("  SELECT")
        query_parts.append("    'cve_exploitation' as event_type,")
        query_parts.append("    src_ip,")
        query_parts.append("    service_name as target,")
        query_parts.append("    calculated_severity as severity,")
        query_parts.append("    detection_timestamp,")
        query_parts.append("    'T1190' as suspected_technique  -- Exploit Public-Facing Application")
        query_parts.append("  FROM `" + self.project_id + ".sentinelops_detections.cve_exploitation_attempts`")
        query_parts.append("  WHERE detection_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL " + str(hours_back) + " HOUR)")
        query_parts.append("")
        query_parts.append("  UNION ALL")
        query_parts.append("")
        query_parts.append("  SELECT")
        query_parts.append("    'dns_tunneling' as event_type,")
        query_parts.append("    src_ip,")
        query_parts.append("    domain as target,")
        query_parts.append("    severity,")
        query_parts.append("    detection_timestamp,")
        query_parts.append("    'T1071.004' as suspected_technique  -- DNS Tunneling")
        query_parts.append("  FROM `" + self.project_id + ".sentinelops_detections.suspicious_dns_activity`")
        query_parts.append("  WHERE detection_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL " + str(hours_back) + " HOUR)")
        query_parts.append("    AND detection_type = 'dns_tunneling'")
        query_parts.append("),")
        query_parts.append("")

        # Attack timeline CTE
        query_parts.append("attack_timeline AS (")
        query_parts.append("  SELECT")
        query_parts.append("    se.*,")
        query_parts.append("    mt.technique_name,")
        query_parts.append("    mt.tactic,")
        query_parts.append("    mt.platform,")
        query_parts.append("    mt.description as technique_description")
        query_parts.append("  FROM recent_security_events se")
        query_parts.append("  LEFT JOIN `" + self.project_id + "." + self.threat_intel_dataset + ".mitre_attack` mt")
        query_parts.append("    ON se.suspected_technique = mt.technique_id")
        query_parts.append("),")
        query_parts.append("")

        # Attack chains CTE
        query_parts.append("attack_chains AS (")
        query_parts.append("  SELECT")
        query_parts.append("    src_ip,")
        query_parts.append("    STRING_AGG(DISTINCT tactic ORDER BY detection_timestamp) as tactic_sequence,")
        query_parts.append("    STRING_AGG(DISTINCT technique_name ORDER BY detection_timestamp) as technique_sequence,")
        query_parts.append("    COUNT(DISTINCT event_type) as event_variety,")
        query_parts.append("    COUNT(*) as total_events,")
        query_parts.append("    MIN(detection_timestamp) as campaign_start,")
        query_parts.append("    MAX(detection_timestamp) as campaign_end,")
        query_parts.append("    TIMESTAMP_DIFF(MAX(detection_timestamp), MIN(detection_timestamp), MINUTE) as duration_minutes")
        query_parts.append("  FROM attack_timeline")
        query_parts.append("  WHERE technique_name IS NOT NULL")
        query_parts.append("  GROUP BY src_ip")
        query_parts.append("  HAVING event_variety >= 2  -- Multi-stage attacks")
        query_parts.append(")")
        query_parts.append("")

        # Main query
        query_parts.append("SELECT")
        query_parts.append("  ac.*,")
        query_parts.append("  ti.source as threat_intel_source,")
        query_parts.append("  ti.severity as ip_reputation_severity,")
        query_parts.append("  ti.confidence as ip_reputation_confidence,")
        query_parts.append("  CASE")
        query_parts.append("    WHEN duration_minutes <= 60 AND event_variety >= 3 THEN 'CRITICAL'")
        query_parts.append("    WHEN event_variety >= 2 THEN 'HIGH'")
        query_parts.append("    ELSE 'MEDIUM'")
        query_parts.append("  END as campaign_severity,")
        query_parts.append("  CURRENT_TIMESTAMP() as analysis_timestamp")
        query_parts.append("FROM attack_chains ac")
        query_parts.append("LEFT JOIN `" + self.project_id + "." + self.threat_intel_dataset + ".threat_indicators` ti")
        query_parts.append("  ON ac.src_ip = ti.indicator")
        query_parts.append("ORDER BY campaign_severity DESC, event_variety DESC, duration_minutes ASC")

        return "\n".join(query_parts)

    def create_detection_views(self) -> Dict[str, str]:
        """
        Create BigQuery views for all detection queries
        """
        views = {
            "malicious_ip_connections": self.get_malicious_ip_connections(),
            "cve_exploitation_attempts": self.get_vulnerable_asset_exploitation_attempts(),
            "suspicious_dns_activity": self.get_suspicious_dns_activity(),
            "mitre_attack_correlation": self.get_mitre_attack_correlation(),
        }

        return views

    def get_threat_intel_enrichment_udf(self) -> str:
        """
        BigQuery UDF for threat intelligence lookups
        """
        # Build query using string concatenation to avoid f-string SQL construction
        udf_parts = []

        # IS_MALICIOUS_IP function
        udf_parts.append("CREATE OR REPLACE FUNCTION `" + self.project_id + "." + self.threat_intel_dataset + ".IS_MALICIOUS_IP`(ip STRING)")
        udf_parts.append("RETURNS STRUCT<is_malicious BOOL, source STRING, severity STRING, confidence FLOAT64>")
        udf_parts.append("AS ((")
        udf_parts.append("  SELECT AS STRUCT")
        udf_parts.append("    CASE WHEN ti.indicator IS NOT NULL THEN TRUE ELSE FALSE END as is_malicious,")
        udf_parts.append("    COALESCE(ti.source, 'unknown') as source,")
        udf_parts.append("    COALESCE(ti.severity, 'unknown') as severity,")
        udf_parts.append("    COALESCE(ti.confidence, 0.0) as confidence")
        udf_parts.append("  FROM `" + self.project_id + "." + self.threat_intel_dataset + ".threat_indicators` ti")
        udf_parts.append("  WHERE ti.indicator = ip")
        udf_parts.append("    AND ti.confidence >= 0.7")
        udf_parts.append("  ORDER BY ti.confidence DESC")
        udf_parts.append("  LIMIT 1")
        udf_parts.append("));")
        udf_parts.append("")

        # GET_CVE_INFO function
        udf_parts.append("CREATE OR REPLACE FUNCTION `" + self.project_id + "." + self.threat_intel_dataset + ".GET_CVE_INFO`(product STRING)")
        udf_parts.append("RETURNS STRUCT<has_known_exploits BOOL, cve_count INT64, ransomware_risk BOOL>")
        udf_parts.append("AS ((")
        udf_parts.append("  SELECT AS STRUCT")
        udf_parts.append("    COUNT(*) > 0 as has_known_exploits,")
        udf_parts.append("    COUNT(*) as cve_count,")
        udf_parts.append("    COUNTIF(knownRansomwareCampaignUse = 'Known') > 0 as ransomware_risk")
        udf_parts.append(
            "  FROM `" + self.project_id + "."
            + self.threat_intel_dataset + ".cisa_kev`"
        )
        udf_parts.append("  WHERE REGEXP_CONTAINS(LOWER(product), LOWER(product))")
        udf_parts.append("     OR REGEXP_CONTAINS(LOWER(vulnerabilityName), LOWER(product))")
        udf_parts.append("));")

        return "\n".join(udf_parts)

    def get_real_time_threat_scoring_query(self) -> str:
        """
        Real-time threat scoring based on multiple indicators
        """
        # Build query using string concatenation to avoid f-string SQL construction
        query_parts = []

        # Threat scores CTE
        query_parts.append("WITH threat_scores AS (")
        query_parts.append("  SELECT")
        query_parts.append("    src_ip,")
        query_parts.append("    -- IP reputation score (0-40 points)")
        query_parts.append("    CASE")
        query_parts.append("      WHEN ti.confidence >= 0.9 THEN 40")
        query_parts.append("      WHEN ti.confidence >= 0.8 THEN 30")
        query_parts.append("      WHEN ti.confidence >= 0.7 THEN 20")
        query_parts.append("      ELSE 0")
        query_parts.append("    END as ip_reputation_score,")
        query_parts.append("")
        query_parts.append("    -- Geographic risk score (0-20 points)")
        query_parts.append("    CASE")
        query_parts.append("      WHEN country_code IN ('CN', 'RU', 'IR', 'KP') THEN 20")
        query_parts.append("      WHEN country_code IN ('BR', 'IN', 'VN') THEN 10")
        query_parts.append("      ELSE 0")
        query_parts.append("    END as geo_risk_score,")
        query_parts.append("")
        query_parts.append("    -- Behavioral anomaly score (0-40 points)")
        query_parts.append("    CASE")
        query_parts.append("      WHEN connection_count >= 1000 THEN 40")
        query_parts.append("      WHEN connection_count >= 100 THEN 30")
        query_parts.append("      WHEN connection_count >= 50 THEN 20")
        query_parts.append("      WHEN connection_count >= 10 THEN 10")
        query_parts.append("      ELSE 0")
        query_parts.append("    END as behavioral_score,")
        query_parts.append("")
        query_parts.append("    ti.source as threat_source,")
        query_parts.append("    ti.severity as threat_severity")
        query_parts.append("  FROM (")
        query_parts.append("    SELECT")
        query_parts.append("      src_ip,")
        query_parts.append("      COUNT(*) as connection_count")
        query_parts.append(
            "    FROM `" + self.project_id
            + ".sentinelops_logs.vpc_flow_logs`"
        )
        query_parts.append(
            "    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), "
            "INTERVAL 1 HOUR)"
        )
        query_parts.append("    GROUP BY src_ip")
        query_parts.append("  ) connections")
        query_parts.append(
            "  LEFT JOIN `" + self.project_id + "."
            + self.threat_intel_dataset + ".threat_indicators` ti"
        )
        query_parts.append("    ON connections.src_ip = ti.indicator")
        query_parts.append(
            "  LEFT JOIN `" + self.project_id + "."
            + self.threat_intel_dataset + ".abuseipdb_blacklist` abuse"
        )
        query_parts.append("    ON connections.src_ip = abuse.ip")
        query_parts.append(")")
        query_parts.append("")

        # Main query
        query_parts.append("SELECT")
        query_parts.append("  src_ip,")
        query_parts.append(
            "  ip_reputation_score + geo_risk_score + behavioral_score "
            "as total_threat_score,"
        )
        query_parts.append("  ip_reputation_score,")
        query_parts.append("  geo_risk_score,")
        query_parts.append("  behavioral_score,")
        query_parts.append("  threat_source,")
        query_parts.append("  threat_severity,")
        query_parts.append("  CASE")
        query_parts.append("    WHEN ip_reputation_score + geo_risk_score + behavioral_score >= 80 THEN 'CRITICAL'")
        query_parts.append("    WHEN ip_reputation_score + geo_risk_score + behavioral_score >= 60 THEN 'HIGH'")
        query_parts.append("    WHEN ip_reputation_score + geo_risk_score + behavioral_score >= 40 THEN 'MEDIUM'")
        query_parts.append("    ELSE 'LOW'")
        query_parts.append("  END as calculated_risk_level,")
        query_parts.append("  CURRENT_TIMESTAMP() as score_timestamp")
        query_parts.append("FROM threat_scores")
        query_parts.append("WHERE ip_reputation_score + geo_risk_score + behavioral_score > 0")
        query_parts.append("ORDER BY total_threat_score DESC")

        return "\n".join(query_parts)
