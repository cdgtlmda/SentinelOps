# Detection Agent Configuration for Pagination

The following configuration parameters have been added to support BigQuery result pagination:

## Configuration Parameters

Add these to your configuration under `agents.detection`:

```yaml
agents:
  detection:
    # Pagination settings
    query_page_size: 1000          # Number of results per page (default: 1000)
    max_results_per_query: 10000   # Maximum total results per query (default: 10000)
    query_timeout_ms: 30000        # Query timeout in milliseconds (default: 30000)
    max_events_per_rule: 5000      # Maximum events to process per rule (default: 5000)
```

## Features Implemented

1. **Paginated Query Executor**: A new `PaginatedQueryExecutor` class handles efficient pagination of large query results
2. **Memory-efficient processing**: Results are processed in pages to avoid memory issues with large datasets
3. **Configurable limits**: Page size and maximum results are configurable
4. **Automatic pagination**: The detection agent automatically uses pagination for all detection queries

## Usage

The pagination is transparent to the detection rules. Simply configure the parameters above and the agent will:
- Execute queries with pagination support
- Process results in manageable chunks
- Stop processing when limits are reached
- Log warnings when limits are hit

## Performance Benefits

- Reduced memory usage for large result sets
- Better handling of queries that return millions of rows
- Prevents timeout issues with long-running queries
- Allows processing to stop early when sufficient events are found
