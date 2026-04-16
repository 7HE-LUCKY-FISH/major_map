## Stress Test Results

This section summarizes database performance testing conducted using Sysbench against an AWS RDS MySQL instance connected to a FastAPI backend.

---

### Test Configurations

Two levels of concurrency were tested to evaluate system scalability.

#### Light Load Test (5 Threads)

| Parameter | Value |
|----------|------|
| Threads | 5 |
| Duration | ~20 seconds |
| Workload | OLTP read/write |
| Total Queries | ~2,320 |

#### Stress Load Test (50 Threads)

| Parameter | Value |
|----------|------|
| Threads | 50 |
| Duration | ~30 seconds |
| Workload | OLTP read/write |
| Total Queries | ~29,728 |

---

### 5-Thread Results

| Metric | Value |
|------|------|
| Transactions/sec (TPS) | 7.09 TPS |
| Queries/sec (QPS) | 113.47 QPS |
| Average Latency | 695.55 ms |
| Errors | 0 |
| Reconnects | 0 |

#### Observations
- System executed all requests successfully with no failures.
- Throughput remained stable but relatively low.
- High latency (~695 ms) suggests network or database overhead.
- System was not saturated at this load level.

---

### 50-Thread Results

| Metric | Value |
|------|------|
| Transactions/sec (TPS) | 60.44 TPS |
| Queries/sec (QPS) | 966.97 QPS |
| Average Latency | 817.93 ms |
| Minimum Latency | 671.13 ms |
| Maximum Latency | 1164.95 ms |
| Errors | 0 |
| Reconnects | 0 |

#### Observations
- System scaled successfully from 5 → 50 threads.
- Throughput increased significantly (~8× improvement).
- No errors or connection failures under heavy load.
- Latency increased slightly under stress conditions.
- System remained stable throughout execution.

---

### Key Performance Insights

#### Scalability
- System demonstrates good scalability under increasing concurrency.
- TPS increased from ~7 to ~60 when scaling from light to heavy load.
- Backend and database handle concurrent requests effectively.

#### Latency Behavior
- Latency increased from ~695 ms to ~818 ms under load.
- Likely due to:
  - Network latency between client and AWS RDS
  - Database processing overhead under concurrency

#### Reliability
- No errors recorded across all tests.
- No reconnects observed.
- System remained stable under all tested loads.

---

### Bottlenecks Identified

- **Network Latency:** Local machine to AWS RDS introduces round-trip delay.
- **Database Instance Limits:** Likely burstable RDS instance affecting performance.
- **Read-Heavy Workload:** Write operations were not included in this benchmark.

---

### System Limits (Observed)

- Stable up to 50 concurrent threads
- No failures under stress conditions
- Performance scales well at low-to-medium concurrency
- Maximum system capacity not yet reached

---

### Recommendations

- Enable connection pooling in FastAPI
- Add database indexing for frequently queried fields
- Run tests from AWS EC2 in the same region to reduce latency
- Upgrade RDS instance for higher performance testing
- Extend stress testing to 100+ threads
- Include write-heavy workloads for balanced evaluation

---

### Conclusion

The system demonstrates strong stability and reliable performance under both light and heavy load conditions. While throughput scales effectively with concurrency, latency remains elevated due to network overhead and database instance constraints. Overall, the system is suitable for moderate production workloads with clear opportunities for optimization.