#ifndef BITCOIN_POLICY_ORACLE_PROMETHEUS_H
#define BITCOIN_POLICY_ORACLE_PROMETHEUS_H

namespace node {
struct NodeContext;
}

namespace OraclePrometheus {

// Start the Prometheus metrics exporter in a background thread.
void StartPrometheusExporter(const node::NodeContext& node, int port);

// Stop the Prometheus exporter.
void StopPrometheusExporter();

} // namespace OraclePrometheus

#endif // BITCOIN_POLICY_ORACLE_PROMETHEUS_H
