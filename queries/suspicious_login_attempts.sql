
-- Detect suspicious login attempts
SELECT 
    timestamp,
    principal_email,
    authentication_info,
    COUNT(*) as attempt_count,
    ARRAY_AGG(DISTINCT JSON_EXTRACT_SCALAR(request, '$.sourceIp')) as source_ips
FROM `your-gcp-project-id.sentinelops_dev.audit_logs`
WHERE method_name LIKE '%authenticate%'
    AND severity = 'ERROR'
    AND DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
GROUP BY timestamp, principal_email, authentication_info
HAVING attempt_count > 5
ORDER BY attempt_count DESC
