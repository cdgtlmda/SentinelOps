
-- Detect privilege escalation attempts
SELECT 
    timestamp,
    principal,
    resource,
    bindings,
    JSON_EXTRACT_SCALAR(policy_delta, '$.action') as action
FROM `your-gcp-project-id.sentinelops_dev.iam_logs`
WHERE operation.type IN ('SetIamPolicy', 'UpdateRole')
    AND DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    AND EXISTS (
        SELECT 1 FROM UNNEST(bindings) AS b
        WHERE b.role IN ('roles/owner', 'roles/editor', 'roles/iam.securityAdmin')
    )
ORDER BY timestamp DESC
