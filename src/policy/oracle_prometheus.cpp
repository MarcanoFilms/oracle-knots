#include <policy/oracle_prometheus.h>
#include <policy/oracle_policy.h>
#include <node/context.h>
#include <node/miner.h>
#include <net.h>
#include <validation.h>
#include <deploymentstatus.h>
#include <consensus/params.h>
#include <txmempool.h>
#include <logging.h>
#include <util/time.h>

#include <thread>
#include <atomic>
#include <sstream>
#include <string>
#include <vector>
#include <cstring>
#include <cerrno>

#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <poll.h>

namespace OraclePrometheus {

static std::atomic<bool> g_prometheus_run{false};
static std::thread g_prometheus_thread;

static void ExporterThread(const node::NodeContext& node, int port) {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        LogPrintf("Oracle Prometheus: Error creating socket: %s\n", std::strerror(errno));
        return;
    }

    int opt = 1;
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        LogPrintf("Oracle Prometheus: Error setting SO_REUSEADDR: %s\n", std::strerror(errno));
        close(server_fd);
        return;
    }

    struct sockaddr_in address;
    std::memset(&address, 0, sizeof(address));
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY; // Bind to all interfaces
    address.sin_port = htons(port);

    if (bind(server_fd, (struct sockaddr*)&address, sizeof(address)) < 0) {
        LogPrintf("Oracle Prometheus: Error binding to port %d: %s\n", port, std::strerror(errno));
        close(server_fd);
        return;
    }

    if (listen(server_fd, 5) < 0) {
        LogPrintf("Oracle Prometheus: Error listening: %s\n", std::strerror(errno));
        close(server_fd);
        return;
    }

    LogPrintf("Oracle Prometheus: Exporter listening on port %d\n", port);

    struct pollfd fds[1];
    fds[0].fd = server_fd;
    fds[0].events = POLLIN;

    while (g_prometheus_run) {
        int ret = poll(fds, 1, 500); // 500ms timeout
        if (ret < 0) {
            if (errno == EINTR) continue;
            LogPrintf("Oracle Prometheus: Poll error: %s\n", std::strerror(errno));
            break;
        }
        if (ret == 0) continue; // Timeout, check loop condition

        if (fds[0].revents & POLLIN) {
            int client_fd = accept(server_fd, nullptr, nullptr);
            if (client_fd >= 0) {
                // Read request headers (and ignore them)
                char buffer[1024];
                int bytes_read = recv(client_fd, buffer, sizeof(buffer) - 1, 0);
                if (bytes_read > 0) {
                    buffer[bytes_read] = '\0';
                }

                std::stringstream metrics;

                // 1. Block Height
                int block_height = node.chainman ? node.chainman->ActiveChain().Height() : 0;
                metrics << "# HELP bitcoin_blocks Current block height\n"
                        << "# TYPE bitcoin_blocks gauge\n"
                        << "bitcoin_blocks " << block_height << "\n\n";

                // 2. Mempool metrics
                if (node.mempool) {
                    metrics << "# HELP bitcoin_mempool_size Number of transactions in mempool\n"
                            << "# TYPE bitcoin_mempool_size gauge\n"
                            << "bitcoin_mempool_size " << node.mempool->size() << "\n\n"
                            << "# HELP bitcoin_mempool_bytes Total size of mempool in bytes\n"
                            << "# TYPE bitcoin_mempool_bytes gauge\n"
                            << "bitcoin_mempool_bytes " << node.mempool->GetTotalTxSize() << "\n\n"
                            << "# HELP bitcoin_mempool_usage Mempool memory usage in bytes\n"
                            << "# TYPE bitcoin_mempool_usage gauge\n"
                            << "bitcoin_mempool_usage " << node.mempool->DynamicMemoryUsage() << "\n\n";
                }

                // 3. Peer metrics
                if (node.connman) {
                    metrics << "# HELP bitcoin_peers Connected peers\n"
                            << "# TYPE bitcoin_peers gauge\n"
                            << "bitcoin_peers " << node.connman->GetNodeCount(ConnectionDirection::Both) << "\n\n"
                            << "# HELP bitcoin_peers_inbound Connected inbound peers\n"
                            << "# TYPE bitcoin_peers_inbound gauge\n"
                            << "bitcoin_peers_inbound " << node.connman->GetNodeCount(ConnectionDirection::In) << "\n\n"
                            << "# HELP bitcoin_peers_outbound Connected outbound peers\n"
                            << "# TYPE bitcoin_peers_outbound gauge\n"
                            << "bitcoin_peers_outbound " << node.connman->GetNodeCount(ConnectionDirection::Out) << "\n\n";
                }

                // 4. Custom policy metrics
                metrics << "# HELP bitcoin_oracle_policy_profile Active policy profile\n"
                        << "# TYPE bitcoin_oracle_policy_profile gauge\n"
                        << "bitcoin_oracle_policy_profile{profile=\"" << OraclePolicy::g_active_profile << "\"} 1\n\n";

                metrics << "# HELP bitcoin_oracle_bip110_mode Active BIP110 enforcement mode\n"
                        << "# TYPE bitcoin_oracle_bip110_mode gauge\n"
                        << "bitcoin_oracle_bip110_mode{mode=\"" << OraclePolicy::g_bip110_mode << "\"} 1\n\n";

                metrics << "# HELP bitcoin_rejected_tx_total Rejection counts by reason\n"
                        << "# TYPE bitcoin_rejected_tx_total counter\n";
                for (const auto& entry : OraclePolicy::g_rejection_counts) {
                    metrics << "bitcoin_rejected_tx_total{reason=\"" << entry.first << "\"} " << entry.second << "\n";
                }
                metrics << "\n";

                const auto& tpl = OraclePolicy::g_last_template_stats;
                metrics << "# HELP bitcoin_oracle_template_txs_included Txs in last sovereign template\n"
                        << "# TYPE bitcoin_oracle_template_txs_included gauge\n"
                        << "bitcoin_oracle_template_txs_included " << tpl.txs_included << "\n\n"
                        << "# HELP bitcoin_oracle_template_policy_filtered Txs filtered from last template\n"
                        << "# TYPE bitcoin_oracle_template_policy_filtered gauge\n"
                        << "bitcoin_oracle_template_policy_filtered " << tpl.policy_filtered << "\n\n"
                        << "# HELP bitcoin_oracle_template_fees_sats Fees in last template (sats)\n"
                        << "# TYPE bitcoin_oracle_template_fees_sats gauge\n"
                        << "bitcoin_oracle_template_fees_sats " << tpl.fees << "\n\n";

                bool bip110_enforced = false;
                if (node.chainman) {
                    LOCK(::cs_main);
                    const CBlockIndex* tip = node.chainman->ActiveChain().Tip();
                    if (tip) {
                        if (OraclePolicy::g_bip110_mode == "always") {
                            bip110_enforced = true;
                        } else if (OraclePolicy::g_bip110_mode != "never") {
                            bip110_enforced = DeploymentActiveAt(*tip, *node.chainman, Consensus::DEPLOYMENT_REDUCED_DATA);
                        }
                    }
                }
                metrics << "# HELP bitcoin_oracle_bip110_enforced BIP-110 consensus enforced (1=yes)\n"
                        << "# TYPE bitcoin_oracle_bip110_enforced gauge\n"
                        << "bitcoin_oracle_bip110_enforced " << (bip110_enforced ? 1 : 0) << "\n\n";

                metrics << "# HELP bitcoin_uptime Uptime in seconds\n"
                        << "# TYPE bitcoin_uptime gauge\n"
                        << "bitcoin_uptime " << (GetTime() - OraclePolicy::g_startup_time) << "\n\n";

                std::string body = metrics.str();
                std::stringstream response;
                response << "HTTP/1.1 200 OK\r\n"
                         << "Content-Type: text/plain; version=0.0.4; charset=utf-8\r\n"
                         << "Content-Length: " << body.size() << "\r\n"
                         << "Connection: close\r\n\r\n"
                         << body;

                std::string response_str = response.str();
                send(client_fd, response_str.c_str(), response_str.size(), 0);
                close(client_fd);
            }
        }
    }

    close(server_fd);
    LogPrintf("Oracle Prometheus: Exporter thread stopped\n");
}

void StartPrometheusExporter(const node::NodeContext& node, int port) {
    if (g_prometheus_run) return;

    g_prometheus_run = true;
    g_prometheus_thread = std::thread(ExporterThread, std::ref(node), port);
}

void StopPrometheusExporter() {
    if (!g_prometheus_run) return;

    g_prometheus_run = false;
    if (g_prometheus_thread.joinable()) {
        g_prometheus_thread.join();
    }
}

} // namespace OraclePrometheus
