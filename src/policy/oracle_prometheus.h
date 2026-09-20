#ifndef BITCOIN_POLICY_ORACLE_PROMETHEUS_H
#define BITCOIN_POLICY_ORACLE_PROMETHEUS_H

#include <string>

namespace node {
struct NodeContext;
}

namespace OraclePrometheus {

/** Address the metrics exporter binds to unless -prometheusbind says otherwise. */
inline const std::string DEFAULT_PROMETHEUS_BIND{"127.0.0.1"};

// Start the Prometheus metrics exporter in a background thread. The exporter
// serves unauthenticated node telemetry, so bind_addr defaults to loopback.
void StartPrometheusExporter(const node::NodeContext& node, const std::string& bind_addr, int port);

// Stop the Prometheus exporter.
void StopPrometheusExporter();

} // namespace OraclePrometheus

#endif // BITCOIN_POLICY_ORACLE_PROMETHEUS_H
