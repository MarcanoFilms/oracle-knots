#ifndef BITCOIN_POLICY_ORACLE_POLICY_H
#define BITCOIN_POLICY_ORACLE_POLICY_H

#include <kernel/mempool_options.h>
#include <primitives/transaction.h>
#include <uint256.h>

#include <cstdint>
#include <deque>
#include <map>
#include <string>

namespace OraclePolicy {

// The active policy profile: maximalist, bip110-strict, monetary-only, default-knots, custom
extern std::string g_active_profile;

// BIP-110 Enforcement Mode: auto, always, never
extern std::string g_bip110_mode;

// Configurable parameters
extern int g_max_datacarrier_bytes;
extern bool g_reject_tokens;
extern bool g_reject_inscriptions;
extern int g_dust_relay_fee;
extern bool g_permit_bare_multisig;
extern bool g_permit_bare_pubkey;
extern bool g_reject_parasites;
extern int g_max_op_return_outputs;

// Uptime tracking for observability
extern int64_t g_startup_time;

// Rejection counters
extern std::map<std::string, uint64_t> g_rejection_counts;

struct RecentPolicyRejection {
    std::string reason;
    std::string message;
    std::string wtxid;
    std::string context;
    int64_t timestamp;
};

struct SovereignTemplateStats {
    int64_t txs_included{0};
    int64_t mempool_size{0};
    int64_t policy_filtered{0};
    int64_t fees{0};
    int64_t weight{0};
    int64_t assembly_ms{0};
    std::string profile;
    int64_t timestamp{0};
};

extern std::deque<RecentPolicyRejection> g_recent_rejections;
extern SovereignTemplateStats g_last_template_stats;

// Helper to check if a transaction contains an inscription envelope
bool HasInscription(const CTransaction& tx);

// Check if a transaction has too many OP_RETURN outputs
bool ExceedsMaxOpReturns(const CTransaction& tx);

// Load the policy configuration from policy.toml (creates a default one if missing)
void LoadPolicyConfig(kernel::MemPoolOptions& mempool_opts);

// Apply current global policy state to mempool options (no disk I/O)
void ApplyActivePolicyToMempool(kernel::MemPoolOptions& mempool_opts);

// Apply runtime globals to mempool and persist to policy.toml (no disk read)
void ApplyPolicyFromRuntime(kernel::MemPoolOptions& mempool_opts);

// Save the active policy configuration to policy.toml
bool SavePolicyConfig();

// Apply a profile's settings to MemPoolOptions
void ApplyProfileSettings(const std::string& profile_name, kernel::MemPoolOptions& mempool_opts);

// Increment rejection counter (legacy; prefer RecordPolicyRejection)
void IncrementRejectionCount(const std::string& reason);

/** Human-readable operator message for a rejection reason code */
std::string RejectReasonToMessage(const std::string& reason);

/** Record rejection: counter + debug.log + ring buffer */
void RecordPolicyRejection(const std::string& reason, const uint256& wtxid, const std::string& context);

void UpdateTemplateStats(const SovereignTemplateStats& stats);

} // namespace OraclePolicy

#endif // BITCOIN_POLICY_ORACLE_POLICY_H
