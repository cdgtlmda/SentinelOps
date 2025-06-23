
-- Detect potential data exfiltration
SELECT 
    timestamp,
    connection.src_ip,
    connection.dest_ip,
    SUM(bytes_sent) as total_bytes,
    COUNT(*) as connection_count
FROM `your-gcp-project-id.sentinelops_dev.vpc_flow_logs`
WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
    AND connection.dest_port NOT IN (80, 443)  -- Non-standard ports
    AND reporter = 'SRC'
GROUP BY timestamp, connection.src_ip, connection.dest_ip
HAVING total_bytes > 1000000000  -- More than 1GB
ORDER BY total_bytes DESC
